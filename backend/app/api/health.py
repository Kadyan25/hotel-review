from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # database not reachable
        db_status = f"unreachable: {exc}"

    return {
        "status": "ok",
        "database": db_status,
        "llm_classification_enabled": settings.llm_configured,
        "apify_fallback_configured": settings.apify_configured,
        "scrape_endpoint_enabled": settings.enable_scrape_endpoint,
    }
