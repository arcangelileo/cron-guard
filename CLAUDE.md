# CronGuard

Phase: COMPLETE

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
- **Auth**: JWT in httponly cookies, bcrypt passwords, standard login/register flow. Custom `AuthRequired` exception with app-level handler for proper 303 redirects.
- **Database**: Single SQLite file, async SQLAlchemy, Alembic migrations.
- **Templates**: Jinja2 + Tailwind CSS via CDN + Inter font. Dashboard-first design.
- **API key**: Auto-generated per user for programmatic monitor management. Passed via `X-Api-Key` header.
- **Tests**: pytest + httpx async test client, in-memory SQLite. 62 tests covering all features.

## Task Backlog
- [x] Create project structure (pyproject.toml, src/app/, configs)
- [x] Set up FastAPI app skeleton with health check and config
- [x] Create database models (User, Monitor, Ping, Alert) and Alembic migrations
- [x] Implement user auth (register, login, logout, JWT middleware)
- [x] Build auth UI (login/register pages with Tailwind styling)
- [x] Implement monitor CRUD (create, edit, delete, pause/resume)
- [x] Build dashboard UI (monitor list with status indicators, create/edit forms)
- [x] Implement ping endpoint (`/ping/{slug}` — fast, no-auth, records ping)
- [x] Build ping history / monitor detail page
- [x] Implement background checker (APScheduler job for overdue detection)
- [x] Implement email alerts (down + recovery notifications via SMTP)
- [x] Implement webhook alerts (POST JSON to user-configured URLs)
- [x] Build settings page (profile, email prefs, API key management)
- [x] Add public badge/status endpoint per monitor
- [x] Write comprehensive tests (auth, monitors, pings, checker, alerts)
- [x] Write Dockerfile and docker-compose.yml
- [x] Write README with setup and deploy instructions
- [x] QA pass: bug fixes, UI polish, expanded test coverage
- [x] Production deployment: Dockerfile, docker-compose, .env.example, comprehensive README, final code cleanup

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

### Session 3 — FULL MVP IMPLEMENTATION
- Created all database models: User, Monitor, Ping, Alert with SQLAlchemy mapped columns, relationships, and cascading deletes
- Implemented complete auth system: JWT in httponly cookies, bcrypt password hashing, register/login/logout, API key auth via X-Api-Key header
- Built auth UI: professional split-panel login/register pages with Tailwind CSS, form validation, error display
- Implemented full monitor CRUD: create with period presets (1min–weekly), edit, delete, pause/resume with proper state transitions
- Built dashboard: stats cards (total/up/down/new), monitor table with status indicators, empty state with quick-start guide
- Built monitor detail page: ping URL with copy button, status badge preview, configuration display, ping history table
- Implemented ping endpoint: `/ping/{slug}` accepts GET/POST, no auth, records timestamp + IP + user-agent, handles recovery from down state
- Implemented background checker: APScheduler job every 60 seconds, detects overdue monitors (last_ping + period + grace < now), transitions to down
- Implemented email alerts: SMTP via aiosmtplib, dev mode logs to console, sends on down + recovery transitions
- Implemented webhook alerts: POST JSON payload to user-configured URL with 5s timeout
- Built settings page: alert email preferences, change password, API key display + regenerate
- Added public badge endpoint: SVG and JSON status badges per monitor at `/badge/{slug}.svg` and `/badge/{slug}.json`
- Created base template with responsive nav, mobile-friendly layout, Tailwind CSS + Inter font
- Wrote 54 comprehensive tests covering auth, monitors, pings, badges, checker, and settings — all passing
- Created Dockerfile and docker-compose.yml for deployment
- Wrote README with setup instructions, config reference, and integration examples
- All backlog items complete — phase changed to QA

### Session 4 — QA & POLISH
**Bugs found and fixed:**
1. **Auth redirect bug** — `get_current_user` used `HTTPException` with status 303 + Location header, but FastAPI's default exception handler returns JSON for HTTPException, not a redirect. Unauthenticated users saw JSON error instead of being redirected to login. **Fix:** Created custom `AuthRequired` exception class and registered an `@app.exception_handler(AuthRequired)` that returns a proper `RedirectResponse("/auth/login", status_code=303)`.
2. **Email alert body string concatenation bug** — In `alerts.py`, the recovery email body was constructed using a ternary inline `if/else` with implicit f-string concatenation. Due to Python operator precedence, the `if alert_type == "down"` only applied to the first string literal; the remaining f-strings were always concatenated. **Fix:** Replaced with explicit `if/else` block to construct the body correctly for each alert type.
3. **Dockerfile build order bug** — `pip install --no-cache-dir .` was run before `src/` was copied, but `pyproject.toml` references `where = ["src"]` for package discovery, causing the install to fail. **Fix:** Moved `COPY src/ src/` before the `pip install` step.
4. **Dockerfile/docker-compose.yml SQLite path bug** — Used `sqlite+aiosqlite:///data/cronguard.db` (3 slashes = relative path) instead of `sqlite+aiosqlite:////data/cronguard.db` (4 slashes = absolute path `/data/cronguard.db`). **Fix:** Added the 4th slash in both Dockerfile and docker-compose.yml.

**UI polish completed:**
- Added emoji favicon (clock icon) via inline SVG data URI
- Added `<meta description>` tag for SEO
- Added Inter font weight 300 and 800 for more typographic range
- Defined reusable CSS utility classes: `.btn-primary`, `.btn-secondary`, `.input-field`
- Added user avatar initial circle in navigation bar
- Added persistent footer with copyright and version info
- Enhanced login page: deeper gradient (brand-700→950), decorative SVG background circles, green checkmark badges for feature list, 4th feature bullet (status badges)
- Enhanced register page: matching gradient treatment, styled code example box with syntax highlighting
- Enhanced error messages across all forms with warning icon SVGs
- Enhanced dashboard stats cards with contextual icons (list, checkmark, alert, clock)
- Enhanced dashboard monitor table with ring borders on status badges, hover reveal on View button
- Enhanced empty state with numbered step circles instead of plain numbers
- Enhanced monitor detail page with proper breadcrumb navigation, section icons, green dots in ping history timeline, improved empty state
- Enhanced monitor form with breadcrumb navigation, consistent button classes
- Enhanced settings page with grid layout for account info, consistent button/input classes, success message with checkmark icon

**Test coverage expanded (54 → 62 tests):**
- `test_register_duplicate_username` — duplicate username registration
- `test_settings_requires_auth_redirect` — settings auth redirect
- `test_monitors_new_requires_auth` — new monitor auth redirect
- `test_authenticated_user_redirected_from_register` — authed user visiting register page
- `test_expired_token_redirects_to_login` — invalid/expired JWT token handling
- `test_root_redirects` — root URL redirect for unauthenticated users
- `test_root_redirects_to_dashboard_when_authed` — root URL redirect for authenticated users
- `test_ping_recovery_from_down` — verifies ping to a down monitor creates recovery alert and transitions to up

**All 62 tests passing. Phase changed from QA → DEPLOYMENT.**

### Session 5 — DEPLOYMENT & FINALIZATION
- Enhanced Dockerfile: multi-stage build (builder + runtime), non-root `cronguard` user, OCI labels, health check via `/health` endpoint, exec-form CMD for proper signal handling, persistent `/data` volume
- Updated docker-compose.yml: container name, optional `.env` file loading, production-ready SMTP defaults (port 587, TLS enabled), health check
- Created `.env.example` with fully documented environment variables, SMTP provider examples (Gmail, SendGrid, Mailgun), and secret key generation instructions
- Wrote comprehensive README.md: feature list, architecture diagram, quick start (Docker one-liner), local dev setup, full API reference with all 24 endpoints, ping integration examples (Bash, Python, Node.js, PowerShell, wget, Docker healthcheck), architecture overview, monitor status flow diagram, tech stack table, development guide
- Final code cleanup: fixed 9 ruff lint issues — removed 6 unused imports (RedirectResponse, Response, AsyncSession, selectinload, get_current_user_optional), replaced 2 `== True` comparisons with `.is_(True)` for SQLAlchemy column filters, removed 1 unused variable assignment
- All 62 tests passing, ruff lint clean
- **Phase changed from DEPLOYMENT → COMPLETE**

## Known Issues
(none)

## Files Structure
```
cron-guard/
├── CLAUDE.md
├── README.md                   # Comprehensive setup, API docs, architecture
├── .gitignore
├── .env.example                # Documented environment variables template
├── pyproject.toml              # Project config, dependencies, pytest/ruff settings
├── Dockerfile                  # Multi-stage production build, non-root user
├── docker-compose.yml          # One-command Docker deployment
├── alembic.ini                 # Alembic migration config
├── alembic/
│   ├── env.py                  # Async Alembic environment
│   ├── script.py.mako          # Migration template
│   └── versions/               # Migration files
├── src/
│   └── app/
│       ├── __init__.py
│       ├── config.py           # Pydantic settings (DB, auth, SMTP, etc.)
│       ├── database.py         # Async SQLAlchemy engine, session, Base
│       ├── main.py             # FastAPI app, lifespan, scheduler, router wiring
│       ├── models.py           # SQLAlchemy models (User, Monitor, Ping, Alert)
│       ├── auth.py             # JWT/bcrypt auth, get_current_user, AuthRequired exception
│       ├── alerts.py           # Email + webhook alert sending
│       ├── checker.py          # Background overdue monitor checker
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py         # Register, login, logout endpoints
│       │   ├── monitors.py     # Dashboard, monitor CRUD, pause/resume
│       │   ├── ping.py         # Ping endpoint (no auth, GET/POST)
│       │   ├── badge.py        # SVG + JSON status badges
│       │   └── settings.py     # Profile, password, API key management
│       ├── static/
│       │   └── .gitkeep
│       └── templates/
│           ├── base.html       # Base layout with nav, footer, Tailwind, Inter font
│           ├── dashboard.html  # Monitor list with stats cards
│           ├── settings.html   # Settings page
│           ├── auth/
│           │   ├── login.html  # Login page (split-panel with branding)
│           │   └── register.html # Registration page
│           └── monitors/
│               ├── form.html   # Create/edit monitor form
│               └── detail.html # Monitor detail + ping history
└── tests/
    ├── __init__.py
    ├── conftest.py             # Test fixtures (in-memory DB, async client)
    ├── test_health.py          # Health check tests (2 tests)
    ├── test_auth.py            # Auth tests (24 tests)
    ├── test_monitors.py        # Monitor CRUD tests (12 tests)
    ├── test_ping.py            # Ping endpoint tests (8 tests)
    ├── test_badge.py           # Badge endpoint tests (4 tests)
    ├── test_checker.py         # Background checker tests (5 tests)
    └── test_settings.py        # Settings page tests (7 tests)
```
