import asyncio
import time
from typing import Any, Dict, Optional
import httpx
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential_jitter,
)
import structlog
from pipeline.utils.rate_limiter import get_rate_limiter

logger = structlog.get_logger(__name__)


class AuthError(Exception):
    """Raised when an API returns 401 or 403."""

    pass


class RateLimitError(Exception):
    """Raised when retries are exhausted for 429 responses."""

    pass


class BaseAPIClient:
    """Base HTTP client with retry, rate limiting, and structured logging."""

    def __init__(
        self,
        base_url: str,
        stage_name: str,
        requests_per_minute: int,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.base_url = base_url
        self.stage_name = stage_name
        self.rate_limiter = get_rate_limiter(stage_name, requests_per_minute)
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers or {},
            timeout=timeout,
        )

    def _is_retryable_exception(self, retry_state: Any) -> bool:
        if not retry_state.outcome or not retry_state.outcome.failed:
            return False
        exc = retry_state.outcome.exception()
        if isinstance(exc, AuthError):
            return False
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if status in (429, 502, 503, 504):
                return True
            return False
        if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout)):
            return True
        return False

    async def _handle_retry_after(self, retry_state: Any) -> None:
        """Checks for Retry-After header and sleeps if necessary."""
        if retry_state.outcome and retry_state.outcome.failed:
            exc = retry_state.outcome.exception()
            if (
                isinstance(exc, httpx.HTTPStatusError)
                and exc.response.status_code == 429
            ):
                retry_after = exc.response.headers.get("Retry-After")
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(
                        "rate_limited",
                        stage=self.stage_name,
                        wait_seconds=wait_time,
                    )
                    await asyncio.sleep(wait_time)

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        """Executes an HTTP request with rate limiting and retries."""
        await self.rate_limiter.acquire()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=4, exp_base=2, jitter=1),
            retry=self._is_retryable_exception,
            before_sleep=self._handle_retry_after,
            reraise=True,
        ):
            with attempt:
                start_time = time.monotonic()
                try:
                    response = await self.client.request(method, endpoint, **kwargs)
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    status = e.response.status_code

                    if status in (401, 403):
                        logger.error(
                            "auth_failed",
                            stage=self.stage_name,
                            method=method,
                            endpoint=endpoint,
                            status=status,
                            elapsed_ms=elapsed_ms,
                        )
                        raise AuthError(
                            f"Authentication failed: {status} - {e.response.text}"
                        ) from e

                    logger.error(
                        "api_request_failed",
                        stage=self.stage_name,
                        method=method,
                        endpoint=endpoint,
                        status=status,
                        elapsed_ms=elapsed_ms,
                    )
                    raise
                except Exception as e:
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    logger.error(
                        "api_request_error",
                        stage=self.stage_name,
                        method=method,
                        endpoint=endpoint,
                        error=str(e),
                        elapsed_ms=elapsed_ms,
                    )
                    raise

                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                logger.info(
                    "api_request_success",
                    stage=self.stage_name,
                    method=method,
                    endpoint=endpoint,
                    status=response.status_code,
                    elapsed_ms=elapsed_ms,
                )
                return response
        raise Exception("Unreachable")

    async def close(self) -> None:
        await self.client.aclose()
