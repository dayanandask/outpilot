# Subspace Cold Outreach Pipeline

A fully automated cold-outreach pipeline from scratch — production-ready, secure, scalable, well-tested, and documented.

## Prerequisites
- Python 3.12+
- `uv` (Fast Python package and project manager)

## Quickstart
1. Clone the repository
2. Run `uv sync` to install dependencies
3. Copy `.env.example` to `.env` and fill in the required API keys
4. Run `python -m pipeline run <domain>` to execute the pipeline
5. Run `python -m pipeline run <domain> --dry-run` to preview the output

## API Quotas / Free Tier Limits
- **Ocean.io**: 5 req/min
- **Prospeo**: 10 req/min
- **Eazyreach**: 10 req/min
- **Brevo**: ~300 emails/day

## Environment Variables
See `.env.example` for details.
