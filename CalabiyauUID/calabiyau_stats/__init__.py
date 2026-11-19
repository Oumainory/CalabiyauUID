"""卡拉彼丘战绩命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .stats_services import resolve_player_id, extract_season_tag, render_snapshot_card, resolve_season_label, ensure_player_snapshot
from ..utils.api.dakanu import DakanuError
from ..utils.helper.player_data import load_player_snapshot

sv_stats = SV("卡拉彼丘战绩查询")


@sv_stats.on_command("战绩总览", block=True)
async def calabiyau_stats_summary(bot: Bot, ev: Event) -> None:
    raw_text, season_label = extract_season_tag(ev.text.strip())
    player_id, region, error = await resolve_player_id(ev, raw_text=raw_text)
    if error is not None:
        await bot.send(error)
        return

    season: tuple[int, str] | None = None
    if season_label is not None:
        try:
            season = await resolve_season_label(season_label, region=region)
        except DakanuError as exc:
            await bot.send(str(exc))
            return
        if season is None:
            await bot.send(f"没有在 Dakanu 赛季列表中找到「{season_label}」。请确认赛季标签后重试。")
            return

    await bot.send("正在同步最新战绩，通常需要 10～30 秒，完成后会发图。")
    try:
        snapshot = await ensure_player_snapshot(player_id, refresh=True, region=region)
    except (DakanuError, RuntimeError) as exc:
        snapshot = await load_player_snapshot(player_id, region=region)
        if snapshot is None:
            await bot.send(str(exc))
            return
        await bot.send(f"最新数据刷新失败：{exc}\n先显示本地快照。")

    try:
        image = await render_snapshot_card(
            snapshot,
            season_id=season[0] if season else None,
            season_label=season[1] if season else None,
            region=region,
        )
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except Exception:
        logger.exception("[卡拉彼丘·战绩总览] 渲染卡片失败")
        await bot.send("战绩卡片生成失败，请稍后再试。")
        return

    await bot.send(image)
