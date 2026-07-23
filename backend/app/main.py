import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.insights import router as insights_router
from app.api.properties import router as properties_router
from app.api.reviews import router as reviews_router
from app.api.scrape import router as scrape_router
from app.config import get_settings
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="Azzurro Hotels Review Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Full stack trace goes to the server log; the client gets a stable,
    # non-leaky message rather than a raw traceback.
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health_router, prefix="/api")
app.include_router(properties_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(scrape_router, prefix="/api")
