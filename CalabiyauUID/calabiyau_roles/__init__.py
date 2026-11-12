"""卡拉彼丘超弦体排行命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .roles_services import build_roles_card
from ..utils.api.dakanu import DakanuError

sv_roles = SV("卡拉彼丘超弦体排行")


@sv_roles.on_command("角色排行", block=True)
async def calabiyau_role_ranking(bot: Bot, ev: Event) -> None:
    try:
        image = await build_roles_card(ev.text.strip())
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·超弦体榜] 卡片生成失败")
        await bot.send("超弦体排行卡片生成失败，请稍后再试。")
        return
    await bot.send(image)
