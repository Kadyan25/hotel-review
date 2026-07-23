from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db
from app.models import Property, ScrapeRun
from app.scraper.properties import PROPERTIES
from app.services.scrape_service import scrape_all_properties_task, scrape_single_property_task

router = APIRouter()


def _require_scrape_enabled(settings: Settings) -> None:
    if not settings.enable_scrape_endpoint:
        raise HTTPException(
            status_code=403,
            detail="Manual scrape trigger is disabled on this deployment (ENABLE_SCRAPE_ENDPOINT=false). "
            "Run scripts/run_scrape.py locally instead -- see README.",
        )


@router.post("/properties/{property_id}/scrape")
async def trigger_property_scrape(
    property_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    _require_scrape_enabled(settings)

    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="property not found")

    prop_def = next((p for p in PROPERTIES if p.slug == prop.slug), None)
    if prop_def is None:
        raise HTTPException(status_code=400, detail=f"no scraper definition for slug '{prop.slug}'")

    already_running = await db.execute(
        select(ScrapeRun).where(ScrapeRun.property_id == property_id, ScrapeRun.status == "running")
    )
    if already_running.scalars().first() is not None:
        raise HTTPException(status_code=409, detail="a scrape is already running for this property")

    background_tasks.add_task(scrape_single_property_task, prop_def)
    return {"status": "started", "property": prop.slug}


@router.get("/properties/{property_id}/scrape-status")
async def property_scrape_status(property_id: int, db: AsyncSession = Depends(get_db)):
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="property not found")

    result = await db.execute(
        select(ScrapeRun).where(ScrapeRun.property_id == property_id).order_by(ScrapeRun.started_at.desc()).limit(1)
    )
    run = result.scalars().first()
    if run is None:
        return {"status": "never_run"}
    return {
        "status": run.status,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "reviews_new": run.reviews_new,
        "error": run.error_message,
    }


@router.post("/scrape-all")
async def trigger_scrape_all(background_tasks: BackgroundTasks, settings: Settings = Depends(get_settings)):
    _require_scrape_enabled(settings)
    background_tasks.add_task(scrape_all_properties_task)
    return {"status": "started", "properties": [p.slug for p in PROPERTIES]}


@router.get("/scrape-all-status")
async def scrape_all_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScrapeRun).where(ScrapeRun.status == "running"))
    running = result.scalars().all()
    return {"running": len(running) > 0, "running_property_ids": [r.property_id for r in running]}
