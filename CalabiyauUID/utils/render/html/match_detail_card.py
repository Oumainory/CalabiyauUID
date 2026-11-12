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


def _team_badges(players: list[object]) -> dict[int, tuple[str, str]]:
    explicit: dict[int, tuple[str, str]] = {}
    for index, player in enumerate(players):
        if not isinstance(player, dict):
            continue
        if player.get("mvp"):
            explicit[index] = ("MVP", "mvp")
        elif player.get("svp"):
            explicit[index] = ("SVP", "svp")
    if explicit:
        return explicit

    rated = [
        (score, index)
        for index, player in enumerate(players)
        if isinstance(player, dict)
        if (score := _int(player.get("score"))) is not None
    ]
    if not rated:
        return {}
    highest = max(score for score, _ in rated)
    return {index: ("最高评分", "top") for score, index in rated if score == highest}


def _max_damage(teams: list[tuple[int, dict[str, object], str]]) -> int:
    damages = [
        damage
        for _, team, _ in teams
        for player in (team.get("players") if isinstance(team.get("players"), list) else [])
        if isinstance(player, dict)
        if (damage := _int(player.get("damage"))) is not None
    ]
    return max(damages, default=0)


def _player_rows(
    team: dict[str, object],
    viewer_id: str | None,
    role_images: Mapping[int, str],
    max_damage: int,
) -> str:
    players = team.get("players")
    if not isinstance(players, list):
        return '<div class="empty">暂无阵容数据</div>'
    output: list[str] = []
    badges = _team_badges(players)
    for index, player in enumerate(players):
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
        deaths = _int(player.get("deaths"))
        assists = _int(player.get("assists"))
        damage = _int(player.get("damage"))
        score = _int(player.get("score"))
        personal_score = _int(player.get("personalScore"))
        strategy_score = _int(player.get("strategyScore"))
        teamwork_score = _int(player.get("teamworkScore"))
        badge = badges.get(index)
        badge_html = f'<span class="player-badge badge-{badge[1]}">{badge[0]}</span>' if badge else ""
        damage_text = f"{damage:,}" if damage is not None else "—"
        damage_width = max(0, damage) / max_damage * 100 if damage is not None and max_damage > 0 else 0
        tone = " target" if target else ""
        output.append(
            f'<div class="player{tone}">{role_avatar}<div class="player-main">'
            f'<div class="player-top"><div class="identity"><div class="identity-title">'
            f'<span class="role">{_escape(role)}</span>{badge_html}</div>'
            f'<span class="name">{_escape(nickname)}</span></div>'
            f'<span class="kda"><b>{kills if kills is not None else "—"}</b><i>/</i>'
            f'<b class="death">{deaths if deaths is not None else "—"}</b><i>/</i>'
            f'<b>{assists if assists is not None else "—"}</b></span></div>'
            f'<div class="player-stats">'
            f'<div class="stat"><span>伤害</span><b>{damage_text}</b></div>'
            f'<div class="stat"><span>评分</span><b>{score if score is not None else "—"}</b></div>'
            f'<div class="stat is-secondary"><span>个人</span><b>{personal_score if personal_score is not None else "—"}</b></div>'
            f'<div class="stat is-secondary"><span>策略</span><b>{strategy_score if strategy_score is not None else "—"}</b></div>'
            f'<div class="stat is-secondary"><span>团队</span><b>{teamwork_score if teamwork_score is not None else "—"}</b></div>'
            f'</div><div class="damage-track"><span style="width:{damage_width:.1f}%"></span></div></div></div>'
        )
    return "".join(output) or '<div class="empty">暂无阵容数据</div>'


def _team_html(
    team: dict[str, object],
    label: str,
    score: int | None,
    viewer_id: str | None,
    role_images: Mapping[int, str],
    max_damage: int,
    tone: str,
) -> str:
    score_html = f'<span class="team-score">{score}</span>' if score is not None else ""
    team_name = team.get("label")
    team_name_html = (
        f'<small>{_escape(team_name)}</small>'
        if isinstance(team_name, str) and team_name and team_name != label
        else ""
    )
    return (
        f'<section class="team team-{tone}"><div class="team-head"><div class="team-title">'
        f'<b>{label}</b>{team_name_html}</div>{score_html}</div>'
        f"{_player_rows(team, viewer_id, role_images, max_damage)}</section>"
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
    map_image: str = "",
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
    max_damage = _max_damage(teams)
    team_html = "".join(
        _team_html(
            team,
            label,
            _team_score(team, index, viewer_team_index, summary),
            viewer_id,
            role_images,
            max_damage,
            "own" if position == 0 else "opponent",
        )
        for position, (index, team, label) in enumerate(teams)
    )
    if not team_html:
        team_html = '<div class="empty">战绩站暂未提供双方阵容详情</div>'
    score_label = _score_label(summary, teams, viewer_team_index)
    if " : " in score_label:
        my_score, opponent_score = score_label.split(" : ", 1)
        score_html = (
            f'<span class="score-self">{_escape(my_score)}</span>'
            f'<i>:</i><span class="score-opponent">{_escape(opponent_score)}</span>'
        )
    else:
        score_html = f'<span class="score-missing">{_escape(score_label)}</span>'

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
    viewer_html = f'<span class="hero-viewer">视角 {_escape(viewer_nickname)}</span>' if viewer_nickname else ""
    map_art = (
        f'<div class="hero-art" style="background-image:url(\'{_escape(map_image)}\')"></div>' if map_image else ""
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>对局详情</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
.card{{width:100%;padding:24px;background:linear-gradient(145deg,#f8fafc 0%,#e9eef4 100%)}}
.hero{{position:relative;overflow:hidden;padding:14px 18px 12px;border:1px solid #dce3ec;border-radius:13px;background:#f5f7fa;box-shadow:0 5px 18px rgba(22,26,33,.07)}}
.hero-win{{background:linear-gradient(135deg,#eaf2ff 0%,#f6f8fc 100%)}}
.hero-lose{{background:linear-gradient(135deg,#fff0ef 0%,#fbf7f7 100%)}}
.hero-draw{{background:linear-gradient(135deg,#fbf5e8 0%,#faf8f2 100%)}}
.hero-unknown{{background:linear-gradient(135deg,#eef1f5 0%,#f8fafc 100%)}}
.hero-art,.hero-veil{{position:absolute;inset:0}}
.hero-art{{background-size:cover;background-position:center 30%;background-repeat:no-repeat}}
.hero-veil{{background:rgba(255,255,255,.58)}}
.hero-win .hero-veil{{background:rgba(243,247,255,.58)}}
.hero-lose .hero-veil{{background:rgba(255,245,244,.58)}}
.hero-draw .hero-veil{{background:rgba(255,250,240,.58)}}
.hero-unknown .hero-veil{{background:rgba(255,255,255,.62)}}
.hero-content{{position:relative;z-index:1}}
.hero-top,.hero-main,.hero-bottom{{display:flex;align-items:center;justify-content:space-between;gap:10px}}
.mode{{overflow:hidden;color:#68758a;font-size:12px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.region{{flex:none;padding:4px 8px;border-radius:6px;background:rgba(237,243,255,.88);color:#356fd1;font-size:10px;font-weight:700;white-space:nowrap}}
.hero-main{{margin-top:5px}}
.map{{min-width:0;overflow:hidden;color:#27364a;font-size:25px;font-weight:750;line-height:1.2;text-overflow:ellipsis;white-space:nowrap}}
.score{{display:flex;flex:none;align-items:baseline;gap:8px;margin-left:12px;font-variant-numeric:tabular-nums;white-space:nowrap}}
.score-self,.score-opponent{{font-size:34px;font-weight:800;line-height:1;color:#3778e8}}
.score-opponent{{color:#c66e72}}
.score i{{color:#8390a2;font-size:19px;font-style:normal;font-weight:500}}
.score-missing{{color:#536176;font-size:17px;font-weight:700}}
.hero-bottom{{justify-content:space-between;flex-wrap:wrap;gap:6px 12px;margin-top:10px;color:#68758a;font-size:10.5px}}
.hero-meta,.hero-ids{{display:flex;align-items:center;flex-wrap:wrap;gap:8px;min-width:0}}
.hero-ids{{margin-left:auto}}
.outcome{{padding:3px 8px;border-radius:999px;background:rgba(255,255,255,.75);font-size:10px;font-weight:700}}
.outcome-win{{color:#2563eb}}.outcome-lose{{color:#c62828}}.outcome-draw{{color:#946200}}.outcome-unknown{{color:#6f7c8f}}
.hero-viewer{{color:#68758a;white-space:nowrap}}
.room{{color:#8490a1;font:10px "Mono",Consolas,monospace;white-space:nowrap}}
.teams{{display:flex;align-items:stretch;gap:12px;margin-top:12px}}
.team{{display:flex;flex:1;min-width:0;flex-direction:column;overflow:hidden;border:1px solid #dce3ec;border-left:4px solid var(--team-accent);border-radius:12px;box-shadow:0 5px 16px rgba(22,26,33,.05)}}
.team-own{{--team-accent:#4b8ef0;--team-tint:rgba(75,142,240,.12);background:linear-gradient(145deg,#f5f9ff 0%,#edf3fc 100%)}}
.team-opponent{{--team-accent:#e2453c;--team-tint:rgba(226,69,60,.11);background:linear-gradient(145deg,#fff8f7 0%,#f8efee 100%)}}
.team-head{{display:flex;align-items:center;justify-content:space-between;min-height:38px;padding:8px 12px;border-bottom:1px solid rgba(216,224,234,.85);background:rgba(255,255,255,.4)}}
.team-title{{display:flex;align-items:baseline;gap:7px;min-width:0;color:#344156;font-size:12px}}
.team-title b{{color:var(--team-accent);font-size:13px}}
.team-title small{{overflow:hidden;color:#8793a4;font-size:9px;text-overflow:ellipsis;white-space:nowrap}}
.team-score{{color:var(--team-accent);font-size:19px;font-weight:800;font-variant-numeric:tabular-nums}}
.player{{display:grid;grid-template-columns:60px minmax(0,1fr);align-items:center;gap:8px;min-height:84px;padding:6px 8px;border-bottom:1px solid rgba(221,227,235,.8)}}
.player:last-child{{border-bottom:0}}
.player.target{{box-shadow:inset 3px 0 var(--team-accent),inset 0 0 0 1px var(--team-tint);background:linear-gradient(90deg,var(--team-tint),rgba(255,255,255,.22) 70%)}}
.role-art{{display:flex;width:60px;height:72px;align-items:center;justify-content:center;overflow:hidden;border:1px solid #e3e9f1;border-radius:8px;background:linear-gradient(145deg,#f3f6fb,#e5ebf3);box-shadow:0 2px 6px rgba(39,55,80,.08)}}
.role-art img{{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}}
.role-art.is-empty{{color:#71829a;font-size:23px;font-weight:700}}
.player-main{{display:flex;min-width:0;flex-direction:column;gap:4px}}
.player-top{{display:flex;align-items:center;justify-content:space-between;gap:5px;min-width:0}}
.identity{{display:flex;min-width:0;flex-direction:column;gap:1px}}
.identity-title{{display:flex;align-items:center;gap:4px;min-width:0}}
.role{{overflow:hidden;color:#29384d;font-size:12px;font-weight:750;text-overflow:ellipsis;white-space:nowrap}}
.name{{overflow:hidden;color:#778397;font-size:9.5px;text-overflow:ellipsis;white-space:nowrap}}
.kda{{display:flex;flex:none;align-items:baseline;gap:2px;color:#26364b;font-size:15px;font-weight:800;font-variant-numeric:tabular-nums;white-space:nowrap}}
.kda i{{color:#8a96a7;font-size:11px;font-style:normal;font-weight:500}}
.kda .death{{color:#c62828}}
.player-badge{{flex:none;padding:1px 4px;border-radius:4px;color:#fff;font-size:8px;font-weight:700;line-height:12px;white-space:nowrap}}
.badge-mvp{{background:#b8862c}}.badge-svp{{background:#4b8ef0}}.badge-top{{background:#7f8fa5}}
.player-stats{{display:grid;grid-template-columns:1.1fr .8fr repeat(3,minmax(0,1fr));gap:3px;min-width:0}}
.stat{{display:flex;min-width:0;flex-direction:column;gap:1px}}
.stat span{{color:#7b8798;font-size:8px;line-height:1.1;white-space:nowrap}}
.stat b{{overflow:hidden;color:#344156;font-size:10px;font-weight:700;font-variant-numeric:tabular-nums;text-overflow:ellipsis;white-space:nowrap}}
.stat.is-secondary span{{color:#929cad}}
.stat.is-secondary b{{color:#778397;font-size:9px;font-weight:600}}
.damage-track{{height:3px;overflow:hidden;border-radius:3px;background:rgba(128,145,166,.17)}}
.damage-track span{{display:block;height:100%;border-radius:3px;background:var(--team-accent);opacity:.8}}
.empty{{display:flex;flex:1;align-items:center;justify-content:center;min-height:90px;padding:20px 12px;color:#8a96a7;text-align:center;font-size:11px}}
.footer{{padding-top:10px;color:#7c8799;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<section class="hero hero-{result_tone}">{map_art}<div class="hero-veil"></div><div class="hero-content">
<div class="hero-top"><span class="mode">{_escape(mode)}</span><span class="region">{_escape(region)}</span></div>
<div class="hero-main"><div class="map">{_escape(map_name)}</div><div class="score">{score_html}</div></div>
<div class="hero-bottom"><div class="hero-meta"><span class="outcome outcome-{result_tone}">{_escape(result_label)}</span>
<span>{_escape(played_at)}</span><span>时长 {_escape(duration)}</span></div><div class="hero-ids">{viewer_html}<span class="room">对局编号 {_escape(room_id)}</span></div></div>
</div></section>
<div class="teams">{team_html}</div><div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div>
</div></body></html>"""


async def render_match_detail_card(
    detail: dict[str, object],
    *,
    room_id: str,
    viewer_id: str | None,
    region: str,
    role_images: Mapping[int, str] | None = None,
    map_image: str = "",
) -> bytes:
    return await render_html_to_bytes(
        render_match_detail_html(
            detail,
            room_id=room_id,
            viewer_id=viewer_id,
            region=region,
            role_images=role_images,
            map_image=map_image,
        ),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
