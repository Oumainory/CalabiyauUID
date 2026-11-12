"""共用卡拉彼丘玩家参数解析。"""

from gsuid_core.models import Event

from ..api.dakanu import DakanuError, DakanuPlayerSuggestion, search_players
from ..database.model_bind import get_main_uid


async def resolve_player_argument(raw_text: str) -> tuple[str, str | None]:
    """把 UID 或昵称解析为 UID；同优先级搜索结果有歧义时要求用户细化。"""
    query = raw_text.strip()
    if not query:
        return "", "请在命令后附带卡拉彼丘 UID 或昵称。"
    if query.isdigit():
        return query, None

    try:
        suggestions = await search_players(query)
    except DakanuError as exc:
        return "", str(exc)

    if not suggestions:
        return "", f"没有找到昵称「{query}」对应的玩家。"

    normalized_query = query.casefold()
    exact = [
        suggestion
        for suggestion in suggestions
        if suggestion.get("exact") is True or suggestion["nickname"].casefold() == normalized_query
    ]
    if exact:
        candidates = exact
    else:
        candidates = [
            suggestion
            for suggestion in suggestions
            if suggestion["nickname"].casefold().startswith(normalized_query)
        ]
    if len(candidates) == 1:
        return candidates[0]["playerId"], None
    if len(candidates) > 1:
        return "", _ambiguous_message(query, candidates)

    return suggestions[0]["playerId"], None


async def resolve_player_query(ev: Event, *, allow_at: bool = False) -> tuple[str, str | None]:
    """解析显式 UID/昵称，或回退到当前绑定账号；可选支持查询 @ 用户。"""
    raw_text = ev.text.strip()
    if raw_text:
        return await resolve_player_argument(raw_text)

    at_target = ev.at.strip() if allow_at and ev.at is not None else ""
    is_self_at = at_target in {ev.bot_id, ev.real_bot_id, ev.bot_self_id}
    target_user = ev.user_id if not at_target or is_self_at else at_target
    player_id = await get_main_uid(ev.bot_id, target_user)
    if player_id is not None:
        return player_id, None
    if target_user == ev.user_id:
        return "", "尚未绑定卡拉彼丘账号。\n发送 kq绑定 <UID 或昵称> 进行绑定。"
    return "", "对方尚未绑定卡拉彼丘账号。"


def _ambiguous_message(query: str, candidates: list[DakanuPlayerSuggestion]) -> str:
    lines = [f"昵称「{query}」匹配到多个玩家，请选择更精确的昵称或直接使用 UID："]
    for candidate in candidates[:5]:
        nickname = " ".join(candidate["nickname"].split())
        line = f"- {nickname}（UID {candidate['playerId']}）"
        level = candidate.get("level")
        if level is not None:
            line += f"，等级 {level}"
        lines.append(line)
    return "\n".join(lines)
