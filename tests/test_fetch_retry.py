"""
Unit tests for _fetch_with_retry.

Covers the retry contract documented in ARCHITECTURE.md:
  - Returns immediately on any non-5xx status (200, 404, 429, 400, 403)
  - Retries on HTTP 500, 502, 503, 504 up to _MAX_RETRIES additional attempts
  - Applies exponential backoff between retries: base * 2^(attempt-1)
  - TimeoutException -> raises HTTP 504 immediately, no retry
  - RequestError (network failure) -> retries, then raises HTTP 502
  - Succeeds on a later attempt after earlier transient failures
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from api.core import (
    _BACKOFF_BASE,
    _MAX_RETRIES,
    _RETRYABLE_STATUS,
    _fetch_with_retry,
)


def make_response(status_code: int) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    return response


# Immediate return - non-retryable status codes
class TestImmediateReturn:
    """The function must return on the first attempt for non-retryable statuses."""

    @pytest.mark.parametrize("status_code", [200, 400, 403, 404, 429])
    async def test_returns_on_first_attempt(self, status_code, address):
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = make_response(status_code)

        result = await _fetch_with_retry(client, address)

        assert result.status_code == status_code
        assert client.get.call_count == 1

    async def test_does_not_sleep_on_200(self, address):
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = make_response(200)

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await _fetch_with_retry(client, address)

        mock_sleep.assert_not_called()


# Retry behavior on 5xx responses
class TestRetryOn5xx:
    """All four retryable status codes must trigger the full retry cycle."""

    @pytest.mark.parametrize("status_code", sorted(_RETRYABLE_STATUS))
    async def test_exhausts_all_attempts_on_persistent_5xx(self, status_code, address):
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = make_response(status_code)

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch_with_retry(client, address)

        assert result.status_code == status_code
        assert client.get.call_count == _MAX_RETRIES + 1

    async def test_stops_retrying_on_first_success(self, address):
        """Recovers mid-retry: 503 on attempt 1, 200 on attempt 2."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.side_effect = [make_response(503), make_response(200)]

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch_with_retry(client, address)

        assert result.status_code == 200
        assert client.get.call_count == 2

    async def test_returns_last_5xx_after_all_retries_exhausted(self, address):
        """The final non-200 response is returned to the caller for inspection."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = make_response(502)

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch_with_retry(client, address)

        assert result.status_code == 502


# Exponential backoff
class TestExponentialBackoff:
    """Sleep durations must follow: base * 2^(attempt-1) + jitter(0..0.3)."""

    async def test_sleep_durations_are_correct(self, address):
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = make_response(500)

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await _fetch_with_retry(client, address)

        actual_delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert len(actual_delays) == _MAX_RETRIES
        for i, delay in enumerate(actual_delays):
            base = _BACKOFF_BASE * (2 ** i)
            # Jitter adds up to 0.3s on top of the base backoff
            assert base <= delay <= base + 0.3, (
                f"attempt {i+1}: delay {delay:.3f}s not in [{base}, {base + 0.3}]"
            )

    async def test_sleep_called_between_retries_only(self, address):
        """Sleep is called exactly _MAX_RETRIES times — not before attempt 0."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.return_value = make_response(503)

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await _fetch_with_retry(client, address)

        assert mock_sleep.call_count == _MAX_RETRIES


# Exception handling
class TestExceptionHandling:

    async def test_timeout_raises_504_on_first_attempt(self, address):
        """
        TimeoutException means the 25-second budget is spent. Retrying would
        push past Vercel's 30-second function timeout. Must raise immediately.
        """
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.side_effect = httpx.TimeoutException("upstream timed out")

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_with_retry(client, address)

        assert exc_info.value.status_code == 504
        assert client.get.call_count == 1

    async def test_timeout_does_not_retry(self, address):
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.side_effect = httpx.TimeoutException("upstream timed out")

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(HTTPException):
                await _fetch_with_retry(client, address)

        mock_sleep.assert_not_called()

    async def test_network_error_retries_all_attempts(self, address):
        """RequestError (DNS failure, connection refused) is transient — retry."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.side_effect = httpx.RequestError("connection refused")

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await _fetch_with_retry(client, address)

        assert exc_info.value.status_code == 502
        assert client.get.call_count == _MAX_RETRIES + 1

    async def test_network_error_then_success_returns_200(self, address):
        """A transient network error followed by a successful attempt returns 200."""
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get.side_effect = [
            httpx.RequestError("temporary failure"),
            make_response(200),
        ]

        with patch("api.core.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch_with_retry(client, address)

        assert result.status_code == 200
        assert client.get.call_count == 2
