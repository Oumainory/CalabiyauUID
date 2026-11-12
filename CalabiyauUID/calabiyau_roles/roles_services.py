"""超弦体排行查询与卡片编排。"""

from ..utils.api.dakanu import DakanuError, fetch_role_ranking
from ..utils.helper.resolve_player import region_label, parse_region_keyword
from ..utils.render.html.roles_card import render_roles_card


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
    return await render_roles_card(payload, region=region_label(region), ranked_only=ranked_only)
