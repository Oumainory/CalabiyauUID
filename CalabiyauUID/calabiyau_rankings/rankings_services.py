"""排行榜参数解析与卡片编排。"""

import re

from ..utils.api.dakanu import DakanuError, fetch_rankings, fetch_ranking_types, fetch_ranking_seasons
from ..utils.helper.resolve_player import region_label, parse_region_keyword
from ..utils.render.html.rankings_card import render_rankings_card

RANK_TYPES = {
    "段位榜": 1,
    "团队乱斗榜": 2,
    "极限推进榜": 6,
    "挑战榜": 7,
    "晶源感染榜": 8,
}


def _remove_season_tag(raw_text: str) -> tuple[str, str | None]:
    match = re.search(r"(?<!\S)(S\d+EP\d+)(?!\S)", raw_text, re.IGNORECASE)
    if match is None:
        return raw_text, None
    remaining = f"{raw_text[:match.start()]} {raw_text[match.end():]}"
    return " ".join(remaining.split()), match.group(1).upper()


async def _season_id(label: str | None, region: str) -> tuple[int | None, str]:
    payload = await fetch_ranking_seasons(region=region)
    current = payload.get("current")
    current_label = current.get("label") if isinstance(current, dict) else None
    if label is None:
        return None, current_label if isinstance(current_label, str) else "当前赛季"
    seasons = payload.get("seasons", [])
    for season in seasons if isinstance(seasons, list) else []:
        if not isinstance(season, dict):
            continue
        season_label = season.get("label")
        season_id = season.get("season_id")
        if (
            isinstance(season_label, str)
            and season_label.casefold() == label.casefold()
            and isinstance(season_id, int)
            and not isinstance(season_id, bool)
        ):
            return season_id, season_label
    raise DakanuError(f"没有在 Dakanu 赛季列表中找到「{label}」。请确认赛季标签后重试。")


async def build_rankings_card(raw_text: str, *, forced_type: int | None = None) -> bytes:
    query, region = parse_region_keyword(raw_text)
    query, season_tag = _remove_season_tag(query)
    selected_type = forced_type
    remaining: list[str] = []
    for token in query.split():
        if token in RANK_TYPES:
            if selected_type is None:
                selected_type = RANK_TYPES[token]
        else:
            remaining.append(token)
    if remaining:
        raise DakanuError("用法：kq排行榜 [段位榜/团队乱斗榜/极限推进榜/挑战榜/晶源感染榜] [S26EP4] [国际服]")
    if selected_type is None:
        selected_type = RANK_TYPES["段位榜"]

    types_payload = await fetch_ranking_types(region=region)
    available_types = types_payload.get("types", [])
    type_info = next(
        (
            item
            for item in available_types
            if isinstance(item, dict) and item.get("code") == selected_type
        ),
        None,
    ) if isinstance(available_types, list) else None
    if type_info is None:
        raise DakanuError("Dakanu 暂未提供该排行榜类型。")
    type_label = type_info.get("label") if isinstance(type_info.get("label"), str) else "排行榜"

    season_id, season_label = await _season_id(season_tag, region)
    payload = await fetch_rankings(
        selected_type,
        page=1,
        page_size=20,
        season_id=season_id,
        region=region,
    )
    return await render_rankings_card(
        payload,
        title=type_label,
        season=season_label,
        region=region_label(region),
    )
