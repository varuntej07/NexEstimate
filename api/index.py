"""
NexEstimate — Zillow Estimate Agent
Vercel Serverless Function: FastAPI app served as a Python serverless function.
"""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

# Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "private-zillow.p.rapidapi.com")
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"

# Pydantic response models
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


# FastAPI app
app = FastAPI(
    title="NexEstimate",
    description="Zillow Estimate Agent — fetch Zestimates for any property address",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper: parse API response into our model
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


# API endpoint
@app.get("/api/estimate", response_model=PropertyEstimate)
async def get_estimate(
    address: str = Query(
        ...,
        min_length=5,
        description="Full US property address (e.g. '328 26th Avenue, Seattle, WA 98122')",
        examples=["328 26th Avenue, Seattle, WA 98122"],
    ),
):
    """
    Fetch the Zillow Zestimate and property details for a given US address.

    Returns curated property data including the Zestimate, rent estimate,
    property details, pricing info, and a photo.
    """
    if not RAPIDAPI_KEY:
        raise HTTPException(
            status_code=500,
            detail="RAPIDAPI_KEY not configured. Add it to your environment variables.",
        )

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.get(
                f"{RAPIDAPI_BASE}/pro/byaddress",
                headers=headers,
                params={"propertyaddress": address},
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="The Zillow API request timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach the Zillow API: {str(exc)}",
        )

    if response.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="API rate limit reached. Please wait a moment and try again.",
        )

    if response.status_code != 200:
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

    return _parse_property(data)
