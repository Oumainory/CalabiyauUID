"""超弦体排行查询与卡片编排。"""

from ..utils.api.dakanu import DakanuError, fetch_role_ranking
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
    role_images = await load_role_images(_role_ids(payload))
    return await render_roles_card(
        payload,
        region=region_label(region),
        ranked_only=ranked_only,
        role_images=role_images,
    )
