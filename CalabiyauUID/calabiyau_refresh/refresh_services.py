"""执行强制刷新并回复用户。"""

import time

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..utils.api.dakanu import DakanuError
from ..utils.helper.refresh import refresh_player_data
from ..utils.helper.resolve_player import region_label, resolve_player_query_context


async def resolve_refresh_uid(ev: Event) -> tuple[str, str, str | None]:
    return await resolve_player_query_context(ev)


async def refresh_and_report(bot: Bot, ev: Event, player_id: str, region: str = "cn") -> None:
    try:
        result = await refresh_player_data(player_id, force=True, region=region)
    except DakanuError as exc:
        detail = str(exc)
        hint = "\n请检查 UID 是否正确；站点繁忙时可稍后重试。"
        if "没有找到" in detail:
            hint = "\n请确认 UID 是否正确后重试。"
        await bot.send([MessageSegment.at(ev.user_id), MessageSegment.text(f" 刷新失败：{detail}{hint}")])
        return
    except RuntimeError as exc:
        await bot.send([MessageSegment.at(ev.user_id), MessageSegment.text(f" 刷新失败：{exc}")])
        return
    saved_at = time.strftime("%Y-%m-%d %H:%M", time.localtime(result.snapshot.saved_at))
    await bot.send(
        [
            MessageSegment.at(ev.user_id),
            MessageSegment.text(f" {region_label(region)} UID {player_id} 战绩刷新成功。\n本地快照时间：{saved_at}"),
        ]
    )
