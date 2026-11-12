"""好友榜查询与卡片编排。"""

from ..utils.api.dakanu import DakanuError, fetch_friend_ranking
from ..utils.helper.resolve_player import region_label, parse_region_keyword
from ..utils.render.html.friends_card import render_friends_card


async def build_friends_card(raw_text: str) -> bytes:
    query, region = parse_region_keyword(raw_text)
    if query:
        raise DakanuError("用法：kq好友榜 [国际服]")
    payload = await fetch_friend_ranking(page=1, page_size=20, region=region)
    return await render_friends_card(payload, region=region_label(region))
