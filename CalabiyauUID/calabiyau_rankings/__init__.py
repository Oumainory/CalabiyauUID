"""卡拉彼丘全服排行榜命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.api.dakanu import DakanuError
from .rankings_services import RANK_TYPES, build_rankings_card

sv_rankings = SV("卡拉彼丘排行榜")


async def _send_rankings(bot: Bot, ev: Event, forced_type: int | None = None) -> None:
    try:
        image = await build_rankings_card(ev.text.strip(), forced_type=forced_type)
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·排行榜] 卡片生成失败")
        await bot.send("排行榜卡片生成失败，请稍后再试。")
        return
    await bot.send(image)


@sv_rankings.on_command("排行榜", block=True)
async def calabiyau_rankings(bot: Bot, ev: Event) -> None:
    await _send_rankings(bot, ev)


@sv_rankings.on_command("段位榜", block=True)
async def calabiyau_rank_stars(bot: Bot, ev: Event) -> None:
    await _send_rankings(bot, ev, RANK_TYPES["段位榜"])


@sv_rankings.on_command("团队乱斗榜", block=True)
async def calabiyau_rank_team(bot: Bot, ev: Event) -> None:
    await _send_rankings(bot, ev, RANK_TYPES["团队乱斗榜"])


@sv_rankings.on_command("极限推进榜", block=True)
async def calabiyau_rank_pushcar(bot: Bot, ev: Event) -> None:
    await _send_rankings(bot, ev, RANK_TYPES["极限推进榜"])


@sv_rankings.on_command("挑战榜", block=True)
async def calabiyau_rank_leisure(bot: Bot, ev: Event) -> None:
    await _send_rankings(bot, ev, RANK_TYPES["挑战榜"])


@sv_rankings.on_command("晶源感染榜", block=True)
async def calabiyau_rank_zombie(bot: Bot, ev: Event) -> None:
    await _send_rankings(bot, ev, RANK_TYPES["晶源感染榜"])
