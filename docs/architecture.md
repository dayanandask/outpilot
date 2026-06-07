# Architecture

## Data Flow

```
Seed Domain
    │
    ▼
[Stage 1] Apollo ──► Companies + Prospects
    │
    ▼
[Stage 2] Email Resolution ──► Verified Contacts
    │
    ▼
[Checkpoint] User review
    │
    ▼
[Stage 3] Brevo ──► Outreach Records
    │
    ▼
SQLite (runs/{run_id}.db)
```

## Stages

### Stage 1: Lookalike Companies (Apollo)
- Searches organizations by seed domain.
- Prospecting people with decision-maker titles.

### Stage 2: Email Resolution (Eazyreach)
- Resolves LinkedIn URLs to verified work emails.
- Deduplicates contacts.

### Stage 3: Outreach (Brevo)
- Sends personalized emails via template engine.
- Enforces daily send cap.
