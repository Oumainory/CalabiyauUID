"""卡拉彼丘账号绑定、解绑与查看。"""

from ..utils.helper.refresh import refresh_player_data
from ..utils.helper.player_data import load_player_snapshot
from ..utils.database.model_bind import CalabiyauBind


async def bind_account(
    bot_id: str,
    user_id: str,
    game_uid: str,
) -> str:
    result = await refresh_player_data(game_uid)
    added = await CalabiyauBind.add_bind(bot_id, user_id, game_uid)
    source = "本地快照" if result.from_cache else "最新战绩"
    nickname = result.snapshot.profile["player"]["nickname"]
    account = f"[{game_uid}] {nickname}"
    if not added:
        return f"该账号已绑定：{account}\n{source}已准备就绪。"
    return f"绑定成功：{account} 已设为当前账号。\n{source}已保存。"


async def unbind_account(
    bot_id: str,
    user_id: str,
    game_uid: str,
) -> str:
    deleted, was_main, current_main = await CalabiyauBind.delete_bind(bot_id, user_id, game_uid)
    if not deleted:
        return f"未找到该账号的绑定：[{game_uid}]"
    if current_main is None:
        return f"已解绑：[{game_uid}]\n当前暂无绑定账号。"
    if not was_main:
        return f"已解绑：[{game_uid}]\n当前账号仍为：[{current_main}]"
    return f"已解绑：[{game_uid}]\n当前账号已切换为：[{current_main}]"


async def view_accounts(
    bot_id: str,
    user_id: str,
) -> str:
    binds = await CalabiyauBind.get_binds(bot_id, user_id)
    if not binds:
        return "尚未绑定卡拉彼丘账号。\n发送 kq绑定 <UID 或昵称> 进行绑定。"

    lines = [f"已绑定 {len(binds)} 个卡拉彼丘账号："]
    for index, bind in enumerate(binds, start=1):
        suffix = " [当前账号]" if bind.is_main else ""
        lines.append(f"{index}. {bind.game_uid}{suffix}")
    return "\n".join(lines)


async def switch_account(
    bot_id: str,
    user_id: str,
    game_uid: str | None = None,
) -> str:
    status, current_uid = await CalabiyauBind.switch_bind(bot_id, user_id, game_uid)
    if status == "empty":
        if game_uid is not None:
            return f"尚未绑定 UID {game_uid}。\n发送 kq绑定 {game_uid} 进行绑定。"
        return "尚未绑定卡拉彼丘账号。\n发送 kq绑定 <UID 或昵称> 进行绑定。"
    if status == "not_found":
        return f"未绑定 UID {game_uid}。\n发送 kq绑定 {game_uid} 进行绑定。"
    if status == "only_one":
        return f"当前只绑定了 1 个账号：[{current_uid}]，无需切换。"

    nickname = ""
    try:
        snapshot = await load_player_snapshot(current_uid) if current_uid is not None else None
        if snapshot is not None:
            nickname = snapshot.profile["player"].get("nickname", "")
    except (OSError, ValueError, KeyError, TypeError):
        nickname = ""
    account = f"[{current_uid}] {nickname}" if nickname else f"[{current_uid}]"
    return f"当前账号已切换为：{account}"
