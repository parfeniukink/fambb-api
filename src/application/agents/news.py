"""News pipeline agents.

Level 2 — news_filter_agent: cheap LLM that filters candidates
          via structured output (keep_indices).
Level 3 — grouping_agent: capable LLM that groups filtered
          articles one-by-one via tool calls.

Manual-add agent remains unchanged (tool-based).
"""

from dataclasses import dataclass
from time import perf_counter

import httpx
from loguru import logger
from pydantic_ai import Agent, RunContext, Tool

from src import domain
from src.domain.news.value_objects import (
    ArticleCandidate,
    CandidateGroup,
    FilterResult,
)
from src.infrastructure import database, repositories
from src.infrastructure.agents import AGENT_MODELS, get_model
from src.infrastructure.tracing import get_tracer

# ── Level 2: Filter agent ──


@dataclass
class FilterContext:
    filter_prompt: str
    high_priority_rules: str
    skip_rules: str
    existing_titles: str


news_filter_agent = Agent(
    get_model(AGENT_MODELS["news_filter"]),
    deps_type=FilterContext,
    output_type=FilterResult,
)


@news_filter_agent.system_prompt
async def _filter_system_prompt(
    ctx: RunContext[FilterContext],
) -> str:
    return domain.prompts.SYSTEM_NEWS_FILTER.format(
        filter_prompt=ctx.deps.filter_prompt,
        high_priority_rules=ctx.deps.high_priority_rules,
        skip_rules=ctx.deps.skip_rules,
        existing_titles=ctx.deps.existing_titles,
    )


# ── Level 3: Grouping agent ──


@dataclass
class GroupingContext:
    articles: list[ArticleCandidate]
    groups: list[CandidateGroup]


grouping_agent = Agent(
    get_model(AGENT_MODELS["news_grouper"]),
    deps_type=GroupingContext,
    output_type=str,
)


@grouping_agent.system_prompt
async def _grouping_system_prompt(
    ctx: RunContext[GroupingContext],
) -> str:
    return domain.prompts.SYSTEM_NEWS_GROUPER.format(
        article_count=len(ctx.deps.articles),
    )


@grouping_agent.tool
async def classify_article(
    ctx: RunContext[GroupingContext],
    article_index: int,
    group_index: int | None,
    title: str,
    inference: str,
) -> str:
    """Classify an article into a new or existing group.

    Args:
        article_index: Index of the article being processed.
        group_index: Index of existing group to merge into,
                     or None to create a new group.
        title: Group title.
        inference: Analytical summary incorporating this
                   article's content.
    """

    articles = ctx.deps.articles
    groups = ctx.deps.groups

    if article_index < 0 or article_index >= len(articles):
        return f"Invalid article_index: {article_index}"

    article = articles[article_index]
    urls = article.all_urls

    if group_index is None:
        groups.append(
            CandidateGroup(
                title=title,
                inference=inference,
                article_urls=urls,
            )
        )
    else:
        if group_index < 0 or group_index >= len(groups):
            return f"Invalid group_index: {group_index}"
        group = groups[group_index]
        group.title = title
        group.inference = inference
        existing = group.article_urls
        group.article_urls = existing + [u for u in urls if u not in existing]

    summary_parts = []
    for i, g in enumerate(groups):
        summary_parts.append(
            f"[{i}] {g.title} " f"({len(g.article_urls)} urls)"
        )
    return "Current groups:\n" + "\n".join(summary_parts)


# ── Web fetch utility ──


async def web_search(url: str) -> str:
    """Fetch a web page for additional context about an article."""

    logger.info(f"AI Web Search: {url}")

    try:
        async with httpx.AsyncClient(
            timeout=15, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise Exception(f"Invalid Status Code: {resp.status_code}")
    except Exception as error:
        logger.error(error)
        return "Web search unavailable."
    else:
        return f"Content from {url}:\n{resp.text[:3000]}"


# ── Manual add agent (unchanged) ──


@dataclass
class ManualAddContext:
    url: str
    user_id: int


manual_add_agent = Agent(
    get_model(AGENT_MODELS["manual_add"]),
    deps_type=ManualAddContext,
    output_type=str,
    tools=[Tool(web_search, takes_ctx=False)],
)


@manual_add_agent.system_prompt
async def _manual_add_prompt(
    ctx: RunContext[ManualAddContext],
) -> str:
    return domain.prompts.SYSTEM_MANUAL_ADD


@manual_add_agent.tool
async def save_manual_article(
    ctx: RunContext[ManualAddContext],
    title: str,
    description: str,
    urls: str,
) -> str:
    """Save the analyzed article to the database.

    Args:
        title: Article title.
        description: Rich analysis of the article content.
        urls: Comma-separated URL(s) — original + references.
    """

    tracer = get_tracer()
    t0 = perf_counter()

    url_list = [u.strip() for u in urls.split(",") if u.strip()]

    repo = repositories.News()
    item = database.NewsItem(
        title=title,
        description=description,
        sources=["manual"],
        article_urls=url_list,
        user_id=ctx.deps.user_id,
    )
    await repo.add_news_item(item)
    await repo.flush()

    if tracer:
        tracer.record("save", perf_counter() - t0)

    logger.debug(f"Manual save: '{title[:60]}' (id={item.id})")
    return f"Saved (id={item.id})"
