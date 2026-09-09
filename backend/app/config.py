from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    model_id: str = "black-forest-labs/FLUX.2-klein-base-4B"
    device: str = "cuda"
    dtype: str = "bfloat16"
    output_dir: Path = Path("outputs")
    mock_generation: bool = False
    host: str = "0.0.0.0"
    port: int = 8001
    cors_origins: str = "http://localhost:4200"

    # HQ generation knobs (tuned for ~12GB GPUs like RTX 4070 SUPER)
    preload_model: bool = True
    render_max_side: int = 1280
    default_steps: int = 40
    default_guidance: float = 4.0
    offload_mode: str = "model"  # model | sequential | none
    enhance_wallpaper_prompt: bool = True
    png_compress_level: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    return settings
