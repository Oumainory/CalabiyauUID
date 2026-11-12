"""指定单场对局详情静态卡片。"""

import html

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
        if value is not None:
            return value
    return None


def _duration(value: object) -> str:
    seconds = _int(value)
    if seconds is None or seconds <= 0:
        return "时长未知"
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _player_rows(team: object, viewer_id: str | None) -> str:
    if not isinstance(team, dict):
        return ""
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
            stats.append(f"{kills if kills is not None else '—'}/{assists if assists is not None else '—'}/{deaths if deaths is not None else '—'}")
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
            f'<div class="player{tone}"><span class="name">{_escape(nickname)}</span>'
            f'<span class="role">{_escape(role)}</span><span class="stats">{" · ".join(stats) or "暂无个人数据"}</span></div>'
        )
    return "".join(output) or '<div class="empty">暂无阵容数据</div>'


def _team_html(team: object, index: int, viewer_id: str | None) -> str:
    if not isinstance(team, dict):
        return ""
    label = team.get("label") or f"队伍 {index + 1}"
    score = _int(team.get("score"))
    score_html = f'<span class="team-score">{score}</span>' if score is not None else ""
    return (
        f'<section class="team"><div class="team-head"><b>{_escape(label)}</b>{score_html}</div>'
        f'{_player_rows(team, viewer_id)}</section>'
    )


def render_match_detail_html(detail: dict[str, object], *, room_id: str, viewer_id: str | None, region: str) -> str:
    summary = detail.get("summary")
    map_id = _int(_read(summary, "mapId", "map_id") or detail.get("mapId"))
    map_info = resolve_map(map_id) if map_id is not None else None
    map_name = map_info.name if map_info else (f"地图 {map_id}" if map_id is not None else "地图未知")
    mode = _read(summary, "modeLabel", "modeName", "mode") or detail.get("modeLabel") or "模式未知"
    duration = _duration(_read(summary, "durationSeconds", "duration", "playTime") or detail.get("durationSeconds"))

    score_a = _int(_read(summary, "teamAScore", "scoreA", "blueScore", "leftScore"))
    score_b = _int(_read(summary, "teamBScore", "scoreB", "redScore", "rightScore"))
    if score_a is None:
        score_a = _int(_read(summary, "myScore", "viewerScore"))
    if score_b is None:
        score_b = _int(_read(summary, "opponentScore", "enemyScore"))
    if score_a is not None and score_b is not None:
        score_label = f"{score_a} : {score_b}"
    else:
        scores = _read(summary, "scores", "teamScores")
        score_label = " : ".join(str(_int(value)) for value in scores[:2]) if isinstance(scores, list) and len(scores) >= 2 else "比分暂无"

    teams = detail.get("teams")
    team_html = "".join(_team_html(team, index, viewer_id) for index, team in enumerate(teams) if index < 2) if isinstance(teams, list) else ""
    if not team_html:
        team_html = '<div class="empty">战绩站暂未提供双方阵容详情</div>'
    viewer_nickname = ""
    if isinstance(teams, list):
        for team in teams:
            if not isinstance(team, dict) or not isinstance(team.get("players"), list):
                continue
            for player in team["players"]:
                if isinstance(player, dict) and (player.get("isTarget") or str(player.get("playerId", "")) == str(viewer_id)):
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
.summary{{display:flex;align-items:center;justify-content:space-between;gap:9px;padding:13px 15px;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.06)}}
.meta{{min-width:0}}.mode{{color:#7a879b;font-size:11px}}.map{{margin-top:4px;color:#344156;font-size:16px;font-weight:700}}
.score{{flex:none;color:#263247;font-size:24px;font-weight:750;white-space:nowrap}}.duration{{color:#8994a6;font-size:10px;text-align:right}}
.teams{{display:flex;gap:10px;margin-top:12px;align-items:flex-start}}
.team{{flex:1;min-width:0;overflow:hidden;border:1px solid #dce3ec;border-radius:12px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.05)}}
.team-head{{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-bottom:1px solid #edf0f5;color:#344156;font-size:12px;font-weight:700}}
.team-score{{color:#3778e8;font-size:17px}}.player{{display:flex;flex-wrap:wrap;align-items:center;gap:4px 7px;padding:7px 10px;border-bottom:1px solid #f0f2f6;font-size:10px}}
.player:last-child{{border-bottom:0}}.player.target{{background:#f0f8f3}}
.name{{max-width:120px;overflow:hidden;color:#344156;font-size:11px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.target .name{{color:#18784a}}.role{{color:#7f8ca0;white-space:nowrap}}.stats{{width:100%;color:#8994a6;font-size:9px;white-space:normal}}
.empty{{padding:28px 14px;color:#98a2b2;text-align:center;font-size:12px}}
.footer{{padding-top:10px;color:#929cac;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">对局详情{viewer_note}</div><div class="room">对局编号 {_escape(room_id)}</div></div><div class="region">{_escape(region)}</div></div>
<div class="summary"><div class="meta"><div class="mode">{_escape(mode)}</div><div class="map">{_escape(map_name)}</div></div><div class="score">{_escape(score_label)}</div><div class="duration">时长<br>{_escape(duration)}</div></div>
<div class="teams">{team_html}</div><div class="footer">Data by 白泉幽奈 · Dakanu</div>
</div></body></html>"""


async def render_match_detail_card(
    detail: dict[str, object], *, room_id: str, viewer_id: str | None, region: str
) -> bytes:
    return await render_html_to_bytes(
        render_match_detail_html(detail, room_id=room_id, viewer_id=viewer_id, region=region),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
