# CronGuard

**Dead man's switch monitoring for cron jobs and scheduled tasks.**

CronGuard watches your cron jobs so you don't have to. Create a monitor, add a single `curl` to your script, and get alerted the moment a job stops running. No more silent failures.

---

## Features

- **Dead man's switch detection** — monitors go DOWN if they miss their expected ping window
- **Email & webhook alerts** — instant notifications on failure and recovery
- **Fast ping endpoint** — simple GET/POST, no auth required, sub-10ms response
- **Dashboard** — real-time overview of all monitors with status indicators
- **Status badges** — embeddable SVG/JSON badges for READMEs and status pages
- **API key access** — manage monitors programmatically
- **Pause/resume** — temporarily disable monitoring without deleting
- **Background checker** — evaluates overdue monitors every 60 seconds
- **Recovery alerts** — get notified when a down monitor comes back up

## How It Works

```
┌─────────────┐       ┌─────────────────┐       ┌───────────────┐
│  Your Cron   │──────▶│  GET /ping/:id   │──────▶│   CronGuard   │
│    Job       │ curl  │  (no auth, fast) │       │   Database    │
└─────────────┘       └─────────────────┘       └───────┬───────┘
                                                        │
                                         Every 60s ─────┘
                                                        │
                                                ┌───────▼───────┐
                                                │  Overdue?     │
                                                │  → Alert!     │
                                                └───────────────┘
```

1. **Create a monitor** with the expected run interval (e.g., every 5 minutes, hourly, daily)
2. **Add a ping** to the end of your cron script: `curl -fsS https://your-domain.com/ping/YOUR-MONITOR-ID`
3. **Get alerted** via email or webhook if a ping is missed beyond the grace period

---

## Quick Start

### Docker (recommended)

```bash
# One-liner: generate a secret key and start CronGuard
CRONGUARD_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))") \
  docker compose up -d
```

Open **http://localhost:8000** — create an account, add a monitor, and start pinging.

### Docker with .env file

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env — at minimum, set CRONGUARD_SECRET_KEY

# Start
docker compose up -d
```

### From Source

```bash
# Clone
git clone https://github.com/arcangelileo/cron-guard.git
cd cron-guard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies (with dev tools)
pip install -e ".[dev]"

# Run the app
uvicorn app.main:app --reload

# Open http://localhost:8000
```

---

## Configuration

All settings use the `CRONGUARD_` prefix and can be set via environment variables or a `.env` file. See [`.env.example`](.env.example) for a ready-to-use template.

| Variable | Default | Description |
|---|---|---|
| `CRONGUARD_SECRET_KEY` | `change-me-in-production` | **Required.** JWT signing key. Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CRONGUARD_DATABASE_URL` | `sqlite+aiosqlite:///cronguard.db` | Database connection string. Use 4 slashes for absolute paths in Docker: `sqlite+aiosqlite:////data/cronguard.db` |
| `CRONGUARD_BASE_URL` | `http://localhost:8000` | Public URL shown in ping URLs and email links |
| `CRONGUARD_SMTP_HOST` | `localhost` | SMTP server hostname. Leave as `localhost:1025` for dev mode (console logging) |
| `CRONGUARD_SMTP_PORT` | `1025` | SMTP server port (use 587 for TLS in production) |
| `CRONGUARD_SMTP_FROM_EMAIL` | `alerts@cronguard.dev` | Sender address for alert emails |
| `CRONGUARD_SMTP_USER` | _(empty)_ | SMTP authentication username |
| `CRONGUARD_SMTP_PASSWORD` | _(empty)_ | SMTP authentication password |
| `CRONGUARD_SMTP_TLS` | `false` | Enable SMTP TLS (`true` for production) |
| `CRONGUARD_PORT` | `8000` | Host port mapping (docker-compose only) |

---

## API Reference

### Ping Endpoint

The core of CronGuard. Call this from your cron jobs — no authentication required.

```
GET  /ping/{monitor_slug}
POST /ping/{monitor_slug}
```

**Response:** `200 OK` with plain text body `OK`

**Example:**
```bash
# At the end of your cron job
curl -fsS https://cronguard.example.com/ping/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "app": "CronGuard",
  "version": "0.1.0"
}
```

### Status Badge

Public endpoints for embedding monitor status. No authentication required.

```
GET /badge/{monitor_slug}.svg    → SVG image badge
GET /badge/{monitor_slug}.json   → JSON status object
```

**JSON response:**
```json
{
  "name": "Nightly Backup",
  "status": "up",
  "last_ping": "2026-02-19T03:00:12.345678",
  "period": 86400,
  "grace": 43200
}
```

**Embed in Markdown:**
```markdown
![Monitor Status](https://cronguard.example.com/badge/YOUR-MONITOR-ID.svg)
```

### Authentication

CronGuard supports two authentication methods:

1. **Session cookies** — JWT stored in httponly cookies (used by the web UI)
2. **API key** — passed via `X-Api-Key` header (for programmatic access)

Your API key is available on the Settings page.

### Web Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | No | Redirects to dashboard or login |
| `GET` | `/health` | No | Health check |
| `GET/POST` | `/ping/{slug}` | No | Receive ping from cron job |
| `GET` | `/badge/{slug}.svg` | No | SVG status badge |
| `GET` | `/badge/{slug}.json` | No | JSON status |
| `GET` | `/auth/register` | No | Registration page |
| `POST` | `/auth/register` | No | Create account |
| `GET` | `/auth/login` | No | Login page |
| `POST` | `/auth/login` | No | Authenticate |
| `GET` | `/auth/logout` | Yes | Log out (clears cookie) |
| `GET` | `/dashboard` | Yes | Monitor dashboard |
| `GET` | `/monitors/new` | Yes | Create monitor form |
| `POST` | `/monitors/new` | Yes | Create monitor |
| `GET` | `/monitors/{id}` | Yes | Monitor detail + ping history |
| `GET` | `/monitors/{id}/edit` | Yes | Edit monitor form |
| `POST` | `/monitors/{id}/edit` | Yes | Update monitor |
| `POST` | `/monitors/{id}/delete` | Yes | Delete monitor |
| `POST` | `/monitors/{id}/pause` | Yes | Pause monitoring |
| `POST` | `/monitors/{id}/resume` | Yes | Resume monitoring |
| `GET` | `/settings` | Yes | Settings page |
| `POST` | `/settings/profile` | Yes | Update alert preferences |
| `POST` | `/settings/password` | Yes | Change password |
| `POST` | `/settings/api-key` | Yes | Regenerate API key |

---

## Ping Integration Examples

### Bash / Cron

```bash
# Add to the end of your crontab entry
*/5 * * * * /path/to/backup.sh && curl -fsS https://cronguard.example.com/ping/YOUR-MONITOR-ID
```

### Python

```python
import requests

def main():
    # ... your job logic ...
    requests.get("https://cronguard.example.com/ping/YOUR-MONITOR-ID", timeout=5)

if __name__ == "__main__":
    main()
```

### Node.js

```javascript
const https = require('https');

// At the end of your job
https.get('https://cronguard.example.com/ping/YOUR-MONITOR-ID');
```

### PowerShell

```powershell
# At the end of your scheduled task
Invoke-WebRequest -Uri "https://cronguard.example.com/ping/YOUR-MONITOR-ID" -UseBasicParsing
```

### wget

```bash
wget -q --spider https://cronguard.example.com/ping/YOUR-MONITOR-ID
```

### Docker healthcheck

```dockerfile
HEALTHCHECK --interval=5m CMD curl -fsS https://cronguard.example.com/ping/YOUR-MONITOR-ID
```

---

## Architecture

```
cron-guard/
├── src/app/
│   ├── main.py             # FastAPI app, lifespan, scheduler, router wiring
│   ├── config.py           # Pydantic settings with CRONGUARD_ prefix
│   ├── database.py         # Async SQLAlchemy engine + session
│   ├── models.py           # User, Monitor, Ping, Alert models
│   ├── auth.py             # JWT + bcrypt auth, API key support
│   ├── alerts.py           # Email (SMTP) + webhook alert delivery
│   ├── checker.py          # Background job: detect overdue monitors
│   ├── routers/
│   │   ├── auth.py         # Register, login, logout
│   │   ├── monitors.py     # Dashboard, CRUD, pause/resume
│   │   ├── ping.py         # Ping endpoint (no auth)
│   │   ├── badge.py        # SVG + JSON status badges
│   │   └── settings.py     # Profile, password, API key
│   └── templates/          # Jinja2 + Tailwind CSS templates
├── tests/                  # 62 async tests (pytest + httpx)
├── alembic/                # Database migrations
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # One-command deployment
└── pyproject.toml          # Dependencies and tool config
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web framework** | FastAPI (async) |
| **Database** | SQLite via async SQLAlchemy + aiosqlite |
| **Migrations** | Alembic |
| **Templates** | Jinja2 + Tailwind CSS (CDN) |
| **Auth** | JWT (httponly cookies) + bcrypt |
| **Background jobs** | APScheduler (AsyncIOScheduler) |
| **Email** | aiosmtplib |
| **HTTP client** | httpx (for webhook delivery) |
| **Testing** | pytest + pytest-asyncio + httpx |

### Monitor Status Flow

```
  Created         First ping        Ping missed
  ┌─────┐         ┌─────┐          ┌─────┐
  │ new │────────▶│ up  │────────▶│down │
  └─────┘         └──┬──┘          └──┬──┘
                     │    ◀────────────┘
                     │     Recovery ping
                     │
                  ┌──▼────┐
                  │paused │  (manual pause/resume)
                  └───────┘
```

### Alert Logic

- Alerts fire only on **status transitions** (up→down, down→up) — no repeated alerts for continued downtime
- **Down alert**: sent when the background checker detects `last_ping + period + grace < now`
- **Recovery alert**: sent immediately when a ping arrives for a `down` monitor
- Channels: email (SMTP) and webhook (POST JSON to user-configured URL)

---

## Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Locally

```bash
# Start the development server with auto-reload
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with output
pytest tests/ -v -s
```

### Code Formatting

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

---

## License

MIT
