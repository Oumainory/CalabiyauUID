"""按历史战绩卡片的资源规则加载地图宽图。"""

import asyncio
from pathlib import Path

from gsuid_core.pool import to_thread

from .assets import image_data_uri, local_map_slug_image
from ..downloader import resolve_image


def _read_image_uri(path: Path) -> str:
    return image_data_uri(path.read_bytes(), path.suffix)


async def _resolve_map_image_uri(slug: str) -> str:
    try:
        path = await resolve_image(
            f"https://www.dakanu.com/maps-wide/{slug}.webp",
            local_map_slug_image(slug),
        )
        if path is None:
            return ""
        return await to_thread(_read_image_uri)(path)
    except Exception:
        return ""


async def load_map_images(slugs: set[str]) -> dict[str, str]:
    """优先读取本地地图宽图，缺失时使用 Dakanu 资源缓存。"""
    ordered = sorted(slugs)
    uris = await asyncio.gather(*(_resolve_map_image_uri(slug) for slug in ordered))
    return {slug: uri for slug, uri in zip(ordered, uris, strict=True)}
