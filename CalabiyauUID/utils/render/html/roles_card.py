"""超弦体排行与地图阵容卡片。"""

import html

from gsuid_core.utils.html_render import render_html_to_bytes

from ...helper.maps import resolve_map

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _number(value: object, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def _role_name(role_id: object, name: object = None) -> str:
    if isinstance(name, str) and name.strip():
        return name.strip()
    names = {
        101: "米雪儿·李", 105: "奥黛丽·格罗夫", 107: "玛德蕾娜·利里", 108: "信", 109: "令",
        110: "白墨", 112: "绯莎", 115: "芙拉薇娅", 119: "艾卡", 120: "珐格兰丝",
        121: "忧雾", 122: "玛拉", 123: "蕾欧娜", 124: "心夏", 125: "千代",
        126: "诺诺", 128: "拉薇", 130: "汐", 131: "伊薇特", 132: "明",
        133: "梅瑞狄斯", 137: "香奈美", 146: "星绘", 205: "加拉蒂亚·利里", 220: "假人",
    }
    return names.get(role_id, f"角色 {role_id}")


def _role_rows(entries: object) -> str:
    if not isinstance(entries, list):
        return ""
    ordered = sorted(entries, key=lambda item: _number(item.get("appearanceRate")) if isinstance(item, dict) else 0, reverse=True)
    rows: list[str] = []
    for position, entry in enumerate(ordered[:20], 1):
        if not isinstance(entry, dict):
            continue
        role_id = entry.get("roleId")
        name = _role_name(role_id, entry.get("name") or entry.get("roleName"))
        games = int(_number(entry.get("games")))
        win_rate = _number(entry.get("winRate")) * 100
        appearance = _number(entry.get("appearanceRate", entry.get("pickRate"))) * 100
        delta_raw = entry.get("appearanceRateDelta", entry.get("pickRateDelta"))
        if isinstance(delta_raw, (int, float)) and not isinstance(delta_raw, bool):
            delta = float(delta_raw) * 100
            delta_html = f'<span class="delta {"up" if delta >= 0 else "down"}">{delta:+.1f}%</span>'
        else:
            delta_html = '<span class="delta unknown">昨日暂无</span>'
        rows.append(
            f'<div class="role-row"><span class="role-pos">{position:02d}</span>'
            f'<span class="role-name">{_escape(name)}</span><span class="role-games">{games} 场</span>'
            f'<span class="role-rate">登场 {appearance:.1f}%</span><span class="role-win">胜率 {win_rate:.1f}%</span>{delta_html}</div>'
        )
    return "".join(rows) or '<div class="empty">暂无角色榜数据</div>'


def _lineup_roles(roles: object) -> str:
    if not isinstance(roles, list):
        return "—"
    names: list[str] = []
    ordered = sorted(
        (item for item in roles if isinstance(item, dict)),
        key=lambda item: _number(item.get("pickRate")),
        reverse=True,
    )
    for item in ordered[:3]:
        names.append(_role_name(item.get("roleId"), item.get("name") or item.get("roleName")))
    return "、".join(names) or "—"


def _map_cards(map_stats: object) -> str:
    if not isinstance(map_stats, list):
        return ""
    cards: list[str] = []
    ordered = sorted(
        (item for item in map_stats if isinstance(item, dict)),
        key=lambda item: int(item.get("games", 0)) if isinstance(item.get("games"), int) else 0,
        reverse=True,
    )
    for item in ordered[:3]:
        map_id = item.get("mapId")
        map_info = resolve_map(map_id) if isinstance(map_id, int) else None
        map_name = map_info.name if map_info else f"地图 {map_id or '未知'}"
        sides = item.get("sides")
        side_lines: list[str] = []
        if isinstance(sides, list):
            for side in sides[:2]:
                if not isinstance(side, dict):
                    continue
                raw_side = str(side.get("side") or side.get("label") or "阵容")
                normalized_side = raw_side.casefold()
                if any(word in normalized_side for word in ("attack", "attacker", "atk", "进攻")):
                    label = "进攻"
                elif any(word in normalized_side for word in ("defen", "def", "防守")):
                    label = "防守"
                else:
                    label = raw_side
                side_lines.append(
                    f'<div class="side-line"><b>{label}</b><span>{_escape(_lineup_roles(side.get("roles")))}</span></div>'
                )
        summary = "".join(side_lines) or '<div class="side-line"><span>暂无攻防阵容摘要</span></div>'
        cards.append(
            f'<div class="map-card"><div class="map-head"><b>{_escape(map_name)}</b>'
            f'<span>{int(_number(item.get("games")))} 场 · {_number(item.get("winRate")) * 100:.1f}% 胜率</span></div>{summary}</div>'
        )
    return "".join(cards) or '<div class="empty">暂无地图阵容数据</div>'


def render_roles_html(payload: dict[str, object], *, region: str, ranked_only: bool) -> str:
    entries = payload.get("entries")
    map_stats = payload.get("mapStats")
    mode_label = "仅排位" if ranked_only else "全部模式"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>超弦体排行</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:#eceff4;color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:22px 24px 12px;background:linear-gradient(135deg,#f8fafc 0%,#e5ebf4 100%)}}
.header{{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:4px 2px 14px}}
.title{{font-size:23px;font-weight:750;color:#263247}}.note{{margin-top:5px;color:#8691a3;font-size:11px}}
.region{{padding:5px 9px;border-radius:7px;background:#edf3ff;color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.panel{{overflow:hidden;margin-bottom:12px;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.06)}}
.panel-head{{display:flex;justify-content:space-between;padding:11px 14px;border-bottom:1px solid #edf0f5;color:#344156;font-size:13px;font-weight:700}}
.panel-head span{{color:#929cac;font-size:10px;font-weight:400}}
.role-list{{padding:2px 12px}}
.role-row{{display:flex;align-items:center;gap:8px;min-height:34px;border-bottom:1px solid #f0f2f6;font-size:10px}}
.role-row:last-child{{border-bottom:0}}.role-pos{{width:21px;color:#a67d39;font:700 11px "Mono",monospace}}
.role-name{{flex:1;min-width:70px;overflow:hidden;color:#344156;font-size:11px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.role-games,.role-rate,.role-win{{width:78px;color:#758297;white-space:nowrap;text-align:right}}
.delta{{width:58px;font-weight:700;text-align:right;white-space:nowrap}}.delta.up{{color:#18834d}}.delta.down{{color:#bf4c4c}}.delta.unknown{{color:#9aa4b4;font-weight:400}}
.maps{{display:grid;grid-template-columns:1fr;gap:7px;padding:10px 12px}}
.map-card{{padding:8px 10px;border:1px solid #edf0f5;border-radius:9px;background:#fbfcfe}}
.map-head{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:5px;color:#364359;font-size:11px}}
.map-head span{{color:#8994a6;font-size:9px;white-space:nowrap}}
.side-line{{display:flex;gap:8px;padding-top:4px;color:#788497;font-size:10px}}
.side-line b{{width:33px;flex:none;color:#68758a}}.empty{{padding:23px;color:#98a2b2;text-align:center;font-size:12px}}
.footer{{padding-top:7px;color:#929cac;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">超弦体榜</div><div class="note">{mode_label} · 按登场率排序 · {len(entries) if isinstance(entries, list) else 0} 名角色</div></div><div class="region">{_escape(region)}</div></div>
<div class="panel"><div class="panel-head">角色排行<span>前 20 名 · 场次 · 登场率 · 胜率 · 较昨日变化</span></div><div class="role-list">{_role_rows(entries)}</div></div>
<div class="panel"><div class="panel-head">地图攻防阵容摘要<span>按对局数最多展示 3 张地图</span></div><div class="maps">{_map_cards(map_stats)}</div></div>
<div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div></div></body></html>"""


async def render_roles_card(payload: dict[str, object], *, region: str, ranked_only: bool) -> bytes:
    return await render_html_to_bytes(
        render_roles_html(payload, region=region, ranked_only=ranked_only),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
