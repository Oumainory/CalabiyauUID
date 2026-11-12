"""按历史战绩卡片的资源规则加载角色立绘。"""

import asyncio
from pathlib import Path

from gsuid_core.pool import to_thread

from .assets import image_data_uri, local_role_image
from ..api.dakanu import role_image_url
from ..downloader import resolve_image


def _read_image_uri(path: Path) -> str:
    return image_data_uri(path.read_bytes(), path.suffix)


async def _resolve_role_image_uri(role_id: int) -> str:
    path = await resolve_image(role_image_url(role_id), local_role_image(role_id))
    if path is None:
        return ""
    return await to_thread(_read_image_uri)(path)


async def load_role_images(role_ids: set[int]) -> dict[int, str]:
    """优先读取本地角色立绘，缺失时使用 Dakanu 资源缓存。"""
    ordered = sorted(role_ids)
    uris = await asyncio.gather(*(_resolve_role_image_uri(role_id) for role_id in ordered))
    return {role_id: uri for role_id, uri in zip(ordered, uris, strict=True)}
