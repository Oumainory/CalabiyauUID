"""卡拉彼丘插件帮助图生成。"""

import json
from pathlib import Path

from PIL import Image

from gsuid_core.help.draw_new_plugin_help import get_new_help
from gsuid_core.help.model import PluginHelp

ICON = Path(__file__).parent.parent.parent / "ICON.png"
HELP_DATA = Path(__file__).parent / "help.json"
ICON_PATH = Path(__file__).parent / "icon_path"
TEXT_PATH = Path(__file__).parent / "texture2d"


def get_help_data() -> dict[str, PluginHelp]:
    with HELP_DATA.open(encoding="utf-8") as file:
        return json.load(file)


plugin_help = get_help_data()


def _maybe(name: str) -> Image.Image | None:
    path = TEXT_PATH / name
    return Image.open(path) if path.exists() else None


async def get_help(pm: int):
    return await get_new_help(
        plugin_name="CalabiyauUID",
        plugin_info={},
        plugin_icon=Image.open(ICON),
        plugin_help=plugin_help,
        plugin_prefix="kq",
        help_mode="dark",
        banner_bg=_maybe("banner_bg.png"),
        banner_sub_text="卡拉彼丘战绩查询与账号管理",
        help_bg=_maybe("bg.jpg"),
        cag_bg=_maybe("cag_bg.png"),
        item_bg=_maybe("item.png"),
        icon_path=ICON_PATH,
        enable_cache=False,
        column=4,
        pm=pm,
    )
