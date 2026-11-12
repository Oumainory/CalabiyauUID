"""指定单场对局详情静态卡片。"""

import html
from datetime import datetime
from collections.abc import Mapping

from gsuid_core.utils.html_render import render_html_to_bytes

from ...helper.maps import resolve_map

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _read(source: object, *keys: str) -> object | None:
    if not isinstance(source, dict):
        return None
    for key in keys:
        value = source.get(key)
        if value is not None and value != "":
            return value
    return None


def _preferred(summary: object, detail: object, *keys: str) -> object | None:
    value = _read(summary, *keys)
    return value if value is not None else _read(detail, *keys)


def _duration(value: object) -> str:
    seconds = _int(value)
    if seconds is None or seconds <= 0:
        return "时长未知"
    hours, remainder = divmod(seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    if hours:
        return f"{hours} 小时 {minutes} 分 {remainder} 秒"
    return f"{minutes} 分 {remainder} 秒"


def _date_text(value: object) -> str:
    timestamp = _int(value)
    if timestamp is None or timestamp <= 0:
        return "时间未知"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


def _result(value: object) -> tuple[str, str]:
    if value == "win":
        return "胜利", "win"
    if value == "lose":
        return "失败", "lose"
    if value == "draw":
        return "平局", "draw"
    return "结果未知", "unknown"


def _viewer_team_index(teams: list[object], viewer_id: str | None) -> int | None:
    if viewer_id is not None:
        for index, team in enumerate(teams[:2]):
            if not isinstance(team, dict) or not isinstance(team.get("players"), list):
                continue
            if any(
                isinstance(player, dict) and str(player.get("playerId", "")) == viewer_id for player in team["players"]
            ):
                return index
    for index, team in enumerate(teams[:2]):
        if not isinstance(team, dict) or not isinstance(team.get("players"), list):
            continue
        if any(isinstance(player, dict) and player.get("isTarget") for player in team["players"]):
            return index
    return None


def _ordered_teams(teams: object, viewer_id: str | None) -> tuple[list[tuple[int, dict[str, object], str]], int | None]:
    if not isinstance(teams, list):
        return [], None
    candidates = [(index, team) for index, team in enumerate(teams[:2]) if isinstance(team, dict)]
    viewer_index = _viewer_team_index(teams, viewer_id)
    if viewer_index is None:
        viewer_index = candidates[0][0] if candidates else None
    ordered: list[tuple[int, dict[str, object], str]] = []
    for index, team in candidates:
        label = "我方" if index == viewer_index else "对方"
        ordered.append((index, team, label))
    ordered.sort(key=lambda item: item[0] != viewer_index)
    return ordered, viewer_index


def _summary_team_scores(summary: object) -> tuple[int | None, int | None]:
    score_a = _int(_read(summary, "teamAScore", "scoreA", "blueScore", "leftScore"))
    score_b = _int(_read(summary, "teamBScore", "scoreB", "redScore", "rightScore"))
    scores = _read(summary, "scores", "teamScores")
    if score_a is None and isinstance(scores, list) and len(scores) >= 2:
        score_a = _int(scores[0])
        score_b = _int(scores[1])
    return score_a, score_b


def _team_score(
    team: dict[str, object],
    team_index: int,
    viewer_team_index: int | None,
    summary: object,
) -> int | None:
    score = _int(team.get("score"))
    if score is not None:
        return score

    my_score = _int(_read(summary, "myScore", "viewerScore"))
    opponent_score = _int(_read(summary, "opponentScore", "enemyScore"))
    if my_score is not None or opponent_score is not None:
        own_index = viewer_team_index if viewer_team_index is not None else 0
        if team_index == own_index:
            return my_score
        return opponent_score

    score_a, score_b = _summary_team_scores(summary)
    return score_a if team_index == 0 else score_b


def _player_rows(team: dict[str, object], viewer_id: str | None, role_images: Mapping[int, str]) -> str:
    players = team.get("players")
    if not isinstance(players, list):
        return '<div class="empty">暂无阵容数据</div>'
    output: list[str] = []
    for player in players:
        if not isinstance(player, dict):
            continue
        player_id = str(player.get("playerId", ""))
        target = bool(player.get("isTarget")) or (viewer_id is not None and player_id == viewer_id)
        nickname = player.get("nickname") or "未公开昵称"
        role = player.get("roleName") or player.get("role") or "超弦体未知"
        role_id = _int(player.get("roleId"))
        role_image = role_images.get(role_id, "") if role_id is not None else ""
        if role_image:
            role_avatar = f'<span class="role-art"><img src="{_escape(role_image)}" alt=""></span>'
        else:
            initial = str(role)[:1] or "?"
            role_avatar = f'<span class="role-art is-empty">{_escape(initial)}</span>'

        kills = _int(player.get("kills"))
        assists = _int(player.get("assists"))
        deaths = _int(player.get("deaths"))
        damage = _int(player.get("damage"))
        score = _int(player.get("score"))
        personal_score = _int(player.get("personalScore"))
        strategy_score = _int(player.get("strategyScore"))
        teamwork_score = _int(player.get("teamworkScore"))
        stats = []
        if kills is not None or assists is not None or deaths is not None:
            stats.append(
                f"{kills if kills is not None else '—'}/{assists if assists is not None else '—'}"
                f"/{deaths if deaths is not None else '—'}"
            )
        if damage is not None:
            stats.append(f"{damage:,} 伤害")
        if score is not None:
            stats.append(f"评分 {score}")
        if personal_score is not None:
            stats.append(f"个人 {personal_score}")
        if strategy_score is not None:
            stats.append(f"策略 {strategy_score}")
        if teamwork_score is not None:
            stats.append(f"团队 {teamwork_score}")
        tone = " target" if target else ""
        output.append(
            f'<div class="player{tone}">{role_avatar}<div class="player-main">'
            f'<span class="role">{_escape(role)}</span><span class="name">{_escape(nickname)}</span>'
            f'<span class="stats">{" · ".join(stats) or "暂无个人数据"}</span></div></div>'
        )
    return "".join(output) or '<div class="empty">暂无阵容数据</div>'


def _team_html(
    team: dict[str, object],
    label: str,
    score: int | None,
    viewer_id: str | None,
    role_images: Mapping[int, str],
) -> str:
    score_html = f'<span class="team-score">{score}</span>' if score is not None else ""
    return (
        f'<section class="team"><div class="team-head"><b>{label}</b>{score_html}</div>'
        f"{_player_rows(team, viewer_id, role_images)}</section>"
    )


def _score_label(
    summary: object, ordered_teams: list[tuple[int, dict[str, object], str]], viewer_index: int | None
) -> str:
    scores = [_team_score(team, index, viewer_index, summary) for index, team, _ in ordered_teams]
    my_score = scores[0] if scores else None
    opponent_score = scores[1] if len(scores) > 1 else None
    if my_score is None:
        my_score = _int(_read(summary, "myScore", "viewerScore"))
    if opponent_score is None:
        opponent_score = _int(_read(summary, "opponentScore", "enemyScore"))
    if my_score is None and opponent_score is None:
        score_a, score_b = _summary_team_scores(summary)
        if viewer_index == 1:
            my_score, opponent_score = score_b, score_a
        else:
            my_score, opponent_score = score_a, score_b
    if my_score is None and opponent_score is None:
        return "比分暂无"
    left = str(my_score) if my_score is not None else "—"
    right = str(opponent_score) if opponent_score is not None else "—"
    return f"{left} : {right}"


def render_match_detail_html(
    detail: dict[str, object],
    *,
    room_id: str,
    viewer_id: str | None,
    region: str,
    role_images: Mapping[int, str] | None = None,
) -> str:
    summary = detail.get("summary")
    map_id = _int(_preferred(summary, detail, "mapId", "map_id"))
    map_info = resolve_map(map_id) if map_id is not None else None
    map_name = map_info.name if map_info else (f"地图 {map_id}" if map_id is not None else "地图未知")
    mode = _preferred(summary, detail, "modeLabel", "modeName", "mode") or "模式未知"
    duration = _duration(_preferred(summary, detail, "durationSeconds", "duration", "playTime"))
    played_at = _date_text(_preferred(summary, detail, "playedAt", "timestamp", "time"))
    result_label, result_tone = _result(_preferred(summary, detail, "result", "outcome"))

    teams, viewer_team_index = _ordered_teams(detail.get("teams"), viewer_id)
    role_images = role_images or {}
    team_html = "".join(
        _team_html(
            team,
            label,
            _team_score(team, index, viewer_team_index, summary),
            viewer_id,
            role_images,
        )
        for index, team, label in teams
    )
    if not team_html:
        team_html = '<div class="empty">战绩站暂未提供双方阵容详情</div>'
    score_label = _score_label(summary, teams, viewer_team_index)

    viewer_nickname = ""
    for _, team, _ in teams:
        players = team.get("players")
        if not isinstance(players, list):
            continue
        for player in players:
            if isinstance(player, dict) and (
                player.get("isTarget") or str(player.get("playerId", "")) == str(viewer_id)
            ):
                viewer_nickname = str(player.get("nickname", ""))
                break
        if viewer_nickname:
            break
    viewer_note = f" · 视角 {_escape(viewer_nickname)}" if viewer_nickname else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>对局详情</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:#eceff4;color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:22px 24px 12px;background:linear-gradient(135deg,#f8fafc 0%,#e5ebf4 100%)}}
.header{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:4px 2px 14px}}
.title{{font-size:23px;font-weight:750;color:#263247}}.room{{margin-top:5px;color:#8994a6;font:10px "Mono",monospace}}
.region{{padding:5px 9px;border-radius:7px;background:#edf3ff;color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.summary{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 15px;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.06)}}
.meta{{min-width:0}}.mode{{color:#7a879b;font-size:11px}}.map{{margin-top:3px;color:#344156;font-size:17px;font-weight:750}}
.summary-extra{{display:flex;align-items:center;gap:8px;margin-top:6px;color:#8994a6;font-size:10px}}
.outcome{{padding:3px 7px;border-radius:999px;background:#edf3ff;color:#5573a5;font-weight:700}}
.outcome-win{{background:#e9f6ee;color:#268054}}.outcome-lose{{background:#f9eded;color:#b75a5a}}.outcome-draw{{background:#f4f1e8;color:#907b37}}
.score{{flex:none;color:#263247;font-size:24px;font-weight:750;white-space:nowrap}}.duration{{flex:none;color:#8994a6;font-size:10px;text-align:right;white-space:nowrap}}
.teams{{display:flex;gap:10px;margin-top:12px;align-items:flex-start}}
.team{{flex:1;min-width:0;overflow:hidden;border:1px solid #dce3ec;border-radius:12px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.05)}}
.team-head{{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-bottom:1px solid #edf0f5;color:#344156;font-size:12px;font-weight:700}}
.team-score{{color:#3778e8;font-size:17px}}.team:nth-child(2) .team-score{{color:#c66e72}}
.player{{display:grid;grid-template-columns:48px minmax(0,1fr);align-items:center;gap:8px;padding:7px 9px;border-bottom:1px solid #f0f2f6}}
.player:last-child{{border-bottom:0}}.player.target{{background:#f0f8f3;box-shadow:inset 2px 0 #82b89a}}
.role-art{{display:flex;width:46px;height:54px;align-items:center;justify-content:center;overflow:hidden;border:1px solid #e3e9f1;border-radius:9px;background:linear-gradient(145deg,#f3f6fb,#e5ebf3)}}
.role-art img{{display:block;width:100%;height:100%;object-fit:contain}}.role-art.is-empty{{color:#71829a;font-size:21px;font-weight:700}}
.player-main{{display:flex;min-width:0;flex-direction:column;gap:2px}}
.role{{overflow:hidden;color:#29384d;font-size:14px;font-weight:750;text-overflow:ellipsis;white-space:nowrap}}
.target .role{{color:#286548}}.name{{overflow:hidden;color:#909aaa;font-size:9px;text-overflow:ellipsis;white-space:nowrap}}
.stats{{color:#818da0;font-size:9px;line-height:1.5;overflow-wrap:anywhere}}
.empty{{padding:28px 14px;color:#98a2b2;text-align:center;font-size:12px}}
.footer{{padding-top:10px;color:#929cac;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">对局详情{viewer_note}</div><div class="room">对局编号 {_escape(room_id)}</div></div><div class="region">{_escape(region)}</div></div>
<div class="summary"><div class="meta"><div class="mode">{_escape(mode)}</div><div class="map">{_escape(map_name)}</div><div class="summary-extra"><span class="outcome outcome-{result_tone}">{_escape(result_label)}</span><span>{_escape(played_at)}</span></div></div><div class="score">{_escape(score_label)}</div><div class="duration">时长<br>{_escape(duration)}</div></div>
<div class="teams">{team_html}</div><div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div>
</div></body></html>"""


async def render_match_detail_card(
    detail: dict[str, object],
    *,
    room_id: str,
    viewer_id: str | None,
    region: str,
    role_images: Mapping[int, str] | None = None,
) -> bytes:
    return await render_html_to_bytes(
        render_match_detail_html(
            detail,
            room_id=room_id,
            viewer_id=viewer_id,
            region=region,
            role_images=role_images,
        ),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
