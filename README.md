# NexEstimate — Zillow Estimate Agent

A production-grade Python agent with a React + TypeScript frontend that fetches the current Zillow Zestimate® for any US property address.

> **≥ 99% accuracy** — Returns the exact Zestimate currently displayed on Zillow.com, sourced directly from Zillow's property data.

## Architecture

```
React + TypeScript SPA ──▶ FastAPI (Python) ──▶ Zillow API (RapidAPI)
```

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React 19 + TypeScript + Vite | Industry-standard typed SPA with fast HMR |
| **Backend** | FastAPI + Pydantic v2 | Async Python, auto-generated API docs, typed responses |
| **HTTP Client** | httpx | Async-native, drop-in replacement for `requests` |
| **Data Source** | private-zillow (RapidAPI) | Real-time Zillow property data with Zestimate |
| **Deployment** | Vercel | Serverless Python function + static React build |

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- Node.js 18+
- RapidAPI key for [private-zillow](https://rapidapi.com/apimaker/api/private-zillow)

### Setup

```bash
# Clone and install Python deps
git clone https://github.com/YOUR_USERNAME/NexEstimate.git
cd NexEstimate
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env with your RapidAPI key

# Install frontend deps
cd frontend
npm install
cd ..
```

### Run locally

```bash
# Terminal 1: Start the backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Endpoint**: http://localhost:8000/api/estimate?address=328+26th+Avenue,+Seattle,+WA+98122

## Deploy to Vercel

1. Push to GitHub
2. Import the repo on [vercel.com](https://vercel.com)
3. Add environment variable: `RAPIDAPI_KEY` = your key
4. Deploy — Vercel handles everything via `vercel.json`

## API Response Example

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
  "last_sold_price": 959000,
  "image_url": "https://photos.zillowstatic.com/..."
}
```

## Project Structure

```
NexEstimate/
├── api/
│   └── index.py           # FastAPI serverless function (Vercel)
├── main.py                # FastAPI app (local development)
├── vercel.json            # Vercel deployment config
├── requirements.txt       # Python dependencies
├── .env                   # API keys (gitignored)
├── .gitignore
├── README.md
└── frontend/              # React + TypeScript SPA
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts     # Dev proxy to backend
    └── src/
        ├── App.tsx        # Root component
        ├── index.css      # Global styles
        ├── types/         # TypeScript interfaces
        ├── services/      # API client
        ├── hooks/         # Custom hooks
        └── components/    # UI components
```

## Tech Decisions

- **FastAPI over Flask**: Async-native, auto Swagger docs, Pydantic validation
- **httpx over requests**: Async support required for FastAPI's async endpoints
- **React + TypeScript over vanilla JS**: Typed components, better DX, interview signal
- **Vite over CRA**: CRA is deprecated, Vite is 10-20x faster
- **Vercel over Render**: Serverless = zero ops, free tier, GitHub integration

---

Built for the Nexhelm technical assessment.
