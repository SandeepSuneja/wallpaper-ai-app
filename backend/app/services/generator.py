from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from app.config import Settings
from app.schemas.generation import DesktopPreset, GenerateRequest

logger = logging.getLogger(__name__)

DESKTOP_PRESETS: list[DesktopPreset] = [
    DesktopPreset(
        id="fhd_16_9",
        label="Full HD · 1920×1080",
        width=1920,
        height=1080,
        aspect="16:9",
        orientation="landscape",
        steps=32,
        guidance_scale=4.0,
    ),
    DesktopPreset(
        id="qhd_16_9",
        label="QHD · 2560×1440",
        width=2560,
        height=1440,
        aspect="16:9",
        orientation="landscape",
        steps=36,
        guidance_scale=4.0,
    ),
    DesktopPreset(
        id="uhd_16_9",
        label="4K UHD · 3840×2160",
        width=3840,
        height=2160,
        aspect="16:9",
        orientation="landscape",
        steps=40,
        guidance_scale=4.0,
    ),
    DesktopPreset(
        id="ultrawide_21_9",
        label="Ultrawide · 2560×1080",
        width=2560,
        height=1080,
        aspect="21:9",
        orientation="landscape",
        steps=36,
        guidance_scale=4.0,
    ),
    DesktopPreset(
        id="phone_fhd_9_16",
        label="Phone FHD · 1080×1920",
        width=1080,
        height=1920,
        aspect="9:16",
        orientation="portrait",
        steps=32,
        guidance_scale=4.0,
    ),
    DesktopPreset(
        id="phone_qhd_9_16",
        label="Phone QHD · 1440×2560",
        width=1440,
        height=2560,
        aspect="9:16",
        orientation="portrait",
        steps=36,
        guidance_scale=4.0,
    ),
    DesktopPreset(
        id="tablet_10_16",
        label="Tablet · 1600×2560",
        width=1600,
        height=2560,
        aspect="10:16",
        orientation="portrait",
        steps=36,
        guidance_scale=4.0,
    ),
]

_PRESET_MAP = {preset.id: preset for preset in DESKTOP_PRESETS}

LANDSCAPE_QUALITY_SUFFIX = (
    "ultra detailed desktop wallpaper, cinematic wide composition, rich color grading, "
    "sharp focus, high dynamic range, no watermark, no text, no logo, no UI"
)

PORTRAIT_QUALITY_SUFFIX = (
    "ultra detailed mobile wallpaper, vertical composition, rich color grading, "
    "sharp focus, high dynamic range, no watermark, no text, no logo, no UI"
)


def cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


def gpu_info() -> tuple[str | None, float | None]:
    try:
        import torch

        if not torch.cuda.is_available():
            return None, None
        props = torch.cuda.get_device_properties(0)
        return props.name, round(props.total_memory / (1024**3), 2)
    except Exception:  # noqa: BLE001
        return None, None


@dataclass
class GenerationResult:
    id: str
    prompt: str
    width: int
    height: int
    orientation: str
    seed: int
    steps: int
    guidance_scale: float
    model_id: str
    image_path: Path
    mock: bool
    published: bool
    render_width: int
    render_height: int


class WallpaperGenerator:
    """FLUX.2-klein-base-4B desktop wallpaper generator."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pipe = None
        self._lock = threading.Lock()
        self._loaded = False

    @property
    def model_loaded(self) -> bool:
        return self._loaded

    def resolve_size(self, request: GenerateRequest) -> tuple[int, int]:
        if request.preset == "custom":
            if request.width is None or request.height is None:
                raise ValueError("Custom preset requires both width and height.")
            return request.width, request.height

        preset = _PRESET_MAP.get(request.preset)
        if preset is None:
            raise ValueError(f"Unknown preset: {request.preset}")
        if preset.orientation != request.orientation:
            raise ValueError(
                f"Preset '{request.preset}' is {preset.orientation}, "
                f"but orientation is set to {request.orientation}."
            )
        return preset.width, preset.height

    def ensure_loaded(self) -> None:
        if self.settings.mock_generation:
            self._loaded = True
            return

        if self._loaded and self._pipe is not None:
            return

        with self._lock:
            if self._loaded and self._pipe is not None:
                return
            self._load_pipeline_unlocked()

    def _load_pipeline_unlocked(self) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "PyTorch is not installed. Install backend ML deps or set MOCK_GENERATION=true."
            ) from exc

        if not torch.cuda.is_available() and self.settings.device.startswith("cuda"):
            raise RuntimeError(
                "CUDA is not available. Set MOCK_GENERATION=true for UI work, "
                "or set DEVICE=cpu (very slow)."
            )

        dtype_map = {
            "bfloat16": torch.bfloat16,
            "float16": torch.float16,
            "float32": torch.float32,
        }
        dtype = dtype_map.get(self.settings.dtype, torch.bfloat16)

        logger.info("Loading model %s on %s (%s)...", self.settings.model_id, self.settings.device, dtype)
        try:
            from diffusers import Flux2KleinPipeline
        except ImportError as exc:
            raise RuntimeError(
                "Flux2KleinPipeline is missing. Install:\n"
                "pip install git+https://github.com/huggingface/diffusers.git"
            ) from exc

        try:
            pipe = Flux2KleinPipeline.from_pretrained(
                self.settings.model_id,
                dtype=dtype,
            )
        except TypeError:
            # Older Diffusers builds still expect torch_dtype.
            pipe = Flux2KleinPipeline.from_pretrained(
                self.settings.model_id,
                torch_dtype=dtype,
            )

        # Keep memory footprint safe on 12GB cards.
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_tiling"):
            pipe.vae.enable_tiling()
        if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
            pipe.vae.enable_slicing()

        if self.settings.device.startswith("cuda"):
            mode = self.settings.offload_mode.lower()
            if mode == "sequential" and hasattr(pipe, "enable_sequential_cpu_offload"):
                pipe.enable_sequential_cpu_offload()
            elif mode == "none":
                pipe.to("cuda")
            else:
                pipe.enable_model_cpu_offload()
        else:
            pipe.to(self.settings.device)

        self._pipe = pipe
        self._loaded = True
        logger.info("Model ready (%s offload).", self.settings.offload_mode)

    def resolve_quality(self, request: GenerateRequest) -> tuple[int, float]:
        preset = _PRESET_MAP.get(request.preset)
        steps = request.steps if request.steps is not None else (preset.steps if preset else 36)
        guidance = (
            request.guidance_scale
            if request.guidance_scale is not None
            else (preset.guidance_scale if preset else 4.0)
        )
        return steps, guidance

    def generate(self, request: GenerateRequest) -> GenerationResult:
        width, height = self.resolve_size(request)
        steps, guidance = self.resolve_quality(request)
        render_w, render_h = self._render_size(width, height, self.settings.render_max_side)
        seed = request.seed if request.seed is not None else int(datetime.now(tz=timezone.utc).timestamp()) % (2**31)
        image_id = uuid.uuid4().hex
        output_path = self.settings.output_dir / f"{image_id}.png"
        prompt = self._prepare_prompt(request.prompt, request.orientation)

        self.ensure_loaded()

        if self.settings.mock_generation:
            image = self._mock_image(request.prompt, width, height, seed)
            self._save_png(image, output_path)
            published = self._maybe_publish(request, image_id, width, height, seed, steps, guidance)
            return GenerationResult(
                id=image_id,
                prompt=request.prompt,
                width=width,
                height=height,
                orientation=request.orientation,
                seed=seed,
                steps=steps,
                guidance_scale=guidance,
                model_id=self.settings.model_id,
                image_path=output_path,
                mock=True,
                published=published,
                render_width=render_w,
                render_height=render_h,
            )

        import torch

        assert self._pipe is not None
        generator = torch.Generator(device="cpu").manual_seed(seed)

        logger.info(
            "Generating wallpaper id=%s orient=%s render=%sx%s target=%sx%s steps=%s guidance=%s",
            image_id,
            request.orientation,
            render_w,
            render_h,
            width,
            height,
            steps,
            guidance,
        )

        with self._lock:
            with torch.inference_mode():
                result = self._pipe(
                    prompt=prompt,
                    height=render_h,
                    width=render_w,
                    guidance_scale=guidance,
                    num_inference_steps=steps,
                    generator=generator,
                )
                image = result.images[0]

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        if (render_w, render_h) != (width, height):
            image = self._upscale_wallpaper(image, width, height)

        self._save_png(image, output_path)
        published = self._maybe_publish(request, image_id, width, height, seed, steps, guidance)
        logger.info("Saved wallpaper %s published=%s", output_path, published)

        return GenerationResult(
            id=image_id,
            prompt=request.prompt,
            width=width,
            height=height,
            orientation=request.orientation,
            seed=seed,
            steps=steps,
            guidance_scale=guidance,
            model_id=self.settings.model_id,
            image_path=output_path,
            mock=False,
            published=published,
            render_width=render_w,
            render_height=render_h,
        )

    def _maybe_publish(
        self,
        request: GenerateRequest,
        image_id: str,
        width: int,
        height: int,
        seed: int,
        steps: int,
        guidance: float,
    ) -> bool:
        if not request.publish:
            return False

        from app.services.catalog import get_catalog

        get_catalog().publish(
            image_id=image_id,
            prompt=request.prompt,
            width=width,
            height=height,
            orientation=request.orientation,
            seed=seed,
            steps=steps,
            guidance_scale=guidance,
            model_id=self.settings.model_id,
        )
        return True

    def _prepare_prompt(self, prompt: str, orientation: str) -> str:
        cleaned = " ".join(prompt.strip().split())
        if not self.settings.enhance_wallpaper_prompt:
            return cleaned

        lowered = cleaned.lower()
        if "wallpaper" in lowered or "desktop" in lowered or "mobile" in lowered:
            return cleaned

        suffix = PORTRAIT_QUALITY_SUFFIX if orientation == "portrait" else LANDSCAPE_QUALITY_SUFFIX
        return f"{cleaned}, {suffix}"

    def _save_png(self, image: Image.Image, path: Path) -> None:
        image.save(
            path,
            format="PNG",
            optimize=True,
            compress_level=self.settings.png_compress_level,
        )

    @staticmethod
    def _render_size(width: int, height: int, max_side: int) -> tuple[int, int]:
        """Downscale for inference while preserving aspect ratio (multiples of 16)."""
        scale = min(1.0, max_side / max(width, height))
        render_w = max(16, int(round(width * scale / 16) * 16))
        render_h = max(16, int(round(height * scale / 16) * 16))
        return render_w, render_h

    @staticmethod
    def _upscale_wallpaper(image: Image.Image, width: int, height: int) -> Image.Image:
        """High-quality upscale for crisp desktop wallpapers."""
        upscaled = image.resize((width, height), Image.Resampling.LANCZOS)
        # Mild detail recovery after Lanczos without oversharpening artifacts.
        detail = upscaled.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=2))
        blended = Image.blend(upscaled, detail, alpha=0.35)
        return ImageEnhance.Contrast(blended).enhance(1.03)

    @staticmethod
    def _mock_image(prompt: str, width: int, height: int, seed: int) -> Image.Image:
        image = Image.new("RGB", (width, height), "#0f1720")
        draw = ImageDraw.Draw(image)
        for i in range(8):
            y0 = int(height * (i / 8))
            y1 = int(height * ((i + 1) / 8))
            tone = 18 + i * 8
            draw.rectangle((0, y0, width, y1), fill=(tone, tone + 12, tone + 22))

        accent = (56 + (seed % 40), 140 + (seed % 60), 160 + (seed % 40))
        draw.ellipse(
            (width * 0.55, height * 0.15, width * 0.92, height * 0.75),
            fill=accent,
        )

        try:
            font = ImageFont.truetype("arial.ttf", size=max(28, width // 40))
            small = ImageFont.truetype("arial.ttf", size=max(18, width // 70))
        except OSError:
            font = ImageFont.load_default()
            small = font

        draw.text((48, 48), "Wallcraft · mock preview", fill="#e8eef4", font=font)
        clipped = prompt if len(prompt) < 90 else prompt[:87] + "..."
        draw.text((48, 110), clipped, fill="#b7c4d1", font=small)
        draw.text((48, height - 80), f"{width}×{height} · seed {seed}", fill="#8fa0b0", font=small)
        return image


_generator: WallpaperGenerator | None = None


def get_generator(settings: Settings | None = None) -> WallpaperGenerator:
    global _generator
    if _generator is None:
        from app.config import get_settings

        _generator = WallpaperGenerator(settings or get_settings())
    return _generator
