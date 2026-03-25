from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from polyfactory.factories import DataclassFactory

from src.application.news import _normalize
from src.domain.news.value_objects import ArticleCandidate, FilterResult


@pytest.mark.parametrize(
    "input_,expected",
    [
        ("Hello World", "hello world"),
        ("  foo   bar  ", "foo bar"),
        ("", ""),
        ("already normal", "already normal"),
    ],
)
def test_normalize(input_: str, expected: str):
    assert _normalize(input_) == expected


class ArticleCandidateFactory(DataclassFactory):
    __model__ = ArticleCandidate


# ── ingest_articles ──


async def test_ingest_all_cached_returns_none():
    """All candidates cached → returns None, no filter call."""

    candidate = ArticleCandidateFactory.build()

    with (
        patch(
            "src.application.news._filter_cached",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("src.application.news.news_filter_agent") as mock_filter,
    ):
        from src.application.news import ingest_articles

        result = await ingest_articles(
            candidates=[candidate],
            source_name="test",
            user_id=1,
        )

    assert result is None
    mock_filter.run.assert_not_called()


async def test_ingest_filter_keeps_articles():
    """Filter returns indices → only those proceed."""

    keep = ArticleCandidateFactory.build(title="Keep", url="http://a")
    drop = ArticleCandidateFactory.build(title="Drop", url="http://b")

    mock_repos = MagicMock()
    news_repo = AsyncMock()
    news_repo.today_news_items.return_value = []
    mock_repos.News.return_value = news_repo
    user = MagicMock()
    user.configuration.news_filter_prompt = ""
    user.configuration.news_preference_profile = ""
    user_repo = AsyncMock()
    user_repo.user_by_id.return_value = user
    mock_repos.User.return_value = user_repo

    filter_result = MagicMock()
    filter_result.output = FilterResult(keep_indices=[0])

    with (
        patch(
            "src.application.news._filter_cached",
            new_callable=AsyncMock,
            side_effect=lambda c: c,
        ),
        patch("src.application.news.repositories", mock_repos),
        patch("src.application.news.news_filter_agent") as mock_filter,
        patch("src.application.news.grouping_agent") as mock_grouper,
    ):
        mock_filter.run = AsyncMock(return_value=filter_result)
        mock_grouper.run = AsyncMock()

        from src.application.news import ingest_articles

        result = await ingest_articles(
            candidates=[keep, drop],
            source_name="test",
            user_id=1,
        )

    assert result is None
    mock_filter.run.assert_awaited_once()
    mock_grouper.run.assert_awaited_once()
    user_msg = mock_grouper.run.call_args.args[0]
    assert "Keep" in user_msg
    assert "Drop" not in user_msg


async def test_ingest_filter_error_passes_all_through():
    """Filter agent failure → all candidates pass through."""

    a = ArticleCandidateFactory.build(title="A", url="http://a")
    b = ArticleCandidateFactory.build(title="B", url="http://b")

    mock_repos = MagicMock()
    news_repo = AsyncMock()
    news_repo.today_news_items.return_value = []
    mock_repos.News.return_value = news_repo
    user = MagicMock()
    user.configuration.news_filter_prompt = ""
    user.configuration.news_preference_profile = ""
    user_repo = AsyncMock()
    user_repo.user_by_id.return_value = user
    mock_repos.User.return_value = user_repo

    with (
        patch(
            "src.application.news._filter_cached",
            new_callable=AsyncMock,
            side_effect=lambda c: c,
        ),
        patch("src.application.news.repositories", mock_repos),
        patch("src.application.news.news_filter_agent") as mock_filter,
        patch("src.application.news.grouping_agent") as mock_grouper,
    ):
        mock_filter.run = AsyncMock(side_effect=RuntimeError("LLM down"))
        mock_grouper.run = AsyncMock()

        from src.application.news import ingest_articles

        result = await ingest_articles(
            candidates=[a, b],
            source_name="test",
            user_id=1,
        )

    assert result is None
    user_msg = mock_grouper.run.call_args.args[0]
    assert "A" in user_msg
    assert "B" in user_msg


async def test_ingest_grouping_error_falls_back():
    """Grouping agent failure → each article becomes its
    own group and is saved."""

    candidate = ArticleCandidateFactory.build(
        title="Fallback Article",
        content="Some content here",
        url="http://a",
        extra_urls=[],
    )

    mock_repos = MagicMock()
    news_repo = AsyncMock()
    news_repo.today_news_items.return_value = []
    mock_repos.News.return_value = news_repo
    user = MagicMock()
    user.configuration.news_filter_prompt = ""
    user.configuration.news_preference_profile = ""
    user_repo = AsyncMock()
    user_repo.user_by_id.return_value = user
    mock_repos.User.return_value = user_repo

    filter_result = MagicMock()
    filter_result.output = FilterResult(keep_indices=[0])

    with (
        patch(
            "src.application.news._filter_cached",
            new_callable=AsyncMock,
            side_effect=lambda c: c,
        ),
        patch("src.application.news.repositories", mock_repos),
        patch("src.application.news.news_filter_agent") as mock_filter,
        patch("src.application.news.grouping_agent") as mock_grouper,
        patch(
            "src.application.news._save_groups",
            new_callable=AsyncMock,
        ) as mock_save,
    ):
        mock_filter.run = AsyncMock(return_value=filter_result)
        mock_grouper.run = AsyncMock(side_effect=RuntimeError("LLM down"))

        from src.application.news import ingest_articles

        result = await ingest_articles(
            candidates=[candidate],
            source_name="test",
            user_id=1,
        )

    assert result is None
    mock_save.assert_awaited_once()
    groups = mock_save.call_args.args[0]
    assert len(groups) == 1
    assert groups[0].title == "Fallback Article"
    assert groups[0].article_urls == ["http://a"]


async def test_ingest_no_survivors_after_filter():
    """Filter drops everything → returns None, no grouping."""

    candidate = ArticleCandidateFactory.build()

    mock_repos = MagicMock()
    news_repo = AsyncMock()
    news_repo.today_news_items.return_value = []
    mock_repos.News.return_value = news_repo
    user = MagicMock()
    user.configuration.news_filter_prompt = ""
    user.configuration.news_preference_profile = ""
    user_repo = AsyncMock()
    user_repo.user_by_id.return_value = user
    mock_repos.User.return_value = user_repo

    filter_result = MagicMock()
    filter_result.output = FilterResult(keep_indices=[])

    with (
        patch(
            "src.application.news._filter_cached",
            new_callable=AsyncMock,
            side_effect=lambda c: c,
        ),
        patch("src.application.news.repositories", mock_repos),
        patch("src.application.news.news_filter_agent") as mock_filter,
        patch("src.application.news.grouping_agent") as mock_grouper,
    ):
        mock_filter.run = AsyncMock(return_value=filter_result)

        from src.application.news import ingest_articles

        result = await ingest_articles(
            candidates=[candidate],
            source_name="test",
            user_id=1,
        )

    assert result is None
    mock_grouper.run.assert_not_called()
