from datetime import date, timedelta

from loguru import logger

from src.domain.jobs.registry import register_job_type
from src.infrastructure import database, repositories


@register_job_type("kernel", name="Garbage Collector", interval_minutes=240)
async def garbage_collect() -> None:
    """Cleans up old news articles automatically. Removes articles
    with no reactions or bookmarks older than the retention period.
    Bookmarked and reacted articles are kept.

    NOTES
    (1) Runs every 4 hours
    (2) Stores deleted items in deleted_signals table for
        preference learning
    """

    users = await repositories.User().all_users()

    if not users:
        logger.info("GC: no users found — skipping")
        return

    for user in users:
        retention = user.configuration.gc_retention_days
        cutoff = date.today() - timedelta(days=retention)

        repo = repositories.News()

        # Fetch stale items before deletion for signal storage
        stale = await repo.stale_items(
            user_id=user.id, before_date=cutoff, limit=50
        )

        if stale:
            signals = [
                database.DeletedSignal(
                    user_id=user.id,
                    title=item.title,
                    description=item.description,
                    human_feedback=item.human_feedback,
                    sources=item.sources,
                    source_type="kernel",
                )
                for item in stale
            ]
            await repo.add_deleted_signals(signals)

        count = await repo.delete_stale_items(
            user_id=user.id, before_date=cutoff
        )
        await repo.flush()

        if count:
            logger.success(
                f"GC: user {user.id}: removed {count} items "
                f"older than {cutoff} "
                f"(retention={retention}d)"
            )
