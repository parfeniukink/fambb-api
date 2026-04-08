from datetime import date, timedelta
from time import perf_counter

from loguru import logger

from src.application.agents.preference import (
    PreferenceContext,
    preference_agent,
)
from src.domain.jobs.registry import register_job_type
from src.domain.news import PreferenceRules
from src.domain.news.signals import SIGNAL_WEIGHTS
from src.infrastructure import repositories
from src.infrastructure.tracing import pipeline_tracer

DELETED_RETENTION_DAYS = 30


def _merge_rules(
    existing: PreferenceRules,
    new: PreferenceRules,
) -> PreferenceRules:
    """Merge agent output with existing rules.

    Extends skip/high_priority lists (deduped, order preserved).
    Does NOT touch recently_deleted — managed by
    _build_recently_deleted.
    """

    skip = list(dict.fromkeys(existing.skip + new.skip))
    high_priority = list(
        dict.fromkeys(existing.high_priority + new.high_priority)
    )

    return PreferenceRules(
        skip=skip,
        high_priority=high_priority,
    )


def _build_recently_deleted(
    existing: list[dict],
    new_signals: list[dict],
) -> list[dict]:
    """Deterministic recently_deleted management.

    Age out entries older than DELETED_RETENTION_DAYS,
    then append new deletions (deduped by title).
    """

    cutoff = date.today() - timedelta(days=DELETED_RETENTION_DAYS)

    retained: list[dict] = []
    for entry in existing:
        deleted_at = entry.get("deleted_at")
        if not deleted_at:
            retained.append(entry)
            continue
        if date.fromisoformat(deleted_at) >= cutoff:
            retained.append(entry)

    seen: set[str] = {e.get("title", "") for e in retained}
    for entry in new_signals:
        if entry["title"] not in seen:
            seen.add(entry["title"])
            retained.append(entry)

    return retained


@register_job_type("kernel", name="Preference Learner", interval_minutes=4320)
async def learn_preferences() -> None:  # noqa: C901
    """Analyzes user reactions to build preference rules.
    Considers reactions, bookmarks, feedback, and article
    removals to build a structured filter for validating
    incoming information.

    NOTES
    (1) Runs every 3 days
    """

    users = await repositories.User().all_users()

    for user in users:
        try:
            await _learn_for_user(user)
        except Exception as e:
            logger.warning(
                f"Preference learning failed for " f"user {user.id}: {e}"
            )


LOOKBACK_DAYS = 14


async def _learn_for_user(user) -> None:  # noqa: C901
    """Run preference learning for a single user."""

    if not user.configuration.analyze_preferences:
        logger.info(f"Preference: user {user.id} has " f"analysis disabled")
        return

    news_repo = repositories.News()
    since = date.today() - timedelta(days=LOOKBACK_DAYS)
    items = await news_repo.recent_reactions(user_id=user.id, since=since)

    # Load deleted signals from DB (not cache)
    deleted_signals_rows = await news_repo.get_deleted_signals(user_id=user.id)

    if not items and not deleted_signals_rows:
        logger.info(f"Preference: user {user.id} has no signals")
        return

    # Build weighted reaction context from live items
    reactions: list[dict] = []
    for item in items:
        weight = 0
        if item.reaction:
            weight += SIGNAL_WEIGHTS.get(item.reaction, 0)
        if item.bookmarked:
            weight += SIGNAL_WEIGHTS["bookmark"]
        if item.human_feedback:
            weight += SIGNAL_WEIGHTS["human_feedback"]

        reactions.append(
            {
                "title": item.title,
                "reaction": item.reaction,
                "bookmarked": item.bookmarked,
                "feedback": item.human_feedback,
                "weight": weight,
            }
        )

    # Build signals from deleted items
    deleted_signals: list[dict] = []
    for sig in deleted_signals_rows:
        is_feedback = sig.source_type == "user" and sig.human_feedback
        signal_type = (
            "deleted_with_feedback"
            if is_feedback
            else (
                "gc_deleted" if sig.source_type == "kernel" else "deleted_bare"
            )
        )
        deleted_signals.append(
            {
                "title": sig.title,
                "reaction": None,
                "bookmarked": False,
                "feedback": sig.human_feedback,
                "deleted": True,
                "deleted_at": (sig.created_at.date().isoformat()),
                "signal_type": signal_type,
                "weight": SIGNAL_WEIGHTS[signal_type],
            }
        )

    reactions.extend(deleted_signals)

    # Sort by absolute weight (most opinionated first)
    reactions.sort(key=lambda r: abs(r["weight"]), reverse=True)

    n_reacted = len(items)
    n_deleted = len(deleted_signals_rows)
    logger.info(
        f"Preference: user {user.id}: analyzing "
        f"{len(reactions)} signals "
        f"({n_reacted} reacted, {n_deleted} deleted)"
    )

    # Load existing rules for reconciliation
    existing_rules = PreferenceRules()
    filter_prompt = ""
    try:
        profile = user.configuration.news_preference_profile
        existing_rules = PreferenceRules.from_stored(profile)
        filter_prompt = user.configuration.news_filter_prompt or ""
    except Exception as e:
        logger.warning(f"Could not load existing rules: {e}")

    # Build recently_deleted deterministically (code-managed)
    new_deleted = [
        {
            "title": r["title"],
            "feedback": r.get("feedback"),
            "deleted_at": r.get("deleted_at"),
        }
        for r in deleted_signals
    ]
    recently_deleted = _build_recently_deleted(
        existing_rules.recently_deleted,
        new_deleted,
    )

    # Run preference agent
    ctx = PreferenceContext(
        reactions=reactions,
        filter_prompt=filter_prompt,
        existing_skip=existing_rules.skip,
        existing_high_priority=existing_rules.high_priority,
        existing_recently_deleted=recently_deleted,
    )

    async with pipeline_tracer(
        f"preference:user-{user.id}",
        user_id=user.id,
    ) as tracer:
        t0 = perf_counter()
        result = await preference_agent.run(
            "Analyze these reactions and produce "
            "updated skip/high_priority rules.",
            deps=ctx,
        )
        elapsed = perf_counter() - t0
        tracer.record("preference", elapsed)

        # Merge agent output with existing rules
        # (extend, not replace — agent may drop rules)
        merged = _merge_rules(existing_rules, result.output)
        merged = PreferenceRules(
            skip=merged.skip,
            high_priority=merged.high_priority,
            recently_deleted=recently_deleted,
        )

        user_repo = repositories.User()
        await user_repo.update_user(
            user.id,
            news_preference_profile=merged.to_json(),
        )
        await user_repo.flush()

        # Clear analysis flag on processed items
        if items:
            analyzed_ids = [item.id for item in items]
            await news_repo.clear_ai_analysis_flag(analyzed_ids)
            await news_repo.flush()

        # Delete processed signals ONLY after success
        if deleted_signals_rows:
            signal_ids = [s.id for s in deleted_signals_rows]
            del_repo = repositories.News()
            await del_repo.delete_signals(signal_ids)
            await del_repo.flush()
