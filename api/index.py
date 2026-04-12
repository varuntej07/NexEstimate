"""
NexEstimate — Vercel serverless function.
Creates a fresh httpx.AsyncClient per invocation (no lifespan support).
Business logic lives in api/core.py.
"""

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .core import ALLOWED_ORIGIN, RATE_LIMIT, TIMEOUTS, PropertyEstimate, get_estimate_handler

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="NexEstimate",
    description="Zillow Estimate Agent — fetch Zestimates for any US property address",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/estimate", response_model=PropertyEstimate)
@limiter.limit(RATE_LIMIT)
async def get_estimate(
    request: Request,
    address: str = Query(
        ...,
        min_length=5,
        max_length=100,
        description="Full US property address (e.g. '328 26th Avenue, Seattle, WA 98122')",
        examples=["328 26th Avenue, Seattle, WA 98122"],
    ),
):
    """Fetch the Zillow Zestimate and property details for a given US address."""
    async with httpx.AsyncClient(timeout=TIMEOUTS) as client:
        return await get_estimate_handler(address, client)
