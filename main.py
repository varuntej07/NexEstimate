"""
NexEstimate — local dev server.
Manages a persistent httpx.AsyncClient via lifespan and serves the React SPA.
Business logic lives in api/core.py.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.core import ALLOWED_ORIGIN, RATE_LIMIT, TIMEOUTS, PropertyEstimate, get_estimate_handler

limiter = Limiter(key_func=get_remote_address)
http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the httpx client lifecycle."""
    global http_client
    http_client = httpx.AsyncClient(timeout=TIMEOUTS)
    yield
    await http_client.aclose()


app = FastAPI(
    title="NexEstimate",
    description="Zillow Estimate Agent — fetch Zestimates for any US property address",
    version="1.0.0",
    lifespan=lifespan,
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
        description="Full US property address (e.g. '901 8th Avenue, Seattle, WA 98104')",
        examples=["901 8th Avenue, Seattle, WA 98104"],
    ),
):
    """Fetch the Zillow Zestimate and property details for a given address."""
    if http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return await get_estimate_handler(address, http_client)


# Serve React build in production
FRONTEND_BUILD = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_BUILD.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_BUILD / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """Serve the React SPA — all non-API routes go to index.html."""
        file_path = FRONTEND_BUILD / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_BUILD / "index.html")
