import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import settings
from app.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cronguard")

templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(templates_dir))

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models to register with Base
    import app.models  # noqa: F401

    # Create tables on startup (dev convenience; production uses Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background checker
    from app.checker import check_overdue_monitors

    scheduler.add_job(check_overdue_monitors, "interval", seconds=60, id="overdue_checker")
    scheduler.start()
    logger.info("Background checker started (60s interval)")

    yield

    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Register auth redirect exception handler
from app.auth import AuthRequired  # noqa: E402


@app.exception_handler(AuthRequired)
async def auth_required_handler(request: Request, exc: AuthRequired):
    return RedirectResponse("/auth/login", status_code=303)


# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
from app.routers import auth, monitors, ping, badge, settings as settings_router  # noqa: E402

app.include_router(auth.router)
app.include_router(monitors.router)
app.include_router(ping.router)
app.include_router(badge.router)
app.include_router(settings_router.router)


@app.get("/")
async def root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/auth/login", status_code=303)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }
