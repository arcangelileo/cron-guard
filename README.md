# CronGuard

Dead man's switch monitoring for cron jobs and scheduled tasks. Get alerted the moment a job stops running.

## How It Works

1. **Create a monitor** with the expected run interval (e.g., every 5 minutes, hourly, daily)
2. **Add a ping** to the end of your cron script: `curl -fsS https://your-domain.com/ping/YOUR-MONITOR-ID`
3. **Get alerted** via email or webhook if a ping is missed beyond the grace period

## Features

- **Dead man's switch detection** — monitors go DOWN if they miss their expected ping
- **Email & webhook alerts** — get notified on down and recovery events
- **Fast ping endpoint** — simple GET/POST, no auth required, <10ms
- **Status badges** — embed SVG/JSON status badges in your README
- **API key access** — manage monitors programmatically via `X-Api-Key` header
- **Background checker** — evaluates overdue monitors every 60 seconds
- **Pause/resume** — temporarily disable monitoring without deleting

## Quick Start

### With Docker

```bash
docker compose up -d
```

Open http://localhost:8000 — create an account, add a monitor, and start pinging.

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the app
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v
```

## Configuration

All settings use the `CRONGUARD_` prefix and can be set via environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `CRONGUARD_SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `CRONGUARD_DATABASE_URL` | `sqlite+aiosqlite:///cronguard.db` | Database connection string |
| `CRONGUARD_BASE_URL` | `http://localhost:8000` | Public URL (for ping URLs) |
| `CRONGUARD_SMTP_HOST` | `localhost` | SMTP server host |
| `CRONGUARD_SMTP_PORT` | `1025` | SMTP server port |
| `CRONGUARD_SMTP_FROM_EMAIL` | `alerts@cronguard.dev` | From address for alerts |
| `CRONGUARD_SMTP_USER` | _(empty)_ | SMTP username |
| `CRONGUARD_SMTP_PASSWORD` | _(empty)_ | SMTP password |
| `CRONGUARD_SMTP_TLS` | `false` | Enable SMTP TLS |

## Ping Integration Examples

**Bash / Cron:**
```bash
# Add to end of your cron script
curl -fsS https://cronguard.dev/ping/YOUR-MONITOR-ID
```

**Python:**
```python
import requests
requests.get("https://cronguard.dev/ping/YOUR-MONITOR-ID")
```

**PowerShell:**
```powershell
Invoke-WebRequest -Uri "https://cronguard.dev/ping/YOUR-MONITOR-ID" -UseBasicParsing
```

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy (async), SQLite
- **Frontend:** Jinja2, Tailwind CSS (CDN), Inter font
- **Background:** APScheduler
- **Auth:** JWT (httponly cookies), bcrypt

## License

MIT
