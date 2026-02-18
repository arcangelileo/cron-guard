# CronGuard

Phase: DEVELOPMENT

## Project Spec
- **Idea**: CronGuard is a dead man's switch monitoring service for cron jobs and scheduled tasks. Users create monitors with expected intervals (e.g., "every 5 minutes", "daily at 3am"). Their scripts ping a unique URL on each successful run. If a ping is missed beyond the grace period, CronGuard alerts the team via email (and optionally webhook). Think Healthchecks.io / Cronitor / Dead Man's Snitch — a focused, developer-friendly tool that catches the #1 ops failure: silent cron job breakage.
- **Target users**: Developers, DevOps engineers, small-to-mid SaaS teams, freelancers running scheduled backups/reports/syncs. Anyone with cron jobs, scheduled tasks, or periodic scripts that must not fail silently.
- **Revenue model**: Freemium subscription. Free tier: 5 monitors, email alerts only, 1-day log retention. Pro ($9/mo): 50 monitors, webhook alerts, 30-day log retention, team members. Business ($29/mo): unlimited monitors, 90-day retention, priority support, API access, Slack integration.
- **Tech stack**: Python, FastAPI, SQLite (via async SQLAlchemy + aiosqlite), Jinja2 + Tailwind CSS (CDN), APScheduler, Docker
- **Repo**: https://github.com/arcangelileo/cron-guard
- **MVP scope**:
  - User registration & login (JWT + httponly cookies)
  - Dashboard listing all monitors with status (up/down/new)
  - Create/edit/delete monitors with name, expected period, grace period
  - Unique ping URL per monitor (GET or POST, returns 200 OK)
  - Ping history log per monitor
  - Background checker that evaluates overdue monitors every 60 seconds
  - Email alerts when a monitor goes down (and recovery notifications)
  - Webhook alert support (POST JSON to user-configured URL)
  - Public badge/status endpoint per monitor (SVG or JSON)
  - Settings page (profile, email preferences, API key)
  - Responsive, professional UI with real-time status indicators

## Architecture Decisions
- **Ping endpoint**: `/ping/{monitor_slug}` — accepts GET/POST, records timestamp, returns `200 OK` with plain text. Must be fast (<10ms logic). No auth required on ping endpoints.
- **Monitor slug**: UUID4-based for uniqueness and unguessability. Displayed as `/ping/a1b2c3d4-...`.
- **Period/grace model**: Period in seconds (with human-friendly presets: 1min, 5min, 15min, hourly, daily, weekly). Grace period also in seconds (default: period × 0.5, min 60s).
- **Status logic**: `new` (never pinged), `up` (last ping within period+grace), `down` (last ping older than period+grace), `paused` (manually paused by user).
- **Checker loop**: APScheduler job runs every 60 seconds. Queries monitors where `last_ping_at + period + grace < now()` and `status != 'down'` and `status != 'paused'`. Transitions to `down`, creates alert record, sends notifications.
- **Recovery**: When a ping arrives for a `down` monitor, transition to `up`, send recovery notification.
- **Alert dedup**: Only alert on status transitions (up→down, down→up). No repeated alerts for continued downtime.
- **Email**: SMTP via `aiosmtplib` with Pydantic settings for SMTP config. In dev, log to console.
- **Webhook alerts**: POST JSON payload `{monitor_name, status, timestamp, details}` to user-configured URL with 5s timeout.
- **Auth**: JWT in httponly cookies, bcrypt passwords, standard login/register flow.
- **Database**: Single SQLite file, async SQLAlchemy, Alembic migrations.
- **Templates**: Jinja2 + Tailwind CSS via CDN + Inter font. Dashboard-first design.
- **API key**: Auto-generated per user for programmatic monitor management. Passed via `X-Api-Key` header.
- **Tests**: pytest + httpx async test client, in-memory SQLite.

## Task Backlog
- [x] Create project structure (pyproject.toml, src/app/, configs)
- [x] Set up FastAPI app skeleton with health check and config
- [ ] Create database models (User, Monitor, Ping, Alert) and Alembic migrations
- [ ] Implement user auth (register, login, logout, JWT middleware)
- [ ] Build auth UI (login/register pages with Tailwind styling)
- [ ] Implement monitor CRUD (create, edit, delete, pause/resume)
- [ ] Build dashboard UI (monitor list with status indicators, create/edit forms)
- [ ] Implement ping endpoint (`/ping/{slug}` — fast, no-auth, records ping)
- [ ] Build ping history / monitor detail page
- [ ] Implement background checker (APScheduler job for overdue detection)
- [ ] Implement email alerts (down + recovery notifications via SMTP)
- [ ] Implement webhook alerts (POST JSON to user-configured URLs)
- [ ] Build settings page (profile, email prefs, API key management)
- [ ] Add public badge/status endpoint per monitor
- [ ] Write comprehensive tests (auth, monitors, pings, checker, alerts)
- [ ] Write Dockerfile and docker-compose.yml
- [ ] Write README with setup and deploy instructions

## Progress Log
### Session 1 — IDEATION
- Chose idea: CronGuard — dead man's switch monitoring for cron jobs
- Rationale: proven market (Cronitor, Healthchecks.io, Dead Man's Snitch all charge $20-100+/mo), simple to build (receive pings, alert on missed), complements StatusPing (external uptime vs internal job monitoring), clear freemium model
- Created spec and backlog

### Session 2 — SCAFFOLDING
- Created GitHub repo: https://github.com/arcangelileo/cron-guard
- Set up project structure: pyproject.toml with all dependencies, src/app/ layout
- Created FastAPI app skeleton with health check endpoint (`GET /health`)
- Set up async SQLAlchemy database layer with in-memory SQLite for tests
- Configured Alembic for async migrations
- Created Pydantic settings with env var support (`CRONGUARD_` prefix)
- Wrote and passed health check tests (pytest + httpx async client)
- Phase changed from SCAFFOLDING → DEVELOPMENT

## Known Issues
(none yet)

## Files Structure
```
cron-guard/
├── CLAUDE.md
├── .gitignore
├── pyproject.toml              # Project config, dependencies, pytest/ruff settings
├── alembic.ini                 # Alembic migration config
├── alembic/
│   ├── env.py                  # Async Alembic environment
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files (empty)
├── src/
│   └── app/
│       ├── __init__.py
│       ├── config.py           # Pydantic settings (DB, auth, SMTP, etc.)
│       ├── database.py         # Async SQLAlchemy engine, session, Base
│       ├── main.py             # FastAPI app, lifespan, health check
│       ├── routers/
│       │   └── __init__.py
│       ├── static/
│       │   └── .gitkeep
│       └── templates/
│           └── .gitkeep
└── tests/
    ├── __init__.py
    ├── conftest.py             # Test fixtures (in-memory DB, async client)
    └── test_health.py          # Health check endpoint tests
```
