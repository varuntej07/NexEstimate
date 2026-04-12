"""
Shared fixtures for the NexEstimate test suite.

Provides a realistic mock of the private-zillow RapidAPI response and
helpers used across all three test modules.
"""

import copy
from typing import Any, AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.index import app


# Canonical fixture data — mirrors the real RapidAPI response shape
_FULL_PROPERTY_RESPONSE: dict[str, Any] = {
    "propertyDetails": {
        "zpid": 12345678,
        "streetAddress": "328 26th Avenue",
        "city": "Seattle",
        "state": "WA",
        "zipcode": "98122",
        "county": "King County",
        "zestimate": 850000,
        "zestimateLowPercent": "5",
        "zestimateHighPercent": "10",
        "rentZestimate": 3200,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "livingArea": 1800,
        "lotSize": 5000.0,
        "yearBuilt": 1998,
        "homeType": "SINGLE_FAMILY",
        "homeStatus": "FOR_SALE",
        "propertyTaxRate": 1.2,
        "price": 895000,
        "lastSoldPrice": 720000,
        "daysOnZillow": 14,
        "hiResImageLink": "https://photos.zillowstatic.com/fp/abc123.jpg",
        "streetViewImageUrl": "https://streetview.example.com/abc123.jpg",
        "hdpUrl": "/homedetails/328-26th-Ave-Seattle-WA-98122/12345678_zpid/",
        "description": "Beautiful home in Capitol Hill.",
        "pageViewCount": 1234,
        "favoriteCount": 56,
    },
    "zillowURL": "https://www.zillow.com/homedetails/12345678_zpid/",
}


@pytest.fixture
def full_property_response() -> dict[str, Any]:
    """
    Deep copy of the canonical RapidAPI response with all fields present.
    Each test gets an independent copy so mutations do not bleed between tests.
    """
    return copy.deepcopy(_FULL_PROPERTY_RESPONSE)


@pytest.fixture
def address() -> str:
    return "328 26th Avenue, Seattle, WA 98122"


# Environment
@pytest.fixture(autouse=True)
def patch_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure RAPIDAPI_KEY is always set for every test.
    The endpoint raises HTTP 500 when the key is absent; that failure mode
    is tested explicitly in test_endpoint.py by overriding this fixture.
    """
    monkeypatch.setattr("api.core.RAPIDAPI_KEY", "test-key-12345")


# HTTP test client
@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client wired directly to the FastAPI app via ASGI transport.
    No network socket is opened; requests never leave the process.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


# Rate limiter reset — prevents cross-test interference
@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Clear the in-memory rate limit storage before each test."""
    from api.index import limiter
    limiter.reset()


# Outbound httpx mock
def make_httpx_response(status_code: int, json_body: Optional[dict] = None) -> MagicMock:
    """
    Build a minimal httpx.Response stand-in with a controllable status code
    and optional JSON body.
    """
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_body or {}
    return response


@pytest.fixture
def mock_rapidapi(full_property_response: dict[str, Any]):
    """
    Patches httpx.AsyncClient inside api.index so the endpoint never makes
    real outbound requests. Yields the inner mock client so tests can inspect
    call counts and override return values.

    Usage:
        async def test_something(async_client, mock_rapidapi):
            mock_rapidapi.get.return_value = make_httpx_response(200, payload)
            response = await async_client.get("/api/estimate?address=...")
    """
    mock_response = make_httpx_response(200, full_property_response)
    mock_inner_client = AsyncMock(spec=httpx.AsyncClient)
    mock_inner_client.get.return_value = mock_response

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_inner_client
    mock_cm.__aexit__.return_value = None

    with patch("api.index.httpx.AsyncClient", return_value=mock_cm):
        yield mock_inner_client
