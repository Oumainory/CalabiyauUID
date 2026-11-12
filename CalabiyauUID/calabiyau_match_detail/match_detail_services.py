"""指定对局详情查询与卡片编排。"""

from ..utils.api.dakanu import DakanuError, fetch_match_detail
from ..utils.helper.resolve_player import region_label
from ..utils.render.html.match_detail_card import render_match_detail_card


async def build_match_detail_card(room_id: str, viewer_id: str, *, region: str = "cn") -> bytes:
    detail = await fetch_match_detail(viewer_id, room_id, region=region)
    if detail is None:
        raise DakanuError(f"没有找到对局「{room_id}」的详情，或站点暂未收录该场对局。")
    return await render_match_detail_card(
        detail,
        room_id=room_id,
        viewer_id=viewer_id,
        region=region_label(region),
    )
