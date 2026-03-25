from bs4 import BeautifulSoup
from pydantic import BaseModel

from src.application.scheduler.jobs.crawlers._base import WebCrawlerBase
from src.domain.jobs.registry import register_job_type
from src.domain.jobs.value_objects import JobContext
from src.domain.news.value_objects import ArticleCandidate


class SantaFeParams(BaseModel):
    pass


class SantaFeCrawler(WebCrawlerBase):
    source_name = "santafe.edu"
    feed_url = "https://www.santafe.edu/news-center/news"

    @staticmethod
    def parse_article(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for selector in [
            ".news-content",
            ".news-detail",
            "article",
            "main",
        ]:
            container = soup.select_one(selector)
            if container:
                for unwanted in container.select(
                    "nav, footer, .sidebar, .more-news, "
                    ".news-media-contact, .share-links, "
                    "script, style, .tags"
                ):
                    unwanted.decompose()

                text = container.get_text(separator=" ", strip=True)
                if text:
                    return text

        return ""

    @staticmethod
    def parse_feed(html: str) -> list[ArticleCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        articles: list[ArticleCandidate] = []

        for heading in soup.find_all("h3"):
            link_tag = heading.find("a", href=True)
            if not link_tag:
                continue

            href: str = link_tag["href"]  # type: ignore[assignment]
            if "/news-center/news/" not in href:
                continue

            title = link_tag.get_text(strip=True)
            if not title:
                continue

            url = (
                href
                if href.startswith("http")
                else f"https://www.santafe.edu{href}"
            )

            description = ""
            sibling = heading.find_next_sibling()
            if sibling and sibling.name == "p":
                description = sibling.get_text(strip=True)

            articles.append(
                WebCrawlerBase.make_candidate(
                    title=title,
                    url=url,
                    content=description,
                )
            )

        return articles


@register_job_type(
    label="santafe_crawler",
    name="Santa Fe Institute News",
)
async def fetch_santa_fe(params: SantaFeParams, context: JobContext) -> None:
    """Crawls santafe.edu for complexity science and
    research news."""

    await SantaFeCrawler.execute(context)
