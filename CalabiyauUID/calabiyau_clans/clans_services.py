"""战队搜索、成员读取与卡片编排。"""

import asyncio

from ..utils.api.dakanu import DakanuError, search_clans, fetch_clan_members
from ..utils.helper.map_images import load_map_images
from ..utils.helper.player_images import load_avatar_images
from ..utils.helper.resolve_player import region_label, parse_region_keyword
from ..utils.render.html.clan_card import render_clan_card


def _clans(payload: dict[str, object]) -> list[dict[str, object]]:
    values = payload.get("clans")
    return [value for value in values if isinstance(value, dict)] if isinstance(values, list) else []


def _member_avatar_ids(payload: dict[str, object] | None) -> set[int]:
    if payload is None:
        return set()
    members = payload.get("members")
    if not isinstance(members, list):
        data = payload.get("data")
        members = data.get("members") if isinstance(data, dict) else []
    if not isinstance(members, list):
        return set()
    return {
        member["avatarId"]
        for member in members[:32]
        if isinstance(member, dict)
        and isinstance(member.get("avatarId"), int)
        and not isinstance(member.get("avatarId"), bool)
    }


def _ambiguous_message(query: str, clans: list[dict[str, object]]) -> str:
    lines = [f"战队名称「{query}」匹配到多个结果，请按战队 ID 查询："]
    for clan in clans[:5]:
        name = clan.get("name") or "未命名战队"
        clan_id = clan.get("clanId") or clan.get("id") or "未知"
        level = clan.get("level")
        count = clan.get("memberCount")
        info = []
        if isinstance(level, int):
            info.append(f"Lv.{level}")
        if isinstance(count, int):
            info.append(f"{count} 人")
        suffix = f"，{' · '.join(info)}" if info else ""
        lines.append(f"- {name}（战队 ID {clan_id}{suffix}）")
    return "\n".join(lines)


async def build_clan_card(raw_text: str) -> bytes:
    query, region = parse_region_keyword(raw_text)
    if not query:
        raise DakanuError("请在命令后附带战队名称或战队 ID。")
    if query.isdigit():
        payload = await search_clans(clan_id=query, limit=1, region=region)
    else:
        payload = await search_clans(name=query, limit=10, region=region)
    clans = _clans(payload)
    if not clans:
        raise DakanuError(f"没有找到战队「{query}」。")
    if query.isdigit():
        matches = [clan for clan in clans if str(clan.get("clanId") or clan.get("id")) == query]
    else:
        exact = [
            clan
            for clan in clans
            if isinstance(clan.get("name"), str) and clan["name"].casefold() == query.casefold()
        ]
        matches = exact if exact else clans
    if len(matches) > 1:
        raise DakanuError(_ambiguous_message(query, matches))
    clan = matches[0]
    clan_id = clan.get("clanId") or clan.get("id")
    members = await fetch_clan_members(str(clan_id), region=region) if clan_id else None
    avatar_images, map_images = await asyncio.gather(
        load_avatar_images(_member_avatar_ids(members)),
        load_map_images({"map-01"}),
    )
    return await render_clan_card(
        clan,
        members,
        region=region_label(region),
        avatar_images=avatar_images,
        banner_image=map_images.get("map-01", ""),
    )
