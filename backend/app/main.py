from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.insights import router as insights_router
from app.api.properties import router as properties_router
from app.api.reviews import router as reviews_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Azzurro Hotels Review Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(properties_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
