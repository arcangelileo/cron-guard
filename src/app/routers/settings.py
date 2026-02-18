import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, hash_password, verify_password
from app.database import get_db
from app.main import templates
from app.models import User

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "success": None, "errors": None},
    )


@router.post("/profile")
async def update_profile(
    request: Request,
    alert_email: str = Form(""),
    email_alerts_enabled: str = Form("off"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert_email = alert_email.strip()
    user.alert_email = alert_email if alert_email else user.email
    user.email_alerts_enabled = email_alerts_enabled == "on"

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "success": "Profile updated successfully.", "errors": None},
    )


@router.post("/password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    errors = []

    if not verify_password(current_password, user.hashed_password):
        errors.append("Current password is incorrect.")
    if len(new_password) < 8:
        errors.append("New password must be at least 8 characters.")
    if new_password != new_password_confirm:
        errors.append("New passwords do not match.")

    if errors:
        return templates.TemplateResponse(
            "settings.html",
            {"request": request, "user": user, "success": None, "errors": errors},
            status_code=422,
        )

    user.hashed_password = hash_password(new_password)

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "success": "Password changed successfully.", "errors": None},
    )


@router.post("/api-key")
async def regenerate_api_key(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.api_key = str(uuid.uuid4())

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "success": "API key regenerated.", "errors": None},
    )
