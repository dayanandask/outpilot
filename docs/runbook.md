# Runbook

## Resume a failed run

```bash
uv run python -m pipeline run acme.com --resume run_abcdef12
```

## Add a new stage

1. Add client in `clients/`.
2. Add stage in `stages/` inheriting `BaseStage`.
3. Add Pydantic models if needed in `models.py`.
4. Register in `main.py` orchestrator.

## Swap Brevo for SendGrid

1. Replace `clients/brevo.py` with `SendGridClient`.
2. Keep `EmailTemplateEngine` and `OutreachStage` interfaces.

## Debugging

- Logs are structured JSON via structlog.
- Check `runs/{run_id}.db` for SQLite state.
- Use `list-runs` CLI command.
