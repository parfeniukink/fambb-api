from dataclasses import dataclass, field

from src.domain.entities import InternalData


@dataclass
class ArticleCandidate:
    title: str
    url: str
    content: str = ""
    extra_urls: list[str] = field(default_factory=list)

    @property
    def short_description(self) -> str:
        if len(self.content) <= 500:
            return self.content
        return self.content[:500] + "..."

    @property
    def all_urls(self) -> list[str]:
        return [self.url] + self.extra_urls


class CandidateGroup(InternalData):
    """Save-ready group: title, analytical inference, URLs."""

    title: str
    inference: str
    article_urls: list[str]


class FilterResult(InternalData):
    """Level 2 output: indices of articles to keep."""

    keep_indices: list[int]
