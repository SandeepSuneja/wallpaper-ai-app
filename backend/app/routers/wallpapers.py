from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import get_settings
from app.schemas.generation import (
    GalleryResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    Orientation,
    PresetsResponse,
    PublishRequest,
    PublishResponse,
)
from app.services.catalog import get_catalog
from app.services.generator import DESKTOP_PRESETS, cuda_available, get_generator, gpu_info

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    generator = get_generator(settings)
    name, vram = gpu_info()
    return HealthResponse(
        status="ok",
        model_id=settings.model_id,
        device=settings.device,
        model_loaded=generator.model_loaded,
        mock_generation=settings.mock_generation,
        cuda_available=cuda_available(),
        gpu_name=name,
        vram_total_gb=vram,
    )


@router.get("/presets", response_model=PresetsResponse)
def presets(orientation: Orientation | None = Query(default=None)) -> PresetsResponse:
    items = DESKTOP_PRESETS
    if orientation:
        items = [preset for preset in DESKTOP_PRESETS if preset.orientation == orientation]
    return PresetsResponse(presets=items)


@router.get("/gallery", response_model=GalleryResponse)
def gallery(orientation: Orientation | None = Query(default=None)) -> GalleryResponse:
    return GalleryResponse(items=get_catalog().list_published(orientation=orientation))


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    settings = get_settings()
    generator = get_generator(settings)

    try:
        result = generator.generate(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface model errors to client
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc

    return GenerateResponse(
        id=result.id,
        prompt=result.prompt,
        width=result.width,
        height=result.height,
        orientation=result.orientation,  # type: ignore[arg-type]
        seed=result.seed,
        steps=result.steps,
        guidance_scale=result.guidance_scale,
        model_id=result.model_id,
        image_url=f"/api/images/{result.id}",
        mock=result.mock,
        published=result.published,
        render_width=result.render_width,
        render_height=result.render_height,
    )


@router.post("/images/{image_id}/publish", response_model=PublishResponse)
def publish_image(image_id: str, body: PublishRequest) -> PublishResponse:
    settings = get_settings()
    if not image_id.isalnum() or len(image_id) != 32:
        raise HTTPException(status_code=400, detail="Invalid image id.")

    path = settings.output_dir / f"{image_id}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found.")

    catalog = get_catalog()
    catalog.publish(
        image_id=image_id,
        prompt=body.prompt,
        width=body.width,
        height=body.height,
        orientation=body.orientation,
        seed=body.seed,
        steps=body.steps,
        guidance_scale=body.guidance_scale,
        model_id=settings.model_id,
    )
    return PublishResponse(id=image_id, published=True, image_url=f"/api/images/{image_id}")


@router.get("/images/{image_id}")
def get_image(image_id: str) -> FileResponse:
    settings = get_settings()
    if not image_id.isalnum() or len(image_id) != 32:
        raise HTTPException(status_code=400, detail="Invalid image id.")

    path = settings.output_dir / f"{image_id}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found.")

    return FileResponse(path, media_type="image/png", filename=f"wallpaper-{image_id}.png")
