# NexEstimate — Zillow Estimate Agent

Fetches the current Zillow Zestimate® for any US property address. Enter an address, get back the exact value Zillow shows — no scraping, no approximations.

## How it works

```
React SPA  →  FastAPI (Python)  →  Zillow API via RapidAPI
```

The backend hits the `private-zillow` RapidAPI endpoint and returns structured property data including the Zestimate, rent estimate, and listing details. The frontend is just a clean interface on top of that.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19 + TypeScript + Vite |
| Backend | FastAPI + Pydantic v2 + httpx |
| Data | private-zillow (RapidAPI) |
| Deploy | Vercel (serverless Python + static) |

## Local Setup

**Prerequisites:** Python 3.11+, Node 18+, RapidAPI key for [private-zillow](https://rapidapi.com/apimaker/api/private-zillow)

```bash
git clone https://github.com/YOUR_USERNAME/NexEstimate.git
cd NexEstimate
pip install -r requirements.txt
cp .env.example .env
# add your RAPIDAPI_KEY to .env

cd frontend && npm install && cd ..
```

```bash
# Terminal 1
uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

- Frontend: http://localhost:5173
- Swagger docs: http://localhost:8000/docs
- Raw API: http://localhost:8000/api/estimate?address=328+26th+Avenue,+Seattle,+WA+98122

## Deploy to Vercel

Push to GitHub, import on Vercel, set `RAPIDAPI_KEY` as an environment variable. The `vercel.json` handles the rest.

## Example Response

```json
{
  "zestimate": 1158800,
  "zestimate_range": { "low_percent": "5", "high_percent": "5" },
  "rent_zestimate": 4100,
  "full_address": "328 26th Avenue, Seattle, WA 98122",
  "bedrooms": 5,
  "bathrooms": 2.0,
  "living_area": 2680,
  "year_built": 1912,
  "home_type": "SINGLE_FAMILY",
  "price": 1199000,
  "last_sold_price": 959000
}
```

## Project Structure

```
NexEstimate/
├── api/core.py         # Shared business logic (used by both runtimes)
├── api/index.py        # FastAPI serverless function (Vercel)
├── main.py             # FastAPI app for local dev
├── vercel.json
├── requirements.txt
└── frontend/
    └── src/
        ├── App.tsx
        ├── types/
        ├── services/
        ├── hooks/
        └── components/
```

## Production Hardening

The backend includes:

- **Rate limiting** — 15 requests per 10 minutes per IP (`slowapi`)
- **Structured logging** — request latency, retry attempts, errors; address is hashed (never logged as plain text)
- **Granular timeouts** — connect/read/write split to fit Vercel's 30s limit
- **Input validation** — address must start with a street number, max 100 chars, no control characters
- **CORS** — locked to deployed origin via `ALLOWED_ORIGIN` env var (wildcard in local dev)
- **Error classification** — 401, 403, 429, 404, 5xx each get distinct messages

## Known Limitations

- No authentication or API key protection on the endpoint
- No caching - every request hits RapidAPI
- Rate limiting is per-lambda-instance on Vercel (not a hard global cap - should use Redis/Upstash for that)

---

Built for the Nexhelm technical assessment.
