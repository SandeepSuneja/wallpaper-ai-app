from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.wallpapers import router as wallpapers_router
from app.services.generator import get_generator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("wallcraft")

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.preload_model and not settings.mock_generation:
        logger.info("Preloading FLUX.2-klein-base-4B...")
        try:
            get_generator(settings).ensure_loaded()
            logger.info("Model preload complete.")
        except Exception:  # noqa: BLE001
            logger.exception("Model preload failed; API will retry on first generate request.")
    yield


app = FastAPI(
    title="Wallcraft API",
    description="High-quality desktop wallpaper generation with FLUX.2-klein-base-4B",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in settings.cors_origin_list else settings.cors_origin_list,
    allow_credentials="*" not in settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallpapers_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "wallcraft-api", "docs": "/docs", "model": settings.model_id}
