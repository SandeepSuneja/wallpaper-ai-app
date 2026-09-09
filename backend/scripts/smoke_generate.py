"""Smoke-test FLUX.2-klein-base-4B wallpaper generation."""

from app.config import get_settings
from app.schemas.generation import GenerateRequest
from app.services.generator import get_generator


def main() -> None:
    settings = get_settings()
    print("model:", settings.model_id)
    print("mock:", settings.mock_generation)
    print("device:", settings.device)

    generator = get_generator(settings)
    generator.ensure_loaded()

    result = generator.generate(
        GenerateRequest(
            prompt=(
                "Cinematic alpine lake at dawn, soft mist over glassy water, "
                "pine ridges in deep teal shadow, warm amber light on distant peaks"
            ),
            preset="fhd_16_9",
            steps=28,
            guidance_scale=4.0,
            seed=42,
        )
    )
    print("saved:", result.image_path)
    print("size:", result.width, "x", result.height)
    print("render:", result.render_width, "x", result.render_height)
    print("mock:", result.mock)


if __name__ == "__main__":
    main()
