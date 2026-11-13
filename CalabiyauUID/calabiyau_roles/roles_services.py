"""超弦体排行查询与卡片编排。"""

import asyncio

from ..utils.api.dakanu import DakanuError, fetch_role_ranking
from ..utils.helper.maps import resolve_map
from ..utils.helper.map_images import load_map_images
from ..utils.helper.role_images import load_role_images
from ..utils.helper.resolve_player import region_label, parse_region_keyword
from ..utils.render.html.roles_card import render_roles_card


def _role_ids(payload: dict[str, object]) -> set[int]:
    role_ids: set[int] = set()
    entries = payload.get("entries")
    for entry in entries if isinstance(entries, list) else []:
        if isinstance(entry, dict):
            role_id = entry.get("roleId")
            if isinstance(role_id, int) and not isinstance(role_id, bool):
                role_ids.add(role_id)
    map_stats = payload.get("mapStats")
    for map_stat in map_stats if isinstance(map_stats, list) else []:
        if not isinstance(map_stat, dict):
            continue
        sides = map_stat.get("sides")
        for side in sides if isinstance(sides, list) else []:
            if not isinstance(side, dict):
                continue
            roles = side.get("roles")
            for role in roles if isinstance(roles, list) else []:
                role_id = role.get("roleId") if isinstance(role, dict) else None
                if isinstance(role_id, int) and not isinstance(role_id, bool):
                    role_ids.add(role_id)
    return role_ids


def _map_slugs(payload: dict[str, object]) -> set[str]:
    slugs = {"map-13"}
    map_stats = payload.get("mapStats")
    for map_stat in map_stats if isinstance(map_stats, list) else []:
        if not isinstance(map_stat, dict):
            continue
        map_id = map_stat.get("mapId")
        if isinstance(map_id, int) and not isinstance(map_id, bool):
            map_info = resolve_map(map_id)
            if map_info is not None:
                slugs.add(map_info.slug)
    return slugs


async def build_roles_card(raw_text: str) -> bytes:
    query, region = parse_region_keyword(raw_text)
    tokens = query.split()
    ranked_only = True
    remaining: list[str] = []
    for token in tokens:
        if token == "全模式":
            ranked_only = False
        elif token == "排位":
            ranked_only = True
        else:
            remaining.append(token)
    if remaining:
        raise DakanuError("用法：kq角色排行 [排位/全模式] [国际服]")
    payload = await fetch_role_ranking(ranked_only=ranked_only, region=region)
    role_images, map_images = await asyncio.gather(
        load_role_images(_role_ids(payload)),
        load_map_images(_map_slugs(payload)),
    )
    return await render_roles_card(
        payload,
        region=region_label(region),
        ranked_only=ranked_only,
        role_images=role_images,
        map_images=map_images,
        banner_image=map_images.get("map-13", ""),
    )
