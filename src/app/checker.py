import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import async_session
from app.models import Monitor
from app.alerts import send_down_alert

logger = logging.getLogger("cronguard.checker")


async def check_overdue_monitors(
    session_factory: async_sessionmaker | None = None,
) -> None:
    """Check for monitors that have missed their expected ping interval + grace period."""
    logger.info("Running overdue monitor check...")

    factory = session_factory or async_session
    async with factory() as db:
        try:
            now = datetime.now(timezone.utc)

            # Find monitors that are "up" but overdue
            result = await db.execute(
                select(Monitor).where(
                    Monitor.status.in_(["up"]),
                    Monitor.last_ping_at.isnot(None),
                )
            )
            monitors = result.scalars().all()

            down_count = 0
            for monitor in monitors:
                deadline = monitor.last_ping_at.replace(tzinfo=timezone.utc) + timedelta(
                    seconds=monitor.period + monitor.grace
                )
                if now > deadline:
                    logger.warning(f"Monitor '{monitor.name}' (id={monitor.id}) is overdue — marking DOWN")
                    monitor.status = "down"
                    await send_down_alert(monitor, db)
                    down_count += 1

            await db.commit()
            logger.info(f"Checker complete: {down_count} monitor(s) marked DOWN out of {len(monitors)} checked")

        except Exception as e:
            logger.error(f"Error in checker: {e}")
            await db.rollback()
