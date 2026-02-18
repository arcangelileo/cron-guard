from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Monitor, Ping

router = APIRouter(tags=["ping"])


@router.api_route("/ping/{slug}", methods=["GET", "POST"], response_class=PlainTextResponse)
async def receive_ping(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive a ping for a monitor. No authentication required. Must be fast."""
    result = await db.execute(select(Monitor).where(Monitor.slug == slug))
    monitor = result.scalar_one_or_none()

    if not monitor:
        return PlainTextResponse("Not Found", status_code=404)

    if monitor.status == "paused":
        return PlainTextResponse("OK (paused)", status_code=200)

    now = datetime.now(timezone.utc)
    was_down = monitor.status == "down"

    # Update monitor status
    monitor.last_ping_at = now
    monitor.status = "up"

    # Record ping
    ping = Ping(
        monitor_id=monitor.id,
        remote_addr=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(ping)

    # If recovering from down, we'll handle alert in the checker or here
    if was_down:
        from app.alerts import send_recovery_alert
        await send_recovery_alert(monitor, db)

    return PlainTextResponse("OK", status_code=200)
