# Azzurro Hotels — Review Insights Dashboard

Collects Booking.com guest reviews for four Azzurro Hotels properties (Surry Hills, Potts Point, Central Sydney, Darling Harbour) and surfaces them in an operations dashboard with topic-based insights, built for non-technical ops staff.

## Live demo

- **Dashboard:** https://hotel-review-production.up.railway.app
- **API:** https://backend-production-7450c.up.railway.app/api/health

Runs against a real Postgres instance seeded with 47 real reviews scraped from all four properties. The manual "Refresh reviews" scrape trigger is intentionally disabled on this public deployment (see "Where the scraper is allowed to run" below) — AI Insights is fully live.

## Stack

- **Backend:** Python 3.13 / FastAPI / SQLAlchemy (async) / Alembic / Postgres
- **Frontend:** Vite / React / TypeScript / Tailwind CSS / React Router / Recharts
- **Scraper:** Patchright (a Playwright fork with anti-detection patches)
- **Optional AI classification:** Claude Haiku 4.5, off by default
- **Optional scraper fallback:** Apify (`reviewly/booking-reviews-scraper`)

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
python -m patchright install chromium
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

## Running the scraper

Three ways to collect/update reviews, in increasing order of automation:

### A. CLI, one property (the reliable default)

```bash
cd backend
python scripts/run_scrape.py --property surry-hills
```

Slugs: `surry-hills`, `potts-point`, `central-sydney`, `darling-harbour`. Scoped to the last 30 days by default (`SCRAPE_LOOKBACK_DAYS`) and stops early once it hits already-seen reviews — safe to re-run anytime.

### B. CLI, all four properties in one go

```bash
python scripts/run_all_properties.py
```

Same script the daily scheduled task (below) calls. Loops all four with human-paced spacing between them, keeps going if one property fails.

### C. From the dashboard UI (manual trigger, off by default)

Every property page has a **"Refresh reviews"** button, and the overview page has **"Refresh all."** These call a backend endpoint that's **disabled unless `ENABLE_SCRAPE_ENDPOINT=true`** in `backend/.env`. Off by default deliberately — see "Where the scraper is allowed to run" below. Turn it on for local/demo use:

```
# backend/.env
ENABLE_SCRAPE_ENDPOINT=true
```

The button shows a spinner and polls a status endpoint until the run finishes (usually 1–3 minutes per property).

### Keeping data fresh automatically (daily)

`scripts/run_all_properties.py` is the entrypoint — schedule it with your OS's own scheduler, since the scraper must run from a residential machine (see below), not a cloud cron:

**Windows (Task Scheduler):**
```powershell
$action = New-ScheduledTaskAction -Execute "D:\Azuro\backend\.venv\Scripts\python.exe" -Argument "scripts\run_all_properties.py" -WorkingDirectory "D:\Azuro\backend"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "AzzurroReviewScrape" -Action $action -Trigger $trigger
```

**Linux/macOS (cron), for reference if ever run from a residential server:**
```cron
0 3 * * * cd /path/to/Azuro/backend && .venv/bin/python scripts/run_all_properties.py >> /var/log/azzurro-scrape.log 2>&1
```

Both approaches reuse the same incremental logic as the manual triggers — a daily run only picks up reviews posted since the last run, it doesn't re-fetch everything.

### Where the scraper is allowed to run

The scraper's reliability depends on running from a real residential IP, not a datacenter one (see "Review collection method" below). **It must run from your own machine, not from a cloud deployment** — this is why the manual UI trigger is gated behind an env var that stays `false` on a public Railway/cloud deployment, and why the "official" way to update data is the CLI or the gated local UI button, not something exposed by default on a public demo.

## Deployment

The live demo runs on Railway: `Postgres`, `backend` (FastAPI, Nixpacks), and `hotel-review` (frontend, Vite `preview` server) as three services in one project. To reproduce:

1. **Postgres:** provision a Railway Postgres service.
2. **Backend:** deploy `backend/` (`railway up` from that directory). Set variables: `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `ANTHROPIC_API_KEY`, `APIFY_API_TOKEN`, `ENABLE_SCRAPE_ENDPOINT=false` (**never `true`** on a public host — see above), `ALLOWED_ORIGINS=<frontend public URL>`. `backend/railway.json` runs `alembic upgrade head` before `uvicorn` on every deploy.
3. **Seed the database** (migrations create schema only, not data): point `DATABASE_URL` at Postgres's public proxy URL and run `python scripts/seed_sample_data.py` once — creates the 4 properties and loads `data/sample_reviews.json` plus keyword classification.
4. **Frontend:** deploy `frontend/` the same way, with `VITE_API_BASE_URL=<backend public URL>` set *before* building (Vite bakes it in at build time, not runtime). `frontend/railway.json` serves the build via `vite preview`.

Three real deployment bugs surfaced and got fixed here, worth knowing if you redeploy elsewhere:
- **Railway's `DATABASE_URL` has no driver suffix** (`postgresql://`, not `postgresql+asyncpg://`) — SQLAlchemy silently falls back to `psycopg2`, which isn't installed. Fixed with a Pydantic validator in `app/config.py` that normalizes the URL for every caller (app, Alembic, scripts), not just a one-off patch.
- **Vite's `preview` server rejects unrecognized `Host` headers** by default (DNS-rebinding protection) — needs `preview.allowedHosts` set in `vite.config.ts`.
- **Nixpacks defaulted to Node 18**, too old for this Vite/Rolldown toolchain (needs 20+) — pinned via `frontend/.nvmrc` and `package.json`'s `engines` field.

## Sample data

`data/sample_reviews.json` — a committed snapshot of real reviews scraped from all four properties (47 reviews as of the last export). Re-export anytime with:

```bash
python scripts/export_sample_data.py
```

## Architecture overview

```
Azuro/
├── docker-compose.yml       # local Postgres
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers: properties, reviews, insights, scrape, health
│   │   ├── models/           # SQLAlchemy: Property, Review, ReviewTopic, ScrapeRun, LlmInsightRun
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── services/         # scrape_service.py -- shared by CLI, cron, and the API endpoint
│   │   ├── scraper/          # booking_scraper.py, parser.py, human.py, apify_fallback.py
│   │   ├── classification/   # keyword lexicon/classifier + Claude Haiku client
│   │   └── db/                # session, base
│   ├── scripts/               # run_scrape.py, run_all_properties.py, export_sample_data.py, classify_keyword.py, seed_sample_data.py
│   └── alembic/                # migrations
├── frontend/
│   └── src/
│       ├── pages/              # OverviewPage (collective), PropertyPage (per-hotel)
│       ├── components/         # dashboard components + components/ui (button/select/date-picker)
│       └── api/                 # typed fetch wrappers
└── data/sample_reviews.json
```

**Data flow:** scraper (or Apify fallback) → Postgres (`reviews`, `scrape_runs`) → keyword classifier populates `review_topics` (source=`keyword`) → optional Claude Haiku fallback adds more (`source=`llm`) for text the keyword pass missed → FastAPI aggregation endpoints → React dashboard.

**Dashboard structure:** `/` is the collective overview (KPIs across all properties, an aggregate trend graph, property selector cards, aggregate topic insights). `/properties/:slug` is one hotel's own page (its KPIs, its trend graph, its topic breakdown, its full paginated review feed with date/topic filters, its own scrape and AI-insights triggers).

## Review collection method

1. **Primary — Patchright (self-hosted, free), run locally.** Booking.com runs Akamai Bot Manager; research and live testing both point to residential IPs faring meaningfully better than datacenter ones, so this runs from your own machine, not a cloud box.
2. **The actual fix that mattered:** headless Chromium self-identifies as `HeadlessChrome` in its `User-Agent` header. Live testing confirmed Booking's reviews GraphQL endpoint (`ReviewList`) rejects that specific string with a structured `400 Request not supported` — not sophisticated fingerprinting, a simple check, and one Patchright's CDP-level patches don't cover on their own. Fixed by overriding the context's `user_agent` to the same Chromium build with "Headless" stripped.
3. **Human-mimicking pacing** (`app/scraper/human.py`): every click moves through randomized curved waypoints instead of an instant jump, every wait is randomized (not fixed), an occasional longer "reading pause" breaks up the cadence every ~8 pages, and a session pacing cap stops a run before it turns into a marathon.
4. **Recent-window scope, not full history:** each run stops at `SCRAPE_LOOKBACK_DAYS` (30 by default) — Surry Hills alone has 220 pages / ~2,200 reviews of history; scraping all of it isn't the goal for an operational dashboard focused on recent sentiment. Full historical backfill is available (`SCRAPE_FULL_HISTORY=true`) as a deliberate, separate one-time run.
5. **Dedup:** Booking's DOM exposes no review ID anywhere, confirmed by inspection — the dedup key is a SHA-256 hash of `(reviewer_name, review_date, positive_text, negative_text)`.
6. **Fallback — Apify** (`reviewly/booking-reviews-scraper`), triggered automatically only if the primary scraper gets blocked. Cost-capped (`MAX_REVIEWS_PER_PROPERTY_APIFY`), and live-tested to confirm it actually works and to map its (different, and less complete) schema onto the same internal shape as the primary scraper.
7. **Sentiment signal:** Booking.com natively splits reviews into liked/disliked text blocks — used directly as the sentiment signal for keyword classification, rather than inferring sentiment from scratch.

### ToS

Booking.com's terms explicitly prohibit automated scraping without prior written permission. This project is built for educational/trial-evaluation purposes only, at low request volume, with no attempt to evade detection at scale.

## Review insights methodology

1. **Keyword pass (default, always on, free):** a curated phrase lexicon per topic (`app/classification/keyword_lexicon.py`), matched against `positive_text`/`negative_text` independently — sentiment comes from which field matched, not a separate sentiment model. Every topic (cleanliness, check-in, staff, noise, facilities, location, room condition, value for money) gets a flat confidence score, since a keyword match is binary, not graded. This is the always-on path — classification works fully with zero AI calls.
2. **LLM fallback (Claude Haiku 4.5, off by default):** only for reviews where the keyword pass found nothing on non-trivial text — e.g. non-English reviews the English-only lexicon misses. Every classification row records its `source` (`keyword`/`llm`) so the methodology is auditable, not just asserted.
3. **Both panels show positive and negative breakdowns per topic**, not negative-only — a topic guests only ever praise (e.g. Location) is as much an insight as one they complain about, and sorting is by total mentions so it isn't buried.
4. **"Get AI Insights" runs at most once per calendar day per scope** (collective or per-property), tracked in an `llm_insight_runs` table — re-running against the same reviews can yield different results from the model on identical input, and there's no new information to extract until the next scrape anyway. The button shows "Generated today" and a persisted "Last generated" timestamp once used; results survive a page reload.
5. **Manager's Briefing — the part keyword-matching structurally can't do.** Beyond re-tagging reviews (which keyword-matching already covers), each AI run also generates a short 2-4 sentence synthesis: the standout recurring issue plus one concrete, actionable suggestion (e.g. *"Room condition is the most significant issue, with N negative mentions... prioritize a systematic room audit..."*). It's grounded in the real aggregated topic counts and verbatim negative-review excerpts fed into the prompt — not free-associated — so it can't invent a statistic that doesn't match the bars next to it. Hard-capped (`MAX_LLM_CLASSIFICATIONS`, default 50 reviews/run) so a run costs a few cents at most.

## Known limitations and assumptions

- **The manual scrape trigger is enabled on the live Railway demo**, unlike the safer default described above — the build installs Chromium and, live-tested, the primary Patchright scraper does run successfully there (confirmed server-side: real navigation, `source=patchright`, completed in ~18s). What's **not fully verified is the frontend's live status display** on that deployment — during testing it showed a stale "No scrape has run yet." message after a run that had actually already completed successfully (confirmed independently via the API and the `scrape_runs` table). The scrape itself works; treat the UI's real-time status text on the Railway demo with some caution until this is root-caused, and prefer running locally (`scripts/run_scrape.py`) if you need to trust the on-screen result immediately.
- **Scraping reliability is probabilistic, not guaranteed.** The human-pacing and UA fixes measurably worked in testing (100% success rate across all 4 properties during development), but Booking.com can change its detection at any time.
- **Reviewer country has a rare render-timing bug:** the avatar block briefly shows a placeholder ("7 reviews", "Active since 2018") before its flag/country element finishes loading. Confirmed live that affected reviewers have real countries in the DOM moments later. Mitigated by rejecting known placeholder patterns and storing `null` rather than wrong data — a handful of reviews have a `null` country as a result, better than a wrong one.
- **One unresolved parsing edge case:** a single review has `reviewer_name="A"` with a stray value in the country field, not matching the placeholder-pattern fix above. Left as-is rather than guessing at a fix without more examples to pattern-match against.
- **Apify fallback is lower fidelity than the primary scraper** — its schema has no reviewer country and no length-of-stay at all. A live cross-check also found the same review scored differently between the two sources (rating 3 direct vs. 2 via Apify) — a real, documented discrepancy, not swept under the rug.
- **Property thumbnails are hotlinked**, not downloaded/rehosted, directly from Booking.com's own CDN (`cf.bstatic.com`) — these are the properties' own photos. The URLs include a signed token that may expire; the UI falls back to an icon badge if an image fails to load.
- **Keyword classification is English-only** by construction — the LLM fallback exists specifically to cover what it misses (see the Italian-language test case that surfaced a real markdown-fence parsing bug, since fixed, in `app/classification/llm_client.py`).
- **Weekly comparison uses rolling 7-day windows** (today − 7 days vs. the 7 days before that), not calendar weeks — matches how ops staff actually think about "this week vs last week" day-to-day.
- **`stay_date` is approximated to the 1st of the month** — Booking only ever shows month + year for the stay, never an exact day.

## Logs

Backend logs go to stdout with `%(asctime)s %(levelname)s %(name)s: %(message)s` formatting (`app/logging_config.py`) — when running `uvicorn --reload`, they print directly to the terminal. Unhandled API errors are logged with full stack traces server-side and return a generic `{"detail": "Internal server error"}` to the client, so nothing sensitive leaks into a response. Scraper runs additionally log to the `scrape_runs` table (status, error message, timestamps) — check there for scrape history beyond what's in the terminal.

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. `ANTHROPIC_API_KEY`, `APIFY_API_TOKEN`, and `ENABLE_SCRAPE_ENDPOINT` are all optional/off-by-default — the app runs fully without them (keyword-only classification, Playwright-only scraping, CLI-only updates).
