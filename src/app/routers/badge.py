from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Monitor

router = APIRouter(tags=["badge"])

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20">
  <linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="{width}" height="20" fill="#555"/>
  <rect rx="3" x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
  <rect rx="3" width="{width}" height="20" fill="url(#a)"/>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_center}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_center}" y="14">{label}</text>
    <text x="{value_center}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{value_center}" y="14">{value}</text>
  </g>
</svg>"""

STATUS_COLORS = {
    "up": "#4c1",
    "down": "#e05d44",
    "new": "#9f9f9f",
    "paused": "#dfb317",
}


@router.get("/badge/{slug}.svg")
async def badge_svg(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Monitor).where(Monitor.slug == slug))
    monitor = result.scalar_one_or_none()

    if not monitor:
        return Response(status_code=404)

    label = "status"
    value = monitor.status
    color = STATUS_COLORS.get(monitor.status, "#9f9f9f")

    label_width = len(label) * 7 + 10
    value_width = len(value) * 7 + 10
    width = label_width + value_width

    svg = SVG_TEMPLATE.format(
        width=width,
        label_width=label_width,
        value_width=value_width,
        color=color,
        label=label,
        value=value,
        label_center=label_width / 2,
        value_center=label_width + value_width / 2,
    )

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/badge/{slug}.json")
async def badge_json(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Monitor).where(Monitor.slug == slug))
    monitor = result.scalar_one_or_none()

    if not monitor:
        return JSONResponse({"error": "Not found"}, status_code=404)

    return JSONResponse({
        "name": monitor.name,
        "status": monitor.status,
        "last_ping": monitor.last_ping_at.isoformat() if monitor.last_ping_at else None,
        "period": monitor.period,
        "grace": monitor.grace,
    })
