"""卡拉彼丘历史战绩命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .matches_services import resolve_match_player_id, build_recent_matches_card
from ..utils.api.dakanu import DakanuError
from ..utils.helper.refresh import refresh_player_data
from ..utils.helper.player_data import load_player_snapshot

sv_matches = SV("卡拉彼丘历史战绩")


@sv_matches.on_command("历史战绩", block=True)
async def calabiyau_recent_matches(bot: Bot, ev: Event) -> None:
    player_id, region, error = await resolve_match_player_id(ev)
    if error is not None:
        await bot.send(error)
        return
    await bot.send("正在同步最新战绩，通常需要 10～30 秒，完成后会发图。")
    try:
        snapshot = (await refresh_player_data(player_id, force=True, region=region)).snapshot
    except (DakanuError, RuntimeError) as exc:
        snapshot = await load_player_snapshot(player_id, region=region)
        if snapshot is None:
            await bot.send(str(exc))
            return
        await bot.send(f"最新数据刷新失败：{exc}\n先显示本地快照。")
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
