import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import Alert, Monitor, User

logger = logging.getLogger("cronguard.alerts")


async def send_email_alert(user: User, monitor: Monitor, alert_type: str) -> None:
    """Send email alert. In dev mode, just logs to console."""
    subject = (
        f"[CronGuard] {monitor.name} is DOWN"
        if alert_type == "down"
        else f"[CronGuard] {monitor.name} has RECOVERED"
    )
    recipient = user.alert_email or user.email

    if alert_type == "down":
        body = (
            f"Monitor '{monitor.name}' has gone DOWN.\n"
            f"Last ping: {monitor.last_ping_at or 'never'}\n"
            f"Expected interval: {monitor.period}s (grace: {monitor.grace}s)\n"
            f"\nView monitor: {settings.base_url}/monitors/{monitor.id}\n"
        )
    else:
        body = (
            f"Monitor '{monitor.name}' has RECOVERED and is now UP.\n"
            f"Ping received at: {monitor.last_ping_at}\n"
            f"\nView monitor: {settings.base_url}/monitors/{monitor.id}\n"
        )

    if settings.smtp_host == "localhost" and settings.smtp_port == 1025:
        # Dev mode — log to console
        logger.info(f"EMAIL ALERT [{alert_type.upper()}] to={recipient} subject={subject}")
        logger.info(f"Body: {body}")
        return

    try:
        import aiosmtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email
        msg["To"] = recipient

        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_tls,
        )
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")


async def send_webhook_alert(monitor: Monitor, alert_type: str) -> None:
    """Send webhook alert to user-configured URL."""
    if not monitor.webhook_url:
        return

    payload = {
        "monitor_name": monitor.name,
        "monitor_slug": monitor.slug,
        "status": alert_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": f"Monitor '{monitor.name}' is now {alert_type.upper()}.",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(monitor.webhook_url, json=payload)
    except Exception as e:
        logger.error(f"Failed to send webhook alert to {monitor.webhook_url}: {e}")


async def send_down_alert(monitor: Monitor, db: AsyncSession) -> None:
    """Send down alerts via all configured channels."""
    # Get user
    result = await db.execute(select(User).where(User.id == monitor.user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    # Email alert
    if user.email_alerts_enabled:
        await send_email_alert(user, monitor, "down")
        alert = Alert(
            monitor_id=monitor.id,
            alert_type="down",
            channel="email",
            details=f"Down alert sent to {user.alert_email or user.email}",
        )
        db.add(alert)

    # Webhook alert
    if monitor.webhook_url:
        await send_webhook_alert(monitor, "down")
        alert = Alert(
            monitor_id=monitor.id,
            alert_type="down",
            channel="webhook",
            details=f"Down alert sent to {monitor.webhook_url}",
        )
        db.add(alert)


async def send_recovery_alert(monitor: Monitor, db: AsyncSession) -> None:
    """Send recovery alerts via all configured channels."""
    result = await db.execute(select(User).where(User.id == monitor.user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    if user.email_alerts_enabled:
        await send_email_alert(user, monitor, "up")
        alert = Alert(
            monitor_id=monitor.id,
            alert_type="up",
            channel="email",
            details=f"Recovery alert sent to {user.alert_email or user.email}",
        )
        db.add(alert)

    if monitor.webhook_url:
        await send_webhook_alert(monitor, "up")
        alert = Alert(
            monitor_id=monitor.id,
            alert_type="up",
            channel="webhook",
            details=f"Recovery alert sent to {monitor.webhook_url}",
        )
        db.add(alert)
