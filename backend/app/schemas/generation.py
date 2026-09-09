from typing import Literal

from pydantic import BaseModel, Field


Orientation = Literal["landscape", "portrait"]

DesktopPresetId = Literal[
    "fhd_16_9",
    "qhd_16_9",
    "uhd_16_9",
    "ultrawide_21_9",
    "phone_fhd_9_16",
    "phone_qhd_9_16",
    "tablet_10_16",
    "custom",
]


class DesktopPreset(BaseModel):
    id: DesktopPresetId
    label: str
    width: int
    height: int
    aspect: str
    orientation: Orientation
    steps: int
    guidance_scale: float


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)
    orientation: Orientation = "landscape"
    preset: DesktopPresetId = "fhd_16_9"
    width: int | None = Field(default=None, ge=512, le=3840)
    height: int | None = Field(default=None, ge=512, le=3840)
    # Optional overrides — clients normally omit these; server fills from preset.
    seed: int | None = Field(default=None, ge=0, le=2_147_483_647)
    steps: int | None = Field(default=None, ge=8, le=50)
    guidance_scale: float | None = Field(default=None, ge=1.0, le=10.0)
    publish: bool = False


class GenerateResponse(BaseModel):
    id: str
    prompt: str
    width: int
    height: int
    orientation: Orientation
    seed: int
    steps: int
    guidance_scale: float
    model_id: str
    image_url: str
    mock: bool = False
    published: bool = False
    render_width: int | None = None
    render_height: int | None = None


class HealthResponse(BaseModel):
    status: str
    model_id: str
    device: str
    model_loaded: bool
    mock_generation: bool
    cuda_available: bool
    gpu_name: str | None = None
    vram_total_gb: float | None = None


class PresetsResponse(BaseModel):
    presets: list[DesktopPreset]


class GalleryItem(BaseModel):
    id: str
    prompt: str
    width: int
    height: int
    orientation: Orientation
    seed: int
    steps: int
    guidance_scale: float
    model_id: str
    image_url: str
    published_at: str


class GalleryResponse(BaseModel):
    items: list[GalleryItem]


class PublishRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    width: int = Field(..., ge=1, le=3840)
    height: int = Field(..., ge=1, le=3840)
    orientation: Orientation = "landscape"
    seed: int = 0
    steps: int = 0
    guidance_scale: float = 0.0


class PublishResponse(BaseModel):
    id: str
    published: bool
    image_url: str
