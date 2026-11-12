"""卡拉彼丘历史战绩命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .matches_services import load_matches_snapshot, resolve_match_player_id, build_recent_matches_card
from ..utils.api.dakanu import DakanuError
from ..utils.helper.resolve_player import region_label, parse_region_keyword

sv_matches = SV("卡拉彼丘历史战绩")


@sv_matches.on_command("历史战绩", block=True)
async def calabiyau_recent_matches(bot: Bot, ev: Event) -> None:
    player_query, _ = parse_region_keyword(ev.text.strip())
    explicit_target = bool(player_query)
    player_id, region, error = await resolve_match_player_id(ev)
    if error is not None:
        await bot.send(error)
        return
    try:
        snapshot = await load_matches_snapshot(
            player_id,
            allow_cache_fetch=explicit_target or region == "global",
            region=region,
        )
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    if snapshot is None and explicit_target:
        await bot.send(
            f"本地还没有这个玩家的{region_label(region)}战绩缓存。\n发送 kq刷新数据 {player_id} 拉取后再查看。"
        )
        return
    try:
        image = await build_recent_matches_card(player_id, snapshot, region=region)
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·历史战绩] 渲染卡片失败")
        await bot.send("历史战绩卡片生成失败，请稍后再试。")
        return
    await bot.send(image)
