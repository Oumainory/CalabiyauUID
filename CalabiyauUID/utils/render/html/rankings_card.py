"""全服排行榜卡片。"""

import html
from collections.abc import Mapping

from gsuid_core.utils.html_render import render_html_to_bytes

from .summary_card import tier_label

_CARD_WIDTH = 760
_METRIC_LABELS = {1: "段位分", 2: "胜场", 6: "击杀", 7: "挑战分", 8: "伤害"}
_ROLE_NAMES = {
    101: "米雪儿·李",
    105: "奥黛丽·格罗夫",
    107: "玛德蕾娜·利里",
    108: "信",
    109: "令",
    110: "白墨",
    112: "绯莎",
    115: "芙拉薇娅",
    119: "艾卡",
    120: "珐格兰丝",
    121: "忧雾",
    122: "玛拉",
    123: "蕾欧娜",
    124: "心夏",
    125: "千代",
    126: "诺诺",
    128: "拉薇",
    130: "汐",
    131: "伊薇特",
    132: "明",
    133: "梅瑞狄斯",
    137: "香奈美",
    146: "星绘",
    205: "加拉蒂亚·利里",
    220: "假人",
}


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _number(value: object) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _format_number(value: object) -> str:
    number = _number(value)
    return f"{number:,.0f}" if number is not None else "—"


def _role_details(entry: dict[str, object]) -> tuple[int | None, str]:
    roles = entry.get("roles")
    role: object = roles[0] if isinstance(roles, list) and roles else entry.get("roleId")
    if isinstance(role, dict):
        role_id = _int(role.get("roleId"))
        name = role.get("name") or role.get("roleName")
    else:
        role_id = _int(role)
        name = role if isinstance(role, str) else None
    if isinstance(name, str) and name.strip():
        return role_id, name.strip()
    return role_id, _ROLE_NAMES.get(role_id, "常用角色")


def _avatar_html(entry: dict[str, object], avatar_images: Mapping[int, str], nickname: object) -> str:
    avatar_id = _int(entry.get("avatarId"))
    image = avatar_images.get(avatar_id, "") if avatar_id is not None else ""
    if image:
        content = f'<img src="{_escape(image)}" alt="">'
    else:
        initial = str(nickname)[:1] or "?"
        content = f'<span>{_escape(initial)}</span>'
    return f'<span class="avatar">{content}</span>'


def _metric_html(entry: dict[str, object], ranking_type: int, metric_label: str) -> str:
    score = entry.get("score")
    if ranking_type == 1:
        segment = _int(entry.get("segment"))
        tier = tier_label(segment) if segment is not None else "未定级"
        stars = _int(entry.get("stars"))
        if stars is not None and stars > 0:
            tier += f" · {stars} 星"
        label = metric_label or "段位分"
        return (
            f'<span class="tier">{_escape(tier)}</span>'
            f'<b class="metric-value">{_format_number(score)}</b>'
            f'<span class="metric-label">{_escape(label)}</span>'
        )
    if ranking_type == 2 and score is None:
        score = entry.get("wins")
    label = metric_label or _METRIC_LABELS.get(ranking_type, "积分")
    return f'<b class="metric-value">{_format_number(score)}</b><span class="metric-label">{_escape(label)}</span>'


def _record_html(entry: dict[str, object], ranking_type: int) -> str:
    values: list[str] = []
    games = _int(entry.get("totalGames"))
    if games is None:
        games = _int(entry.get("games"))
    wins = _int(entry.get("wins"))
    if ranking_type == 2:
        if games is not None:
            values.append(f'<span><b>{games:,}</b><em>场</em></span>')
    else:
        if wins is not None:
            values.append(f'<span><b>{wins:,}</b><em>胜</em></span>')
        if games is not None:
            values.append(f'<span><b>{games:,}</b><em>场</em></span>')
    return f'<div class="record">{"".join(values)}</div>' if values else '<div class="record"></div>'


def _change_html(entry: dict[str, object], position: int) -> str:
    delta = _number(entry.get("scoreDelta"))
    if delta is not None:
        tone = "up" if delta >= 0 else "down"
        change = f'<span class="change {tone}">较昨日 {delta:+,.0f}</span>'
    else:
        previous = _int(entry.get("previousPosition"))
        if previous is None:
            change = '<span class="change unknown">昨日暂无</span>'
        else:
            shift = previous - position
            tone = "up" if shift >= 0 else "down"
            change = f'<span class="change {tone}">较昨日 {shift:+d} 位</span>'
    area_parts = [
        entry.get(key)
        for key in ("province", "city")
        if isinstance(entry.get(key), str) and entry[key].strip()
    ]
    area = " · ".join(area_parts) if area_parts else entry.get("region")
    area_html = f'<span class="area">{_escape(area)}</span>' if isinstance(area, str) and area else ""
    return f'<div class="side">{change}{area_html}</div>'


def _entry_html(
    entry: object,
    index: int,
    *,
    ranking_type: int,
    metric_label: str,
    avatar_images: Mapping[int, str],
    role_images: Mapping[int, str],
) -> str:
    if not isinstance(entry, dict):
        return ""
    position = _int(entry.get("position")) or index + 1
    nickname = entry.get("nickname") or entry.get("playerName") or entry.get("name") or "未公开昵称"
    level = _int(entry.get("level"))
    level_html = f'<span class="level">Lv.{level}</span>' if level is not None else ""
    avatar = _avatar_html(entry, avatar_images, nickname)
    role_id, role_name = _role_details(entry)
    role_image = role_images.get(role_id, "") if role_id is not None else ""
    role_html = (
        f'<span class="role-image"><img src="{_escape(role_image)}" alt=""></span>' if role_image else ""
    )
    return (
        f'<article class="entry rank-{position if position <= 3 else "other"}">'
        f'<span class="position">{position:02d}</span>{avatar}'
        f'<div class="identity"><div class="nickname">{_escape(nickname)}{level_html}</div>'
        f'<div class="role">{role_html}<span>{_escape(role_name)}</span></div></div>'
        f'<div class="metric">{_metric_html(entry, ranking_type, metric_label)}</div>'
        f'{_record_html(entry, ranking_type)}{_change_html(entry, position)}</article>'
    )


def render_rankings_html(
    payload: dict[str, object],
    *,
    title: str,
    season: str,
    region: str,
    ranking_type: int = 1,
    avatar_images: Mapping[int, str] | None = None,
    role_images: Mapping[int, str] | None = None,
) -> str:
    entries = payload.get("entries")
    visible_entries = entries[:20] if isinstance(entries, list) else []
    avatars = avatar_images or {}
    roles = role_images or {}
    rank_type = payload.get("rankType")
    payload_title = rank_type.get("label") if isinstance(rank_type, dict) else None
    display_title = payload_title if isinstance(payload_title, str) and payload_title.strip() else title
    raw_metric_label = payload.get("metricLabel")
    metric_label = raw_metric_label if isinstance(raw_metric_label, str) and raw_metric_label.strip() else _METRIC_LABELS.get(ranking_type, "积分")
    rows = "".join(
        _entry_html(
            row,
            index,
            ranking_type=ranking_type,
            metric_label=metric_label,
            avatar_images=avatars,
            role_images=roles,
        )
        for index, row in enumerate(visible_entries)
    )
    if not rows:
        rows = '<div class="empty">当前条件下暂无榜单数据</div>'
    total = _int(payload.get("total"))
    if total is None:
        total = len(entries) if isinstance(entries, list) else 0
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>排行榜</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:#e9eef4;color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:22px 24px 12px;background:linear-gradient(135deg,#f8fafc 0%,#e9eef4 100%)}}
.header{{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:4px 2px 14px}}
.title{{font-size:23px;font-weight:750;color:#263247}}
.sub{{margin-top:5px;color:#77869b;font-size:11px}}
.region{{padding:5px 9px;border-radius:7px;background:#edf3ff;color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.list{{overflow:hidden;border:1px solid #d5deea;border-radius:14px;background:linear-gradient(155deg,#f7f9fc 0%,#edf2f7 100%);box-shadow:0 8px 24px rgba(39,55,80,.07)}}
.entry{{display:flex;align-items:center;gap:9px;min-height:53px;padding:6px 11px;border-bottom:1px solid #e3e9f0;background:rgba(255,255,255,.24)}}
.entry:nth-child(even){{background:rgba(220,230,242,.28)}}.entry:last-child{{border-bottom:0}}
.position{{width:28px;flex:none;color:#77869b;font:700 14px "Mono",monospace;text-align:center}}
.rank-1 .position{{color:#bd8728}}.rank-2 .position{{color:#7c8797}}.rank-3 .position{{color:#a96b4d}}
.avatar{{display:flex;width:37px;height:37px;flex:none;align-items:center;justify-content:center;overflow:hidden;border:2px solid rgba(255,255,255,.9);border-radius:50%;background:#dce5ef;color:#53657b;font-size:13px;font-weight:700;box-shadow:0 2px 6px rgba(40,56,78,.14)}}
.avatar img{{display:block;width:100%;height:100%;object-fit:cover}}
.identity{{flex:1;min-width:0}}
.nickname{{display:flex;align-items:center;gap:6px;overflow:hidden;color:#2d394d;font-size:12px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.level{{flex:none;padding:1px 4px;border-radius:4px;background:#e8edf4;color:#8491a3;font-size:8px;font-weight:600}}
.role{{display:flex;align-items:center;gap:4px;min-width:0;margin-top:3px;color:#78869a;font-size:9px}}
.role>span:last-child{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.role-image{{display:flex;width:18px;height:21px;flex:none;overflow:hidden;border-radius:4px;background:#dfe7f0}}
.role-image img{{width:100%;height:100%;object-fit:cover;object-position:center top}}
.metric{{display:flex;width:132px;flex:none;flex-direction:column;align-items:flex-end;gap:1px;text-align:right}}
.tier{{color:#465a76;font-size:10px;font-weight:700;white-space:nowrap}}
.metric-value{{color:#253852;font-size:16px;font-weight:750;line-height:1.05;font-variant-numeric:tabular-nums;white-space:nowrap}}
.metric-label{{color:#8996a8;font-size:8px;white-space:nowrap}}
.record{{display:flex;width:71px;flex:none;flex-direction:column;align-items:flex-end;gap:2px;color:#66768d;font-variant-numeric:tabular-nums}}
.record span{{display:flex;gap:4px;align-items:baseline;white-space:nowrap}}
.record b{{font-size:10px;font-weight:700}}.record em{{color:#96a1b0;font-size:8px;font-style:normal}}
.side{{display:flex;width:91px;flex:none;flex-direction:column;align-items:flex-end;gap:3px;text-align:right}}
.change{{font-size:9px;font-weight:700;white-space:nowrap}}.change.up{{color:#18834d}}.change.down{{color:#bf4c4c}}.change.unknown{{color:#99a3b1;font-weight:400}}
.area{{max-width:90px;overflow:hidden;color:#9aa4b2;font-size:8px;text-overflow:ellipsis;white-space:nowrap}}
.empty{{padding:42px 18px;color:#7f8da1;text-align:center;font-size:13px}}
.footer{{padding-top:10px;color:#78869a;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">{_escape(display_title)}</div><div class="sub">{_escape(season)} · 前 {len(visible_entries)} 名 / 共 {total} 位 · {len(visible_entries)} 条榜单记录</div></div><div class="region">{_escape(region)}</div></div>
<div class="list">{rows}</div><div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div>
</div></body></html>"""


async def render_rankings_card(
    payload: dict[str, object],
    *,
    title: str,
    season: str,
    region: str,
    ranking_type: int = 1,
    avatar_images: Mapping[int, str] | None = None,
    role_images: Mapping[int, str] | None = None,
) -> bytes:
    return await render_html_to_bytes(
        render_rankings_html(
            payload,
            title=title,
            season=season,
            region=region,
            ranking_type=ranking_type,
            avatar_images=avatar_images,
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
