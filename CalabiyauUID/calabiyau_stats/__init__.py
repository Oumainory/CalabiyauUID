"""卡拉彼丘战绩命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .stats_services import resolve_player_id, extract_season_tag, render_snapshot_card, resolve_season_label
from ..utils.api.dakanu import DakanuError
from ..utils.helper.player_data import load_player_snapshot, load_or_fetch_player_snapshot
from ..utils.helper.resolve_player import region_label, parse_region_keyword

sv_stats = SV("卡拉彼丘战绩查询")


@sv_stats.on_command("战绩总览", block=True)
async def calabiyau_stats_summary(bot: Bot, ev: Event) -> None:
    raw_text, season_label = extract_season_tag(ev.text.strip())
    player_query, _ = parse_region_keyword(raw_text)
    explicit_target = bool(player_query)
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

    if explicit_target or season is not None or region == "global":
        try:
            snapshot = await load_or_fetch_player_snapshot(player_id, region=region)
        except DakanuError as exc:
            await bot.send(str(exc))
            return
    else:
        snapshot = await load_player_snapshot(player_id, region=region)
    if snapshot is None:
        if explicit_target:
            await bot.send(f"本地还没有这个玩家的{region_label(region)}战绩缓存。\n发送 kq刷新数据 {player_id} 拉取后再查看。")
        else:
            await bot.send("本地还没有这个玩家的战绩。\n发送 kq刷新数据 拉取后再查看。")
        return

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
    except RuntimeError:
        logger.exception("[卡拉彼丘·战绩总览] 渲染卡片失败")
        await bot.send("战绩卡片生成失败，请稍后再试。")
        return

    await bot.send(image)
