"""按历史战绩卡片的资源规则加载玩家头像。"""

import asyncio
from pathlib import Path

from gsuid_core.pool import to_thread

from .assets import image_data_uri, local_avatar_image
from ..downloader import resolve_image


def _read_image_uri(path: Path) -> str:
    return image_data_uri(path.read_bytes(), path.suffix)


async def _resolve_avatar_image_uri(avatar_id: int) -> str:
    url = f"https://www.dakanu.com/avatars/{avatar_id}.webp"
    path = await resolve_image(url, local_avatar_image(avatar_id))
    if path is None:
        return ""
    return await to_thread(_read_image_uri)(path)


async def load_avatar_images(avatar_ids: set[int]) -> dict[int, str]:
    """优先读取本地素材，缺失时使用 Dakanu 头像缓存。"""
    ordered = sorted(avatar_ids)
    uris = await asyncio.gather(*(_resolve_avatar_image_uri(avatar_id) for avatar_id in ordered))
    return {avatar_id: uri for avatar_id, uri in zip(ordered, uris, strict=True)}
