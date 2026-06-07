# API Integration

## Apollo
- Auth: `APOLLO_API_KEY` header via BaseAPIClient.
- Endpoints used: `/organizations/search`, `/mixed_people/search`
- Rate limits: configured per service via `RateLimiter`.
- Retries: exponential backoff, 429 handled with Retry-After.

## Prospeo
- Auth: `X-KEY` header.
- Endpoint: `/search-person`
- Rate limits: `PROSPEO_RPM` (default 10)

## Brevo
- Auth: `api-key` header (`BREVO_API_KEY`).
- Endpoint: `/smtp/email`
- Free tier: ~300 emails/day. Enforced by `DAILY_EMAIL_CAP`.
