"""卡拉彼丘全服好友榜命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .friends_services import build_friends_card
from ..utils.api.dakanu import DakanuError

sv_friends = SV("卡拉彼丘好友榜")


@sv_friends.on_command("好友榜", block=True)
async def calabiyau_friend_ranking(bot: Bot, ev: Event) -> None:
    try:
        image = await build_friends_card(ev.text.strip())
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·好友榜] 卡片生成失败")
        await bot.send("好友榜卡片生成失败，请稍后再试。")
        return
    await bot.send(image)
