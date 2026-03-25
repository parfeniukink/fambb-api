from time import perf_counter
from typing import Literal

from loguru import logger

from src.application.agents.news import (
    FilterContext,
    GroupingContext,
    ManualAddContext,
    grouping_agent,
    manual_add_agent,
    news_filter_agent,
)
from src.application.agents.perception import (
    AnalysisContext,
    microscope_agent,
    telescope_agent,
)
from src.application.scheduler import submit
from src.domain.news import PreferenceRules
from src.domain.news.value_objects import ArticleCandidate, CandidateGroup
from src.infrastructure import database, repositories
from src.infrastructure.cache import Cache
from src.infrastructure.tracing import get_tracer, pipeline_tracer

_CACHE_TTL = 604800  # 1 week in seconds

# NOTE: Maps the UI analysis mode to the database column
# that stores the result.
_MODE_TO_COLUMN: dict[str, str] = {
    "microscope": "detailed_description",
    "telescope": "extended_description",
}


def _normalize(title: str) -> str:
    return " ".join(title.casefold().split())[:20]


async def extend_article(
    item_id: int,
    mode: Literal["microscope", "telescope"],
    user_id: int,
) -> None:
    """Submit an inference task to extend a news item.

    NOTES
    (1) Works in 2 modes:
        - microscope: specialized context
        - telescope: broad context
    """

    news_repo = repositories.News()
    user_repo = repositories.User()

    try:
        item = await news_repo.get_news_item(id_=item_id)
        feedback_history = await news_repo.recent_feedback(limit=50)
    except Exception as e:
        logger.error(f"extend_article: failed to load item {item_id}: {e}")
        return

    # Load user preference profile
    user = await user_repo.user_by_id(user_id)
    preference_profile = user.configuration.news_preference_profile or ""

    user_message = f"## {item.title}\n\n{item.description}"
    column = _MODE_TO_COLUMN[mode]
    agent = microscope_agent if mode == "microscope" else telescope_agent

    context = AnalysisContext(
        title=item.title,
        description=item.description,
        feedback_history=feedback_history,
        preference_profile=preference_profile,
    )

    async def _handler() -> None:
        async with pipeline_tracer(
            f"extend:{mode}:{item_id}", user_id=user_id
        ) as tracer:
            t0 = perf_counter()
            result = await agent.run(user_message, deps=context)
            elapsed = perf_counter() - t0
            tracer.record(mode, elapsed)

            repo = repositories.News()
            await repo.set_description_field(
                id_=item_id, column=column, text=result.output
            )
            await repo.flush()

    submit(name=f"extend:{mode}:{item_id}", handler=_handler)


async def add_manual_article(url: str, user_id: int) -> None:
    """Submit a manually added article for AI analysis."""

    repo = repositories.News()
    if await repo.url_exists(url):
        raise ValueError("Article already exists")

    context = ManualAddContext(url=url)

    async def _handler() -> None:
        async with pipeline_tracer("manual_add", user_id=user_id) as tracer:
            t0 = perf_counter()
            await manual_add_agent.run(
                f"Analyze this article: {url}",
                deps=context,
            )
            tracer.record("manual_add", perf_counter() - t0)

    submit(
        name=f"manual_add:{url[:60]}",
        handler=_handler,
    )


# ── Pipeline: Level 1 — Cache dedup ──


async def _filter_cached(
    candidates: list[ArticleCandidate],
) -> list[ArticleCandidate]:
    """Check each candidate URL against memcached.
    Cache surviving URLs immediately. TTL = 1 week."""

    async with Cache() as cache:
        survivors: list[ArticleCandidate] = []
        urls_to_cache: list[str] = []

        for c in candidates:
            try:
                await cache.get("news_seen", c.url)
                # Cache hit — already seen, skip
                continue
            except Exception:
                # Cache miss — new URL
                survivors.append(c)
                urls_to_cache.append(c.url)

        # Cache surviving URLs immediately
        for url in urls_to_cache:
            try:
                await cache.set(
                    "news_seen",
                    url,
                    {"seen": True},
                    exptime=_CACHE_TTL,
                )
            except Exception as e:
                logger.warning(f"Failed to cache URL {url[:60]}: {e}")

    return survivors


# ── Pipeline: Level 2 — Filter (cheap LLM) ──


async def _filter_articles(
    candidates: list[ArticleCandidate],
    source_name: str,
    filter_prompt: str,
    preference_profile: str,
) -> list[ArticleCandidate]:
    """Use cheap LLM to filter irrelevant candidates."""

    news_repo = repositories.News()

    today_items = await news_repo.today_news_items()
    existing_titles = (
        "\n".join(f"- {item.title}" for item in today_items) or "None yet."
    )

    rules = PreferenceRules.from_stored(preference_profile)
    skip_rules = "\n".join(f"- {s}" for s in rules.skip) or "None yet."
    high_priority_rules = (
        "\n".join(f"- {b}" for b in rules.high_priority) or "None yet."
    )

    parts: list[str] = []
    for i, c in enumerate(candidates):
        parts.append(f'Article {i}: "{c.title}"\n' f"{c.short_description}")
    user_message = (
        f"Filter these candidates from "
        f'"{source_name}":\n\n' + "\n\n".join(parts)
    )

    context = FilterContext(
        filter_prompt=filter_prompt or "No specific filter.",
        high_priority_rules=high_priority_rules,
        skip_rules=skip_rules,
        existing_titles=existing_titles,
    )

    result = await news_filter_agent.run(user_message, deps=context)

    return [
        candidates[i]
        for i in result.output.keep_indices
        if 0 <= i < len(candidates)
    ]


# ── Pipeline: Level 3 — Grouping agent (capable LLM) ──


async def _group_articles(
    candidates: list[ArticleCandidate],
) -> list[CandidateGroup]:
    """Use capable LLM to process articles one-by-one
    and build groups."""

    context = GroupingContext(articles=candidates, groups=[])

    parts: list[str] = []
    for i, c in enumerate(candidates):
        parts.append(
            f'[{i}] "{c.title}"\n' f"URL: {c.url}\n" f"Content:\n{c.content}"
        )
    user_message = (
        f"Process these {len(candidates)} articles:\n\n"
        + "\n\n---\n\n".join(parts)
    )

    await grouping_agent.run(user_message, deps=context)

    return context.groups


# ── Pipeline: Save ──


async def _save_groups(
    groups: list[CandidateGroup],
    source_name: str,
) -> None:
    """Persist each group as a NewsItem."""

    repo = repositories.News()

    for group in groups:
        try:
            item = database.NewsItem(
                title=group.title,
                description=group.inference,
                sources=[source_name],
                article_urls=group.article_urls,
            )
            await repo.add_news_item(item)
            logger.debug(f"Saved: '{group.title[:60]}'")
        except Exception as e:
            logger.error(f"Failed to save '{group.title[:60]}': {e}")

    await repo.flush()


# ── Main pipeline ──


async def ingest_articles(  # noqa: C901
    candidates: list[ArticleCandidate], source_name: str, user_id: int
) -> str | None:
    """Multi-stage news ingestion pipeline.

    Level 1: cache dedup (code only, memcached)
    Level 2: cheap LLM filter
    Level 3: grouping agent (tool-driven)
    Save: persist groups as NewsItems

    Returns None on success, error string on failure.
    """

    tracer = get_tracer()

    if tracer:
        tracer.set_meta("candidates", len(candidates))

    # ── Level 1: Cache dedup ──
    t0 = perf_counter()
    survivors = await _filter_cached(candidates)

    if tracer:
        tracer.set_meta(
            "cache_dedup",
            -(len(candidates) - len(survivors)),
        )
        tracer.record("cache_dedup", perf_counter() - t0)

    if not survivors:
        logger.info(f"'{source_name}': all entries already cached")
        return None

    logger.info(
        f"'{source_name}': {len(survivors)} survived "
        f"cache dedup (from {len(candidates)})"
    )

    # Load user preferences
    user = await repositories.User().user_by_id(user_id)
    filter_prompt = user.configuration.news_filter_prompt or ""
    preference_profile = user.configuration.news_preference_profile or ""

    # ── Level 2: Cheap LLM filter ──
    try:
        t1 = perf_counter()
        survivors = await _filter_articles(
            survivors,
            source_name,
            filter_prompt,
            preference_profile,
        )
        if tracer:
            tracer.record("news_filter", perf_counter() - t1)
    except Exception as e:
        logger.warning(
            f"Filter agent error for '{source_name}': "
            f"{e} — passing all candidates through"
        )
        if tracer:
            tracer.record("news_filter", perf_counter() - t1, error=True)

    if tracer:
        tracer.set_meta("after_news_filter", len(survivors))

    if not survivors:
        logger.info(f"'{source_name}': no articles after filtering")
        return None

    logger.info(f"'{source_name}': {len(survivors)} survived " f"filtering")

    # ── Level 3: Grouping agent ──
    try:
        t2 = perf_counter()
        groups = await _group_articles(survivors)
        if tracer:
            tracer.record("news_grouper", perf_counter() - t2)
    except Exception as e:
        logger.error(
            f"Grouping agent error for '{source_name}': "
            f"{e} — falling back to individual articles"
        )
        if tracer:
            tracer.record(
                "grouping",
                perf_counter() - t2,
                error=True,
            )
        groups = [
            CandidateGroup(
                title=a.title,
                inference=a.short_description,
                article_urls=a.all_urls,
            )
            for a in survivors
        ]

    if tracer:
        tracer.set_meta("groups", len(groups))

    if not groups:
        logger.info(f"'{source_name}': no groups produced")
        return None

    # ── Save ──
    try:
        t3 = perf_counter()
        await _save_groups(groups, source_name)
        if tracer:
            tracer.record("save", perf_counter() - t3)
    except Exception as e:
        logger.error(f"Save error for '{source_name}': {e}")
        if tracer:
            tracer.record("save", perf_counter() - t3, error=True)
        return str(e)[:1000]

    logger.info(f"'{source_name}': saved {len(groups)} articles")
    return None
