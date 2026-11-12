"""卡拉彼丘指定对局详情命令。"""

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.api.dakanu import DakanuError
from .match_detail_services import build_match_detail_card
from ..utils.database.model_bind import get_main_uid
from ..utils.helper.resolve_player import parse_region_keyword, resolve_player_argument

sv_match_detail = SV("卡拉彼丘对局详情")


async def _send_match_detail(bot: Bot, ev: Event) -> None:
    text = ev.text.strip()
    if text.startswith("详情"):
        text = text[2:].strip()
    query, region = parse_region_keyword(text)
    arguments = query.split()
    if not arguments:
        await bot.send("请附带对局编号。用法：kq对局 <对局编号> [UID 或昵称] [国际服]")
        return
    room_id = arguments[0]
    viewer_query = " ".join(arguments[1:]).strip()
    if viewer_query:
        viewer_id, error = await resolve_player_argument(viewer_query, region=region)
        if error is not None:
            await bot.send(error)
            return
    else:
        viewer_id = await get_main_uid(ev.bot_id, ev.user_id)
        if viewer_id is None:
            await bot.send("尚未绑定卡拉彼丘账号。请提供视角玩家 UID/昵称，或先发送 kq绑定。")
            return
    try:
        image = await build_match_detail_card(room_id, str(viewer_id), region=region)
    except DakanuError as exc:
        await bot.send(str(exc))
        return
    except RuntimeError:
        logger.exception("[卡拉彼丘·对局详情] 卡片生成失败")
        await bot.send("对局详情卡片生成失败，请稍后再试。")
        return
    await bot.send(image)


@sv_match_detail.on_command(("对局详情", "对局"), block=True)
async def calabiyau_match_detail(bot: Bot, ev: Event) -> None:
    await _send_match_detail(bot, ev)
