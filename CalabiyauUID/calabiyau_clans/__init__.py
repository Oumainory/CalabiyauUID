"""卡拉彼丘战队查询命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .clans_services import build_clan_card
from ..utils.api.dakanu import DakanuError

sv_clans = SV("卡拉彼丘战队查询")


@sv_clans.on_command("战队", block=True)
async def calabiyau_clan(bot: Bot, ev: Event) -> None:
    try:
        image = await build_clan_card(ev.text.strip())
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·战队] 卡片生成失败")
        await bot.send("战队卡片生成失败，请稍后再试。")
        return
    await bot.send(image)
