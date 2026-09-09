from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.generation import GalleryItem, Orientation


class WallpaperCatalog:
    """Persists publish metadata so wallpapers can be listed publicly."""

    def __init__(self, catalog_path: Path) -> None:
        self.catalog_path = catalog_path
        self._lock = threading.Lock()
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.catalog_path.exists():
            self._write({"items": {}})

    def _read(self) -> dict[str, Any]:
        with self.catalog_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: dict[str, Any]) -> None:
        tmp = self.catalog_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        tmp.replace(self.catalog_path)

    def publish(
        self,
        *,
        image_id: str,
        prompt: str,
        width: int,
        height: int,
        orientation: Orientation,
        seed: int,
        steps: int,
        guidance_scale: float,
        model_id: str,
    ) -> GalleryItem:
        published_at = datetime.now(tz=timezone.utc).isoformat()
        item = {
            "id": image_id,
            "prompt": prompt,
            "width": width,
            "height": height,
            "orientation": orientation,
            "seed": seed,
            "steps": steps,
            "guidance_scale": guidance_scale,
            "model_id": model_id,
            "image_url": f"/api/images/{image_id}",
            "published_at": published_at,
            "published": True,
        }
        with self._lock:
            data = self._read()
            data.setdefault("items", {})[image_id] = item
            self._write(data)
        return GalleryItem(**{k: v for k, v in item.items() if k != "published"})

    def is_published(self, image_id: str) -> bool:
        with self._lock:
            data = self._read()
            entry = data.get("items", {}).get(image_id)
            return bool(entry and entry.get("published"))

    def list_published(self, orientation: Orientation | None = None) -> list[GalleryItem]:
        with self._lock:
            data = self._read()
            items = list(data.get("items", {}).values())

        published = [item for item in items if item.get("published")]
        if orientation:
            published = [item for item in published if item.get("orientation") == orientation]

        published.sort(key=lambda item: item.get("published_at", ""), reverse=True)
        return [
            GalleryItem(
                id=item["id"],
                prompt=item["prompt"],
                width=item["width"],
                height=item["height"],
                orientation=item["orientation"],
                seed=item["seed"],
                steps=item["steps"],
                guidance_scale=item["guidance_scale"],
                model_id=item["model_id"],
                image_url=item["image_url"],
                published_at=item["published_at"],
            )
            for item in published
        ]


_catalog: WallpaperCatalog | None = None


def get_catalog(catalog_path: Path | None = None) -> WallpaperCatalog:
    global _catalog
    if _catalog is None:
        from app.config import get_settings

        settings = get_settings()
        path = catalog_path or (settings.output_dir / "catalog.json")
        _catalog = WallpaperCatalog(path)
    return _catalog
