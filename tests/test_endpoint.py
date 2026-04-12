"""
Integration tests for GET /api/estimate.

Tests the full request/response cycle through the FastAPI app. Outbound httpx calls are intercepted 
via the mock_rapidapi fixture in conftest.py, so no real network traffic is generated.

Covers:
  - 200 with valid address and well-formed upstream response
  - Response schema correctness (field values, types)
  - Missing RAPIDAPI_KEY -> HTTP 500
  - Upstream 429 (rate limit) -> HTTP 429 propagated to client
  - Upstream 404 (address not found) -> HTTP 404 propagated to client
  - Upstream 200 but propertyDetails absent -> HTTP 404
  - Upstream 200 with null zestimate -> HTTP 200, zestimate field is null
  - Address shorter than 5 characters -> HTTP 422 (FastAPI input validation)
"""

from unittest.mock import MagicMock

import httpx


def make_httpx_response(status_code: int, json_body: dict | None = None) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_body or {}
    return response


ESTIMATE_URL = "/api/estimate"


class TestSuccessfulRequest:

    async def test_returns_200_for_valid_address(self, async_client, mock_rapidapi):
        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )
        assert response.status_code == 200

    async def test_response_contains_zestimate(self, async_client, mock_rapidapi):
        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )
        assert response.json()["zestimate"] == 850000

    async def test_response_contains_zpid(self, async_client, mock_rapidapi):
        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )
        assert response.json()["zpid"] == 12345678

    async def test_response_contains_zillow_url(self, async_client, mock_rapidapi):
        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )
        assert response.json()["zillow_url"] == "https://www.zillow.com/homedetails/12345678_zpid/"

    async def test_response_contains_full_address(self, async_client, mock_rapidapi):
        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )
        assert response.json()["full_address"] == "328 26th Avenue, Seattle, WA 98122"

    async def test_upstream_called_with_correct_address(self, async_client, mock_rapidapi, address):
        await async_client.get(ESTIMATE_URL, params={"address": address})

        mock_rapidapi.get.assert_called_once()
        _, kwargs = mock_rapidapi.get.call_args
        assert kwargs["params"]["propertyaddress"] == address

    async def test_upstream_called_with_rapidapi_headers(self, async_client, mock_rapidapi, address):
        await async_client.get(ESTIMATE_URL, params={"address": address})

        _, kwargs = mock_rapidapi.get.call_args
        assert "x-rapidapi-key" in kwargs["headers"]
        assert kwargs["headers"]["x-rapidapi-key"] == "test-key-12345"


class TestNullZestimate:
    """A null Zestimate is valid — Zillow omits it for some property types."""

    async def test_null_zestimate_returns_200(self, async_client, mock_rapidapi, full_property_response):
        full_property_response["propertyDetails"]["zestimate"] = None
        mock_rapidapi.get.return_value = make_httpx_response(200, full_property_response)

        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )

        assert response.status_code == 200
        assert response.json()["zestimate"] is None


class TestMissingApiKey:

    async def test_missing_key_returns_500(self, async_client, monkeypatch):
        monkeypatch.setattr("api.core.RAPIDAPI_KEY", "")
        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )
        assert response.status_code == 500
        assert "RAPIDAPI_KEY" in response.json()["detail"]


class TestUpstreamErrorPropagation:
    """Upstream error codes must be surfaced to the client unchanged."""

    async def test_upstream_429_returns_429(self, async_client, mock_rapidapi):
        mock_rapidapi.get.return_value = make_httpx_response(429)

        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )

        assert response.status_code == 429

    async def test_upstream_404_returns_404(self, async_client, mock_rapidapi):
        """
        A 404 from Zillow means the address is not in their database.
        This is a correct answer, not an availability failure.
        """
        mock_rapidapi.get.return_value = make_httpx_response(404)

        response = await async_client.get(
            ESTIMATE_URL, params={"address": "1 Nonexistent Street, Nowhere, ZZ 00000"}
        )

        assert response.status_code == 404

    async def test_missing_property_details_returns_404(self, async_client, mock_rapidapi):
        """
        Upstream returns 200 but propertyDetails is absent — the address could
        not be resolved. Treated as not found, not as a server error.
        """
        mock_rapidapi.get.return_value = make_httpx_response(200, {"someOtherKey": {}})

        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )

        assert response.status_code == 404

    async def test_empty_property_details_returns_404(self, async_client, mock_rapidapi):
        mock_rapidapi.get.return_value = make_httpx_response(200, {"propertyDetails": None})

        response = await async_client.get(
            ESTIMATE_URL, params={"address": "328 26th Avenue, Seattle, WA 98122"}
        )

        assert response.status_code == 404


class TestInputValidation:

    async def test_address_below_min_length_returns_422(self, async_client):
        """FastAPI validates the address query param before the handler runs."""
        response = await async_client.get(ESTIMATE_URL, params={"address": "123"})
        assert response.status_code == 422

    async def test_missing_address_param_returns_422(self, async_client):
        response = await async_client.get(ESTIMATE_URL)
        assert response.status_code == 422
