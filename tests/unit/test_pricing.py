from src.infrastructure.agents import AGENT_MODELS
from src.infrastructure.analytics.pricing import estimate_pipeline_cost


def test_estimate_cost_filter() -> None:
    """news_filter uses gpt-4.1-mini.

    1 * (2000 * 0.40 + 500 * 1.60) / 1_000_000
    = (800 + 800) / 1_000_000 = 0.0016
    """

    stats = [{"agent": "news_filter", "calls": 1, "errors": 0}]

    cost = estimate_pipeline_cost(stats, AGENT_MODELS)

    assert round(cost, 5) == 0.0016


def test_estimate_cost_grouping() -> None:
    """news_grouper uses gpt-4.1-mini.

    1 * (3000 * 0.40 + 1500 * 1.60) / 1_000_000
    = (1200 + 2400) / 1_000_000 = 0.0036
    """

    stats = [{"agent": "news_grouper", "calls": 1, "errors": 0}]

    cost = estimate_pipeline_cost(stats, AGENT_MODELS)

    assert round(cost, 5) == 0.0036


def test_estimate_cost_multiple_agents() -> None:
    """Multiple known agents accumulate cost above zero."""

    stats = [
        {"agent": "news_filter", "calls": 1, "errors": 0},
        {"agent": "microscope", "calls": 2, "errors": 0},
        {"agent": "telescope", "calls": 1, "errors": 0},
    ]

    cost = estimate_pipeline_cost(stats, AGENT_MODELS)

    assert cost > 0


def test_estimate_cost_unknown_agent() -> None:
    """Unknown agent name contributes zero cost."""

    stats = [{"agent": "unknown_future_agent", "calls": 1, "errors": 0}]

    cost = estimate_pipeline_cost(stats, AGENT_MODELS)

    assert cost == 0.0


def test_estimate_cost_empty() -> None:
    """Empty stats list returns zero."""

    cost = estimate_pipeline_cost([], AGENT_MODELS)

    assert cost == 0.0
