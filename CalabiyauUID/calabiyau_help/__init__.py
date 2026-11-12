"""卡拉彼丘插件帮助命令。"""

from PIL import Image

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.help.utils import register_help

from .get_help import ICON, get_help

sv_help = SV("卡拉彼丘帮助")


@sv_help.on_fullmatch("帮助", block=True)
async def calabiyau_help(bot: Bot, ev: Event) -> None:
    await bot.send(await get_help(ev.user_pm))


register_help("CalabiyauUID", "kq帮助", Image.open(ICON))
