"""超弦体排行与地图阵容卡片。"""

import html
from collections.abc import Mapping

from gsuid_core.utils.html_render import render_html_to_bytes

from ...helper.maps import resolve_map

_CARD_WIDTH = 760
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


def _number(value: object, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def _role_name(role_id: object, name: object = None) -> str:
    if isinstance(name, str) and name.strip():
        return name.strip()
    if isinstance(role_id, int) and not isinstance(role_id, bool):
        return _ROLE_NAMES.get(role_id, "角色信息暂不可用")
    return "角色信息暂不可用"


def _role_image(role_id: object, role_images: Mapping[int, str]) -> str:
    return role_images.get(role_id, "") if isinstance(role_id, int) and not isinstance(role_id, bool) else ""


def _portrait(role_id: object, name: str, role_images: Mapping[int, str], *, mini: bool = False) -> str:
    image = _role_image(role_id, role_images)
    class_name = "lineup-portrait" if mini else "role-portrait"
    if image:
        return f'<span class="{class_name}"><img src="{_escape(image)}" alt=""></span>'
    initial = name[:1] or "?"
    return f'<span class="{class_name} is-empty">{_escape(initial)}</span>'


def _rate(value: object) -> float | None:
    return _number(value) * 100 if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _role_rows(entries: object, role_images: Mapping[int, str]) -> str:
    if not isinstance(entries, list):
        return '<div class="empty">暂无角色榜数据</div>'
    ordered = sorted(
        (item for item in entries if isinstance(item, dict)),
        key=lambda item: _number(item.get("appearanceRate", item.get("pickRate"))),
        reverse=True,
    )
    rows: list[str] = []
    for position, entry in enumerate(ordered[:20], 1):
        role_id = entry.get("roleId")
        name = _role_name(role_id, entry.get("name") or entry.get("roleName"))
        games = entry.get("games")
        games_text = f"{games:,}" if isinstance(games, int) and not isinstance(games, bool) else "—"
        win_rate = _rate(entry.get("winRate"))
        appearance = _rate(entry.get("appearanceRate", entry.get("pickRate")))
        appearance_text = f"{appearance:.1f}%" if appearance is not None else "—"
        win_text = f"{win_rate:.1f}%" if win_rate is not None else "—"
        delta_raw = entry.get("appearanceRateDelta", entry.get("pickRateDelta"))
        if isinstance(delta_raw, (int, float)) and not isinstance(delta_raw, bool):
            delta = float(delta_raw) * 100
            delta_html = f'<span class="delta {"up" if delta >= 0 else "down"}">{delta:+.1f}%</span>'
        else:
            delta_html = '<span class="delta unknown">昨日暂无</span>'
        appearance_width = max(0, min(100, appearance or 0))
        win_width = max(0, min(100, win_rate or 0))
        art = _role_image(role_id, role_images)
        art_html = f'<img class="row-art" src="{_escape(art)}" alt="">' if position <= 3 and art else ""
        rows.append(
            f'<article class="role-row rank-{position if position <= 3 else "other"}">{art_html}'
            f'<span class="role-pos">{position:02d}</span>{_portrait(role_id, name, role_images)}'
            f'<div class="role-name">{_escape(name)}</div>'
            f'<div class="role-stat"><b>{games_text}</b><span>场次</span></div>'
            f'<div class="role-stat rate-stat"><b>{appearance_text}</b><span class="rate-track"><i style="width:{appearance_width:.1f}%"></i></span><span>登场率</span></div>'
            f'<div class="role-stat rate-stat"><b>{win_text}</b><span class="rate-track win-track"><i style="width:{win_width:.1f}%"></i></span><span>胜率</span></div>'
            f'{delta_html}</article>'
        )
    return "".join(rows) or '<div class="empty">暂无角色榜数据</div>'


def _lineup_roles(roles: object, role_images: Mapping[int, str]) -> str:
    if not isinstance(roles, list):
        return '<span class="lineup-empty">阵容暂不可用</span>'
    ordered = sorted(
        (item for item in roles if isinstance(item, dict)),
        key=lambda item: _number(item.get("pickRate")),
        reverse=True,
    )
    items: list[str] = []
    for item in ordered[:3]:
        role_id = item.get("roleId")
        name = _role_name(role_id, item.get("name") or item.get("roleName"))
        games = item.get("games")
        win_rate = _rate(item.get("winRate"))
        details: list[str] = []
        if isinstance(games, int) and not isinstance(games, bool):
            details.append(f"{games:,} 场")
        if win_rate is not None:
            details.append(f"{win_rate:.1f}% 胜率")
        detail_html = f'<small>{_escape(" · ".join(details))}</small>' if details else ""
        items.append(
            f'<div class="lineup-role">{_portrait(role_id, name, role_images, mini=True)}'
            f'<span class="lineup-name">{_escape(name)}{detail_html}</span></div>'
        )
    return "".join(items) or '<span class="lineup-empty">暂无阵容角色</span>'


def _map_cards(
    map_stats: object,
    role_images: Mapping[int, str],
    map_images: Mapping[str, str],
) -> str:
    if not isinstance(map_stats, list):
        return '<div class="empty">暂无地图阵容数据</div>'
    ordered = sorted(
        (item for item in map_stats if isinstance(item, dict)),
        key=lambda item: item.get("games", 0) if isinstance(item.get("games"), int) else 0,
        reverse=True,
    )
    cards: list[str] = []
    for item in ordered[:3]:
        map_id = item.get("mapId")
        map_info = resolve_map(map_id) if isinstance(map_id, int) and not isinstance(map_id, bool) else None
        map_name = map_info.name if map_info else "未知地图"
        games = item.get("games")
        games_text = f"{games:,} 场" if isinstance(games, int) and not isinstance(games, bool) else "场次暂无"
        win_rate = _rate(item.get("winRate"))
        rate_text = f"{win_rate:.1f}% 胜率" if win_rate is not None else "胜率暂无"
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
                    f'<div class="side-group"><b>{_escape(label)}</b>'
                    f'<div class="lineup-roles">{_lineup_roles(side.get("roles"), role_images)}</div></div>'
                )
        sides_html = "".join(side_lines) or '<div class="lineup-empty">暂无攻防阵容摘要</div>'
        map_image = map_images.get(map_info.slug, "") if map_info is not None else ""
        map_art = (f'<img class="map-art" src="{_escape(map_image)}" alt="">' if map_image else "") + '<div class="map-veil"></div>'
        cards.append(
            f'<article class="map-card">{map_art}<div class="map-head"><b>{_escape(map_name)}</b>'
            f'<span>{games_text} · {rate_text}</span></div>{sides_html}</article>'
        )
    return "".join(cards) or '<div class="empty">暂无地图阵容数据</div>'


def render_roles_html(
    payload: dict[str, object],
    *,
    region: str,
    ranked_only: bool,
    role_images: Mapping[int, str] | None = None,
    map_images: Mapping[str, str] | None = None,
    banner_image: str = "",
) -> str:
    entries = payload.get("entries")
    map_stats = payload.get("mapStats")
    mode_label = "仅排位" if ranked_only else "全部模式"
    entry_count = len(entries) if isinstance(entries, list) else 0
    images = role_images or {}
    maps = map_images or {}
    banner_html = (f'<img class="banner-art" src="{_escape(banner_image)}" alt="">' if banner_image else "") + '<div class="banner-veil"></div>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>超弦体排行</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:radial-gradient(ellipse at 8% 0%,rgba(109,153,208,.2),transparent 36%),radial-gradient(ellipse at 92% 20%,rgba(232,189,131,.14),transparent 28%),linear-gradient(145deg,#e3eaf3,#d8e2ee 52%,#e9edf3);color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:20px 24px 12px;background:repeating-linear-gradient(135deg,rgba(95,123,158,.025) 0,rgba(95,123,158,.025) 1px,transparent 1px,transparent 8px),linear-gradient(145deg,rgba(248,250,253,.88),rgba(225,233,243,.82))}}
.header{{position:relative;isolation:isolate;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:104px;margin-bottom:13px;padding:17px 19px;overflow:hidden;border:1px solid rgba(255,255,255,.84);border-radius:14px;background:linear-gradient(120deg,#dce6f0,#cad8e7 55%,#e9e2d8);box-shadow:0 8px 22px rgba(39,55,80,.1)}}
.banner-art{{position:absolute;inset:0;z-index:-2;width:100%;height:100%;object-fit:cover;object-position:center 46%;opacity:.96}}
.banner-veil{{position:absolute;left:0;top:0;bottom:0;z-index:-1;width:47%;max-width:400px;background:linear-gradient(90deg,rgba(245,248,252,.9) 0%,rgba(245,248,252,.78) 60%,rgba(245,248,252,0) 100%)}}
.title{{font-size:23px;font-weight:750;color:#263247}}.note{{margin-top:5px;color:#536375;font-size:11px}}
.region{{padding:5px 9px;border:1px solid rgba(255,255,255,.8);border-radius:7px;background:rgba(232,241,255,.92);color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.panel{{overflow:hidden;margin-bottom:12px;border:1px solid #cad6e4;border-radius:14px;background:linear-gradient(155deg,rgba(246,249,252,.84),rgba(222,231,241,.78));box-shadow:0 8px 24px rgba(39,55,80,.09)}}
.panel-head{{display:flex;justify-content:space-between;gap:8px;padding:11px 14px;border-bottom:1px solid #e1e7ef;color:#344156;font-size:13px;font-weight:700}}
.panel-head span{{color:#8491a3;font-size:9px;font-weight:400;text-align:right}}
.role-list{{padding:3px 10px}}
.role-row{{position:relative;isolation:isolate;display:grid;grid-template-columns:24px 43px minmax(105px,1fr) 54px 76px 70px 50px;align-items:center;gap:7px;min-height:51px;padding:4px 4px;border-bottom:1px solid #dce5ef;overflow:hidden}}
.row-art{{position:absolute;inset:0;z-index:0;width:100%;height:100%;object-fit:cover;object-position:center 24%;opacity:.74}}
.role-row::before{{position:absolute;inset:0;z-index:1;content:"";background:rgba(246,249,252,.72)}}
.role-row.rank-1{{min-height:62px;box-shadow:inset 4px 0 #d5aa49}}.role-row.rank-2{{min-height:60px;box-shadow:inset 4px 0 #9da9b8}}.role-row.rank-3{{min-height:58px;box-shadow:inset 4px 0 #bd805c}}
.role-row.rank-1::before{{background:rgba(255,250,232,.68)}}.role-row.rank-2::before{{background:rgba(246,248,251,.7)}}.role-row.rank-3::before{{background:rgba(255,243,235,.68)}}
.role-row>*:not(.row-art){{position:relative;z-index:2}}
.role-row:last-child{{border-bottom:0}}
.role-pos{{color:#77869b;font:700 10px "Mono",monospace;text-align:center}}.rank-1 .role-pos{{color:#bd8728}}.rank-2 .role-pos{{color:#7c8797}}.rank-3 .role-pos{{color:#a96b4d}}
.role-portrait{{display:flex;width:39px;height:44px;align-items:flex-end;justify-content:center;overflow:hidden;border-radius:7px;background:#dce5ef;color:#65758a;font-size:15px;font-weight:700}}
.role-portrait img{{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}}
.role-name{{min-width:0;overflow:hidden;color:#344156;font-size:11px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.role-stat{{display:flex;flex-direction:column;align-items:flex-end;color:#8491a3;text-align:right}}
.role-stat b{{color:#35445b;font-size:10px;font-variant-numeric:tabular-nums;white-space:nowrap}}
.role-stat>span:last-child{{font-size:8px}}
.rate-track{{display:block;width:44px;height:3px;margin:2px 0 1px;overflow:hidden;border-radius:3px;background:#dce5ef}}
.rate-track i{{display:block;height:100%;border-radius:3px;background:#4e8fe8}}.win-track i{{background:#41a47b}}
.delta{{color:#7e8ba0;font-size:9px;font-weight:600;text-align:right;white-space:nowrap}}.delta.up{{color:#18834d}}.delta.down{{color:#bf4c4c}}.delta.unknown{{color:#9aa4b2;font-weight:400}}
.maps{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;padding:10px}}
.map-card{{position:relative;isolation:isolate;min-width:0;padding:9px 10px;overflow:hidden;border:1px solid rgba(255,255,255,.85);border-radius:10px;background:linear-gradient(145deg,#dce6f0,#eef3f8);box-shadow:0 3px 9px rgba(49,67,91,.08)}}
.map-art{{position:absolute;inset:0;z-index:-2;width:100%;height:100%;object-fit:cover;object-position:center 46%;opacity:.92}}
.map-veil{{position:absolute;inset:0;z-index:-1;background:rgba(244,248,252,.52)}}
.map-card>*:not(.map-art){{position:relative}}
.map-head{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:7px;color:#364359;font-size:11px}}
.map-head span{{color:#8491a3;font-size:8px;text-align:right;white-space:nowrap}}
.side-group{{display:flex;align-items:flex-start;gap:7px;padding:4px 0;border-top:1px solid #e3e9f0}}
.side-group>b{{width:28px;flex:none;padding-top:5px;color:#60718a;font-size:9px}}
.lineup-roles{{display:flex;flex:1;flex-wrap:wrap;gap:5px;min-width:0}}
.lineup-role{{display:flex;align-items:center;gap:4px;min-width:88px;max-width:100%;padding:3px 5px;border:1px solid #e1e8f0;border-radius:7px;background:rgba(255,255,255,.58)}}
.lineup-portrait{{display:flex;width:25px;height:29px;flex:none;align-items:center;justify-content:center;overflow:hidden;border-radius:5px;background:#dce5ef;color:#65758a;font-size:10px;font-weight:700}}
.lineup-portrait img{{display:block;width:100%;height:100%;object-fit:cover;object-position:center top}}
.lineup-name{{display:flex;flex-direction:column;min-width:0;overflow:hidden;color:#42516a;font-size:8px;font-weight:650;text-overflow:ellipsis;white-space:nowrap}}
.lineup-name small{{margin-top:2px;color:#8d99aa;font-size:7px;font-weight:400}}
.lineup-empty{{padding:5px 0;color:#97a2b2;font-size:9px}}
.empty{{padding:23px;color:#7f8da1;text-align:center;font-size:12px}}
.footer{{padding-top:7px;color:#78869a;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header">{banner_html}<div><div class="title">超弦体榜</div><div class="note">{mode_label} · 按登场率排序 · {entry_count} 名角色</div></div><div class="region">{_escape(region)}</div></div>
<div class="panel"><div class="panel-head">角色排行<span>前 20 名 · 场次 · 登场率 · 胜率 · 较昨日变化</span></div><div class="role-list">{_role_rows(entries, images)}</div></div>
<div class="panel"><div class="panel-head">地图攻防阵容摘要<span>按对局数最多展示 3 张地图</span></div><div class="maps">{_map_cards(map_stats, images, maps)}</div></div>
<div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div></div></body></html>"""


async def render_roles_card(
    payload: dict[str, object],
    *,
    region: str,
    ranked_only: bool,
    role_images: Mapping[int, str] | None = None,
    map_images: Mapping[str, str] | None = None,
    banner_image: str = "",
) -> bytes:
    return await render_html_to_bytes(
        render_roles_html(
            payload,
            region=region,
            ranked_only=ranked_only,
            role_images=role_images,
            map_images=map_images,
            banner_image=banner_image,
        ),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
