from abc import ABC, abstractmethod

import httpx
from loguru import logger

from src.application.news import ingest_articles
from src.domain.jobs.value_objects import JobContext
from src.domain.news.value_objects import ArticleCandidate
from src.infrastructure.tracing import pipeline_tracer


class WebCrawlerBase(ABC):
    source_name: str
    feed_url: str

    @staticmethod
    @abstractmethod
    def parse_feed(html: str) -> list[ArticleCandidate]:
        """Extract candidates from the feed HTML."""

    @staticmethod
    @abstractmethod
    def parse_article(html: str) -> str:
        """Extract full article text from an article page."""

    @staticmethod
    def make_candidate(
        title: str,
        url: str,
        content: str = "",
    ) -> ArticleCandidate:
        return ArticleCandidate(
            title=title[:500],
            content=content[:5000],
            url=url[:2048],
        )

    @staticmethod
    async def _fetch(url: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    @classmethod
    async def _fetch_all_content(
        cls, candidates: list[ArticleCandidate]
    ) -> None:
        """Fetch and parse full content for all candidates."""

        async with httpx.AsyncClient(timeout=30) as client:
            for candidate in candidates:
                try:
                    resp = await client.get(candidate.url)
                    resp.raise_for_status()
                    body = cls.parse_article(resp.text)
                    if body:
                        candidate.content = body[:5000]
                except Exception as e:
                    logger.warning(
                        f"'{cls.source_name}': failed to "
                        f"fetch {candidate.url}: {e}"
                    )

    @classmethod
    async def execute(cls, context: JobContext) -> None:
        """Fetch feed -> parse -> fetch content -> ingest."""

        async with pipeline_tracer(
            f"web:{cls.source_name}",
            user_id=context.user_id,
        ):
            html = await cls._fetch(cls.feed_url)
            candidates = cls.parse_feed(html)
            if not candidates:
                logger.info(
                    f"'{cls.source_name}': no articles " f"from {cls.feed_url}"
                )
                return
            await cls._fetch_all_content(candidates)
            error = await ingest_articles(
                candidates,
                cls.source_name,
                context.user_id,
            )
            if error:
                raise RuntimeError(error)
