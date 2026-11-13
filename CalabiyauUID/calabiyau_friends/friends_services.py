"""好友榜查询与卡片编排。"""

import asyncio

from ..utils.api.dakanu import DakanuError, fetch_friend_ranking
from ..utils.helper.map_images import load_map_images
from ..utils.helper.player_images import load_avatar_images
from ..utils.helper.resolve_player import region_label, parse_region_keyword
from ..utils.render.html.friends_card import render_friends_card


def _avatar_ids(payload: dict[str, object]) -> set[int]:
    avatar_ids: set[int] = set()
    entries = payload.get("entries")
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        for key in ("avatarA", "avatarB"):
            avatar_id = entry.get(key)
            if isinstance(avatar_id, int) and not isinstance(avatar_id, bool):
                avatar_ids.add(avatar_id)
    return avatar_ids


async def build_friends_card(raw_text: str) -> bytes:
    query, region = parse_region_keyword(raw_text)
    if query:
        raise DakanuError("用法：kq好友榜 [国际服]")
    payload = await fetch_friend_ranking(page=1, page_size=20, region=region)
    avatar_images, map_images = await asyncio.gather(
        load_avatar_images(_avatar_ids(payload)),
        load_map_images({"map-08"}),
    )
    return await render_friends_card(
        payload,
        region=region_label(region),
        avatar_images=avatar_images,
        banner_image=map_images.get("map-08", ""),
    )
