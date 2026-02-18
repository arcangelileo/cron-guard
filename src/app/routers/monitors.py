from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.main import templates
from app.models import Monitor, Ping, User
from app.config import settings

router = APIRouter(tags=["monitors"])

PERIOD_PRESETS = [
    (60, "Every 1 minute"),
    (300, "Every 5 minutes"),
    (900, "Every 15 minutes"),
    (3600, "Every hour"),
    (86400, "Every day"),
    (604800, "Every week"),
]


def compute_grace(period: int, custom_grace: int | None = None) -> int:
    """Compute grace period: custom or 50% of period, minimum 60 seconds."""
    if custom_grace and custom_grace > 0:
        return max(custom_grace, 60)
    return max(int(period * 0.5), 60)


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m = seconds // 60
        return f"{m}m"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h}h"
    d = seconds // 86400
    return f"{d}d"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor)
        .where(Monitor.user_id == user.id)
        .order_by(Monitor.created_at.desc())
    )
    monitors = result.scalars().all()

    # Count stats
    total = len(monitors)
    up_count = sum(1 for m in monitors if m.status == "up")
    down_count = sum(1 for m in monitors if m.status == "down")
    new_count = sum(1 for m in monitors if m.status == "new")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "monitors": monitors,
            "total": total,
            "up_count": up_count,
            "down_count": down_count,
            "new_count": new_count,
            "format_duration": format_duration,
            "base_url": settings.base_url,
        },
    )


@router.get("/monitors/new", response_class=HTMLResponse)
async def new_monitor_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "monitors/form.html",
        {
            "request": request,
            "user": user,
            "presets": PERIOD_PRESETS,
            "monitor": None,
            "editing": False,
        },
    )


@router.post("/monitors/new")
async def create_monitor(
    request: Request,
    name: str = Form(...),
    period: int = Form(...),
    grace: int = Form(0),
    webhook_url: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    errors = []
    name = name.strip()
    webhook_url = webhook_url.strip() or None

    if len(name) < 1:
        errors.append("Monitor name is required.")
    if len(name) > 200:
        errors.append("Monitor name must be at most 200 characters.")
    if period < 60:
        errors.append("Period must be at least 60 seconds.")
    if webhook_url and not (webhook_url.startswith("http://") or webhook_url.startswith("https://")):
        errors.append("Webhook URL must start with http:// or https://.")

    if errors:
        return templates.TemplateResponse(
            "monitors/form.html",
            {
                "request": request,
                "user": user,
                "presets": PERIOD_PRESETS,
                "monitor": None,
                "editing": False,
                "errors": errors,
                "form_name": name,
                "form_period": period,
                "form_grace": grace,
                "form_webhook_url": webhook_url or "",
            },
            status_code=422,
        )

    computed_grace = compute_grace(period, grace)
    monitor = Monitor(
        user_id=user.id,
        name=name,
        period=period,
        grace=computed_grace,
        webhook_url=webhook_url,
    )
    db.add(monitor)
    await db.flush()

    return RedirectResponse("/dashboard", status_code=303)


@router.get("/monitors/{monitor_id}", response_class=HTMLResponse)
async def monitor_detail(
    monitor_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        return RedirectResponse("/dashboard", status_code=303)

    # Get recent pings
    ping_result = await db.execute(
        select(Ping)
        .where(Ping.monitor_id == monitor.id)
        .order_by(Ping.created_at.desc())
        .limit(50)
    )
    pings = ping_result.scalars().all()

    # Get ping count
    count_result = await db.execute(
        select(func.count()).where(Ping.monitor_id == monitor.id)
    )
    ping_count = count_result.scalar()

    return templates.TemplateResponse(
        "monitors/detail.html",
        {
            "request": request,
            "user": user,
            "monitor": monitor,
            "pings": pings,
            "ping_count": ping_count,
            "format_duration": format_duration,
            "base_url": settings.base_url,
        },
    )


@router.get("/monitors/{monitor_id}/edit", response_class=HTMLResponse)
async def edit_monitor_page(
    monitor_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        return RedirectResponse("/dashboard", status_code=303)

    return templates.TemplateResponse(
        "monitors/form.html",
        {
            "request": request,
            "user": user,
            "presets": PERIOD_PRESETS,
            "monitor": monitor,
            "editing": True,
        },
    )


@router.post("/monitors/{monitor_id}/edit")
async def update_monitor(
    monitor_id: int,
    request: Request,
    name: str = Form(...),
    period: int = Form(...),
    grace: int = Form(0),
    webhook_url: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    monitor = result.scalar_one_or_none()
    if not monitor:
        return RedirectResponse("/dashboard", status_code=303)

    errors = []
    name = name.strip()
    webhook_url = webhook_url.strip() or None

    if len(name) < 1:
        errors.append("Monitor name is required.")
    if len(name) > 200:
        errors.append("Monitor name must be at most 200 characters.")
    if period < 60:
        errors.append("Period must be at least 60 seconds.")
    if webhook_url and not (webhook_url.startswith("http://") or webhook_url.startswith("https://")):
        errors.append("Webhook URL must start with http:// or https://.")

    if errors:
        return templates.TemplateResponse(
            "monitors/form.html",
            {
                "request": request,
                "user": user,
                "presets": PERIOD_PRESETS,
                "monitor": monitor,
                "editing": True,
                "errors": errors,
            },
            status_code=422,
        )

    monitor.name = name
    monitor.period = period
    monitor.grace = compute_grace(period, grace)
    monitor.webhook_url = webhook_url

    return RedirectResponse(f"/monitors/{monitor.id}", status_code=303)


@router.post("/monitors/{monitor_id}/delete")
async def delete_monitor(
    monitor_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    monitor = result.scalar_one_or_none()
    if monitor:
        await db.delete(monitor)

    return RedirectResponse("/dashboard", status_code=303)


@router.post("/monitors/{monitor_id}/pause")
async def pause_monitor(
    monitor_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    monitor = result.scalar_one_or_none()
    if monitor and monitor.status != "paused":
        monitor.status = "paused"

    return RedirectResponse(f"/monitors/{monitor_id}", status_code=303)


@router.post("/monitors/{monitor_id}/resume")
async def resume_monitor(
    monitor_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    monitor = result.scalar_one_or_none()
    if monitor and monitor.status == "paused":
        # Resume to appropriate status
        if monitor.last_ping_at:
            monitor.status = "up"
        else:
            monitor.status = "new"

    return RedirectResponse(f"/monitors/{monitor_id}", status_code=303)
