"""全服排行榜静态卡片。"""

import html

from gsuid_core.utils.html_render import render_html_to_bytes

from .summary_card import tier_label

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _int(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _role_name(value: object) -> str:
    if isinstance(value, str):
        return value
    role_names = {
        101: "米雪儿·李", 105: "奥黛丽·格罗夫", 107: "玛德蕾娜·利里", 108: "信", 109: "令",
        110: "白墨", 112: "绯莎", 115: "芙拉薇娅", 119: "艾卡", 120: "珐格兰丝",
        121: "忧雾", 122: "玛拉", 123: "蕾欧娜", 124: "心夏", 125: "千代",
        126: "诺诺", 128: "拉薇", 130: "汐", 131: "伊薇特", 132: "明",
        133: "梅瑞狄斯", 137: "香奈美", 146: "星绘", 205: "加拉蒂亚·利里", 220: "假人",
    }
    if isinstance(value, int) and not isinstance(value, bool):
        return role_names.get(value, f"角色 {value}")
    return "—"


def _entry_html(entry: object, index: int) -> str:
    if not isinstance(entry, dict):
        return ""
    position = _int(entry.get("position"), index + 1)
    nickname = entry.get("nickname") or entry.get("playerName") or entry.get("name") or "未公开昵称"
    segment = entry.get("segment")
    score = entry.get("score")
    stars = entry.get("stars")
    if isinstance(segment, int) and not isinstance(segment, bool):
        rank_value = tier_label(segment)
        if isinstance(stars, int) and stars > 0:
            rank_value += f" · {stars} 星"
    elif isinstance(score, (int, float)) and not isinstance(score, bool):
        rank_value = f"{score:,.0f} 分"
    else:
        rank_value = "—"
    wins = _int(entry.get("wins"))
    games = _int(entry.get("totalGames"), _int(entry.get("games")))
    roles = entry.get("roles")
    role = _role_name(roles[0]) if isinstance(roles, list) and roles else _role_name(entry.get("roleId"))
    delta = entry.get("scoreDelta")
    if isinstance(delta, (int, float)) and not isinstance(delta, bool):
        change = f'<span class="change {"up" if delta >= 0 else "down"}">较昨日 {delta:+,.0f}</span>'
    elif isinstance(entry.get("previousPosition"), int):
        shift = _int(entry.get("previousPosition")) - position
        change = f'<span class="change {"up" if shift >= 0 else "down"}">较昨日 {shift:+d} 位</span>'
    else:
        change = '<span class="change unknown">昨日变化暂无</span>'
    area_parts = [entry.get(key) for key in ("province", "city") if isinstance(entry.get(key), str) and entry[key]]
    area = " · ".join(area_parts) if area_parts else entry.get("region")
    area_html = f'<span class="area">{_escape(area)}</span>' if isinstance(area, str) and area else ""
    return (
        f'<div class="entry"><div class="position">{position:02d}</div>'
        f'<div class="identity"><div class="nickname">{_escape(nickname)}</div>'
        f'<div class="sub">{_escape(rank_value)} · {games} 场 {wins} 胜 · 常用 {_escape(role)}</div></div>'
        f'<div class="side">{change}{area_html}</div></div>'
    )


def render_rankings_html(payload: dict[str, object], *, title: str, season: str, region: str) -> str:
    entries = payload.get("entries")
    rows = "".join(_entry_html(row, index) for index, row in enumerate(entries[:20] if isinstance(entries, list) else []))
    if not rows:
        rows = '<div class="empty">当前条件下暂无榜单数据</div>'
    total = payload.get("total", 0)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>排行榜</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:#eceff4;color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:22px 24px 12px;background:linear-gradient(135deg,#f8fafc 0%,#e5ebf4 100%)}}
.header{{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:4px 2px 14px}}
.title{{font-size:23px;font-weight:750;color:#263247}}
.sub{{margin-top:5px;color:#8691a3;font-size:11px}}
.region{{padding:5px 9px;border-radius:7px;background:#edf3ff;color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.list{{overflow:hidden;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.07)}}
.entry{{display:flex;align-items:center;gap:12px;min-height:54px;padding:7px 13px;border-bottom:1px solid #edf0f5}}
.entry:last-child{{border-bottom:0}}
.position{{width:33px;flex:none;color:#78869a;font:700 16px "Mono",monospace;text-align:center}}
.entry:nth-child(-n+4) .position{{color:#bd8428}}
.identity{{flex:1;min-width:0}}
.nickname{{overflow:hidden;color:#2d394d;font-size:13px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.sub{{overflow:hidden;margin-top:4px;color:#8290a3;font-size:10px;text-overflow:ellipsis;white-space:nowrap}}
.side{{display:flex;flex:none;flex-direction:column;align-items:flex-end;gap:4px;text-align:right}}
.change{{font-size:10px;font-weight:700;white-space:nowrap}}
.change.up{{color:#18834d}}.change.down{{color:#bf4c4c}}.change.unknown{{color:#9aa4b4;font-weight:400}}
.area{{max-width:150px;overflow:hidden;color:#9aa4b4;font-size:9px;text-overflow:ellipsis;white-space:nowrap}}
.empty{{padding:42px 18px;color:#98a2b2;text-align:center;font-size:13px}}
.footer{{padding-top:10px;color:#929cac;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">{_escape(title)}</div><div class="sub">{_escape(season)} · 前 20 名 · 共 {total} 位</div></div><div class="region">{_escape(region)}</div></div>
<div class="list">{rows}</div><div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div>
</div></body></html>"""


async def render_rankings_card(payload: dict[str, object], *, title: str, season: str, region: str) -> bytes:
    return await render_html_to_bytes(
        render_rankings_html(payload, title=title, season=season, region=region),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
