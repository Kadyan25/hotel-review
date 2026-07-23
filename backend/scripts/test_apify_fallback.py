"""Manual verification tool for the Apify fallback path.

Usage: python scripts/test_apify_fallback.py [--property surry-hills] [--max-reviews 10]

Not part of the normal scrape pipeline -- run this by hand when you want to
confirm the Apify actor/token/schema still work, without touching the
Playwright path or spending more than a few cents.
"""

import argparse
import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.scraper.apify_fallback import fetch_reviews_via_apify
from app.scraper.properties import PROPERTIES

OUT_DIR = Path(r"C:\Users\kadia\AppData\Local\Temp\claude\D--Azuro\9c3d57d2-5b46-4847-b2f5-8741c32a86c0\scratchpad")
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--property", default="surry-hills")
    parser.add_argument("--max-reviews", type=int, default=10)
    args = parser.parse_args()

    prop_def = next(p for p in PROPERTIES if p.slug == args.property)
    settings = get_settings()

    if not settings.apify_configured:
        raise SystemExit("APIFY_API_TOKEN not set in backend/.env -- nothing to test")

    cutoff_date = date.today() - timedelta(days=settings.scrape_lookback_days)
    items = await fetch_reviews_via_apify(
        prop_def.booking_url, max_reviews=args.max_reviews, settings=settings, cutoff_date=cutoff_date
    )

    (OUT_DIR / "apify_response.json").write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")
    print(f"\n--- got {len(items)} top-level items, saved full response to apify_response.json ---")

    if items and "reviews" in items[0]:
        reviews = items[0]["reviews"]
        print(f"reviews array length: {len(reviews)}")
        if reviews:
            print("first review full object:")
            print(json.dumps(reviews[0], indent=2, default=str))


asyncio.run(main())
