"""卡拉彼丘历史战绩命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .matches_services import resolve_match_player_id, build_recent_matches_card
from ..utils.api.dakanu import DakanuError

sv_matches = SV("卡拉彼丘历史战绩")


@sv_matches.on_fullmatch("历史战绩", block=True)
async def calabiyau_recent_matches(bot: Bot, ev: Event) -> None:
    player_id, error = await resolve_match_player_id(ev)
    if error is not None:
        await bot.send(error)
        return
    try:
        image = await build_recent_matches_card(player_id)
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·历史战绩] 渲染卡片失败")
        await bot.send("历史战绩卡片生成失败，请稍后再试。")
        return
    await bot.send(image)
