# Subspace Cold Outreach Pipeline

A fully automated cold-outreach pipeline — production-ready, secure, scalable, well-tested, and documented.

## Architecture

```
INPUT: stripe.com
  │
  ▼
Stage 1 — Apollo.io
  POST /organizations/search  → similar companies
  POST /mixed_people/search   → decision-makers
  Output: tuple(list[Company], list[Prospect])
  │
  ▼
Stage 2 — Email Resolution
  Apollo email → use directly
  Else → Prospeo /search-person + /enrich-person
  Output: list[Contact]
  │
  ▼
⚠ SAFETY CHECKPOINT
  Rich table → user must type "send"
  │
  ▼
Stage 3 — Brevo
  POST /v3/smtp/email → send personalized emails
  Output: list[OutreachRecord]
  │
  ▼
SQLite (runs/{run_id}.db)
```

## Quickstart

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env

# 3. Dry run (no emails sent)
uv run python -m pipeline run stripe.com --dry-run

# 4. Live run
uv run python -m pipeline run stripe.com
```

## Commands

| Command | Description |
|---------|-------------|
| `uv run python -m pipeline run <domain>` | Full pipeline |
| `uv run python -m pipeline run <domain> --dry-run` | Stages 1-3 only |
| `uv run python -m pipeline list-runs` | List past runs |
| `uv run python -m pipeline status <run_id>` | Show run details |

## API Services

| Service | Purpose | Auth Header |
|---------|---------|-------------|
| Apollo.io | Companies + people search | `x-api-key` |
| Prospeo | Email enrichment fallback | `X-KEY` |
| Brevo | Transactional email delivery | `api-key` |

## Free Tier Limits

- **Apollo.io**: Free plan blocks `/mixed_people/search` (403)
- **Prospeo**: Check credits before bulk runs
- **Brevo**: ~300 emails/day on free tier (enforced by `DAILY_EMAIL_CAP`)

## Development

```bash
# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/ --strict

# Security scan
uv run bandit -r src/ -ll
```

## Tech Stack

- Python 3.12+
- uv (package manager)
- Pydantic v2 + SQLModel + aiosqlite
- httpx + asyncio + tenacity
- Typer + Rich (CLI)
- pytest + respx + pytest-asyncio
- ruff + mypy + bandit
