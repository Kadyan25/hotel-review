# Azzurro Hotels — Review Insights Dashboard

Collects Booking.com guest reviews for four Azzurro Hotels properties and surfaces them in an operations dashboard with topic-based insights.

**Status: Phase 0 (scaffolding) complete.** Backend + frontend run locally and talk to each other. Scraper, API, dashboard, and insights land in subsequent phases — see `build-plan.md` for the full roadmap (not committed to the repo; local planning doc).

## Stack

- **Backend:** Python 3.13 / FastAPI / SQLAlchemy (async) / Alembic / Postgres
- **Frontend:** Vite / React / TypeScript / Tailwind CSS
- **Scraper:** Patchright (Playwright fork with anti-detection patches) — added in Phase 1
- **Optional AI classification:** Claude Haiku 4.5, off by default

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for local Postgres)

### 1. Database

```bash
docker compose up -d
```

Starts a dedicated Postgres container on port `5437`.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\Activate.ps1 for PowerShell
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/api/health`

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Opens at `http://localhost:5173`.

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. `ANTHROPIC_API_KEY` and `APIFY_API_TOKEN` are both optional — the app runs fully without them (keyword-only classification, Playwright-only scraping).

## Sample data

`data/sample_reviews.json` will contain a committed snapshot of real scraped reviews (added in Phase 2).

## Known limitations (so far)

- Scraping Booking.com without permission likely conflicts with their Terms of Service — this project is built for educational/trial-evaluation purposes only, at low request volume. Full discussion lands in this README once the scraper is built (Phase 1–2).
- This section will be filled in progressively as each phase completes, not written all at once at the end.
