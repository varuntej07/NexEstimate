"""
NexEstimate — shared business logic.
Imported by both main.py (local dev) and api/index.py (Vercel serverless).
"""

import asyncio
import hashlib
import logging
import os
import random
import re
import time
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic import BaseModel, Field

load_dotenv()
logger = logging.getLogger(__name__)

# Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "private-zillow.p.rapidapi.com")
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"

# Lock CORS to deployed origin in production; wildcard falls back for local dev.
# Set ALLOWED_ORIGIN=https://your-app.vercel.app in Vercel environment variables.
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

# Per-client rate limit: 15 lookups per 10 minutes.
RATE_LIMIT = "15/10 minutes"

# Granular per-phase timeouts.
# Total worst-case: connect(5) + read(20) = 25s which leaves 5s under Vercel's 30s limit.
TIMEOUTS = httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=2.0)

# Retry configuration: retry on transient 5xx responses and ConnectTimeout/network errors only.
# Do not retry ReadTimeout (time budget spent) or 429 (hammering rate-limit is worse).
_RETRYABLE_STATUS = frozenset({500, 502, 503, 504})
_MAX_RETRIES = 2          # up to 3 total attempts
_BACKOFF_BASE = 0.5       # seconds: 0.5s -> 1.0s (+jitter) between retries

_ADDRESS_MAX_LEN = 100      # Max length of address
_ADDRESS_RE = re.compile(r"^\d+\s+\w", re.ASCII)      # Must start with a house number followed by a street name character
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")      # Block newlines and control characters


def _hash_addr(address: str) -> str:
    """One-way hash of address for safe log correlation without logging PII."""
    return hashlib.sha256(address.encode()).hexdigest()[:12]


class ZestimateRange(BaseModel):
    low_percent: Optional[str] = None
    high_percent: Optional[str] = None


class PropertyEstimate(BaseModel):
    """Curated property data returned to the frontend."""

    # Core estimate
    zestimate: Optional[int] = Field(None, description="Zillow Zestimate value")
    zestimate_range: Optional[ZestimateRange] = None
    rent_zestimate: Optional[int] = Field(None, description="Monthly rent Zestimate")

    # Address
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    full_address: Optional[str] = None
    county: Optional[str] = None

    # Property details
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    living_area: Optional[int] = Field(None, description="Living area in sqft")
    lot_size: Optional[float] = Field(None, description="Lot size in sqft")
    year_built: Optional[int] = None
    home_type: Optional[str] = None
    home_status: Optional[str] = None
    property_tax_rate: Optional[float] = None

    # Pricing
    price: Optional[int] = Field(None, description="Current list price")
    last_sold_price: Optional[int] = None
    days_on_zillow: Optional[int] = None

    # Media
    image_url: Optional[str] = None
    street_view_url: Optional[str] = None
    zillow_url: Optional[str] = None

    # Description
    description: Optional[str] = None

    # Metadata
    zpid: Optional[int] = Field(None, description="Zillow Property ID")
    page_view_count: Optional[int] = None
    favorite_count: Optional[int] = None


async def _fetch_with_retry(client: httpx.AsyncClient, address: str) -> httpx.Response:
    """
    GET /pro/byaddress with exponential backoff + jitter on transient failures.

    ConnectTimeout and network errors are retried; ReadTimeout is not (budget spent).
    Returns the httpx.Response for the caller to inspect status and classify errors.
    """
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }
    url = f"{RAPIDAPI_BASE}/pro/byaddress"
    params = {"propertyaddress": address}
    addr_id = _hash_addr(address)

    last_response: Optional[httpx.Response] = None

    for attempt in range(_MAX_RETRIES + 1):
        if attempt > 0:
            jitter = random.uniform(0.0, 0.3)
            delay = _BACKOFF_BASE * (2 ** (attempt - 1)) + jitter
            logger.warning(
                "zillow_retry addr_id=%s attempt=%d delay_s=%.2f",
                addr_id, attempt, delay,
            )
            await asyncio.sleep(delay)

        t0 = time.monotonic()
        try:
            response = await client.get(url, headers=headers, params=params)
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.info(
                "zillow_response addr_id=%s attempt=%d status=%d latency_ms=%d",
                addr_id, attempt, response.status_code, latency_ms,
            )
            if response.status_code not in _RETRYABLE_STATUS:
                return response  # 200, 4xx - return immediately for caller to classify
            last_response = response  # 5xx - record and retry

        except httpx.ConnectTimeout:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning(
                "zillow_connect_timeout addr_id=%s attempt=%d latency_ms=%d",
                addr_id, attempt, latency_ms,
            )
            # Server unreachable - safe to retry

        except httpx.ReadTimeout:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning(
                "zillow_read_timeout addr_id=%s attempt=%d latency_ms=%d",
                addr_id, attempt, latency_ms,
            )
            # Time budget spent waiting for response - do not retry
            raise HTTPException(
                status_code=504,
                detail="The Zillow did not respond in time. Please try again.",
            )

        except httpx.TimeoutException:
            # Catch-all for any remaining timeout subclass - do not retry
            raise HTTPException(
                status_code=504,
                detail="The Zillow request timed out. Please try again.",
            )

        except httpx.RequestError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning(
                "zillow_network_error addr_id=%s attempt=%d error=%s latency_ms=%d",
                addr_id, attempt, type(exc).__name__, latency_ms,
            )
            # DNS/socket error — retry

    if last_response is not None:
        return last_response  # last 5xx after all retries — let caller handle it
    raise HTTPException(
        status_code=502,
        detail=f"Failed to reach Zillow after {_MAX_RETRIES + 1} attempts.",
    )


def _parse_property(data: dict) -> PropertyEstimate:
    """Extract curated fields from the raw RapidAPI response."""
    pd = data.get("propertyDetails", {})

    street = pd.get("streetAddress", "")
    city = pd.get("city", "")
    state = pd.get("state", "")
    zipcode = pd.get("zipcode", "")
    full_address = ", ".join(filter(None, [street, city, f"{state} {zipcode}".strip()]))

    zillow_url = data.get("zillowURL") or ""
    if not zillow_url and pd.get("hdpUrl"):
        zillow_url = f"https://www.zillow.com{pd['hdpUrl']}"

    return PropertyEstimate(
        zestimate=pd.get("zestimate"),
        zestimate_range=ZestimateRange(
            low_percent=pd.get("zestimateLowPercent"),
            high_percent=pd.get("zestimateHighPercent"),
        ),
        rent_zestimate=pd.get("rentZestimate"),
        street_address=street or None,
        city=city or None,
        state=state or None,
        zipcode=zipcode or None,
        full_address=full_address or None,
        county=pd.get("county"),
        bedrooms=pd.get("bedrooms"),
        bathrooms=pd.get("bathrooms"),
        living_area=pd.get("livingArea"),
        lot_size=pd.get("lotSize"),
        year_built=pd.get("yearBuilt"),
        home_type=pd.get("homeType"),
        home_status=pd.get("homeStatus"),
        property_tax_rate=pd.get("propertyTaxRate"),
        price=pd.get("price"),
        last_sold_price=pd.get("lastSoldPrice"),
        days_on_zillow=pd.get("daysOnZillow"),
        image_url=pd.get("hiResImageLink") or pd.get("desktopWebHdpImageLink"),
        street_view_url=pd.get("streetViewImageUrl"),
        zillow_url=zillow_url or None,
        description=pd.get("description"),
        zpid=pd.get("zpid"),
        page_view_count=pd.get("pageViewCount"),
        favorite_count=pd.get("favoriteCount"),
    )


async def get_estimate_handler(address: str, client: httpx.AsyncClient) -> PropertyEstimate:
    """
    Core estimate logic: called by both runtimes with their own client.

    Validates input, fetches from the Zillow API with retry, classifies errors,
    and parses the response into a PropertyEstimate.
    """
    if not RAPIDAPI_KEY:
        raise HTTPException(
            status_code=500,
            detail="RAPIDAPI_KEY not configured. Add it to your environment variables.",
        )

    # Input validation: fail fast before spending API quota
    if len(address) > _ADDRESS_MAX_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"Address must be {_ADDRESS_MAX_LEN} characters or fewer.",
        )
    if _CONTROL_CHARS_RE.search(address):
        raise HTTPException(status_code=422, detail="Address contains invalid characters.")
    if not _ADDRESS_RE.match(address):
        raise HTTPException(
            status_code=422,
            detail="Address must start with a street number (e.g. '328 26th Ave, Seattle, WA 98122').",
        )

    addr_id = _hash_addr(address)
    t0 = time.monotonic()
    logger.info("estimate_start addr_id=%s", addr_id)

    response = await _fetch_with_retry(client, address)
    total_ms = int((time.monotonic() - t0) * 1000)

    if response.status_code == 401:
        logger.error("zillow_auth_error addr_id=%s", addr_id)
        raise HTTPException(
            status_code=502,
            detail="Zillow API authentication failed. Check the RAPIDAPI_KEY.",
        )
    if response.status_code == 403:
        logger.error("zillow_forbidden addr_id=%s", addr_id)
        raise HTTPException(
            status_code=502,
            detail="Zillow API access forbidden. Check API key permissions and subscription.",
        )
    if response.status_code == 429:
        logger.warning("zillow_rate_limited addr_id=%s", addr_id)
        raise HTTPException(
            status_code=429,
            detail="API rate limit reached. Please wait a moment and try again.",
        )
    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="No property found for the given address. Check the address and try again.",
        )
    if response.status_code != 200:
        logger.error(
            "zillow_unexpected_status addr_id=%s status=%d total_ms=%d",
            addr_id, response.status_code, total_ms,
        )
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Zillow API error (HTTP {response.status_code})",
        )

    data = response.json()

    if not data.get("propertyDetails"):
        raise HTTPException(
            status_code=404,
            detail="No property found for the given address. Check the address and try again.",
        )

    logger.info("estimate_success addr_id=%s total_ms=%d", addr_id, total_ms)
    return _parse_property(data)
