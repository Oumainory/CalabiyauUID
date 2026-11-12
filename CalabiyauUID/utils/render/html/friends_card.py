"""全服常组队组合榜静态卡片。"""

import html

from gsuid_core.utils.html_render import render_html_to_bytes

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _number(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _rows(entries: object) -> str:
    if not isinstance(entries, list):
        return ""
    output: list[str] = []
    for index, entry in enumerate(entries[:20], 1):
        if not isinstance(entry, dict):
            continue
        nickname_a = entry.get("nicknameA") or "未公开昵称"
        nickname_b = entry.get("nicknameB") or "未公开昵称"
        games = _number(entry.get("games"))
        wins = _number(entry.get("wins"))
        losses = _number(entry.get("losses"))
        draws = _number(entry.get("draws"))
        rate = entry.get("winRate")
        win_rate = float(rate) * 100 if isinstance(rate, (int, float)) and not isinstance(rate, bool) else 0
        output.append(
            f'<div class="entry"><div class="pos">{index:02d}</div><div class="duo">'
            f'<div class="names"><b>{_escape(nickname_a)}</b><span>＋</span><b>{_escape(nickname_b)}</b></div>'
            f'<div class="record">{games} 场 · {wins} 胜 {losses} 负 {draws} 平</div></div>'
            f'<div class="rate"><b>{win_rate:.1f}%</b><span>组队胜率</span></div></div>'
        )
    return "".join(output) or '<div class="empty">暂无达到条件的组队组合</div>'


def render_friends_html(payload: dict[str, object], *, region: str) -> str:
    entries = payload.get("entries")
    total = payload.get("total", 0)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>好友榜</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:#eceff4;color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:22px 24px 12px;background:linear-gradient(135deg,#f8fafc 0%,#e5ebf4 100%)}}
.header{{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;padding:4px 2px 14px}}
.title{{font-size:23px;font-weight:750;color:#263247}}.note{{margin-top:5px;color:#8691a3;font-size:11px}}
.region{{padding:5px 9px;border-radius:7px;background:#edf3ff;color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.list{{overflow:hidden;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.07)}}
.entry{{display:flex;align-items:center;gap:12px;min-height:55px;padding:8px 14px;border-bottom:1px solid #edf0f5}}.entry:last-child{{border-bottom:0}}
.pos{{width:28px;flex:none;color:#a67d39;font:700 14px "Mono",monospace;text-align:center}}
.duo{{flex:1;min-width:0}}.names{{display:flex;align-items:center;gap:7px;overflow:hidden;font-size:12px;white-space:nowrap}}
.names b{{overflow:hidden;color:#344156;text-overflow:ellipsis}}.names span{{color:#97a1b1}}
.record{{margin-top:4px;color:#8994a6;font-size:10px}}
.rate{{width:83px;flex:none;text-align:right}}.rate b{{display:block;color:#28744d;font-size:17px}}.rate span{{color:#929cac;font-size:9px}}
.empty{{padding:42px 18px;color:#98a2b2;text-align:center;font-size:13px}}
.footer{{padding-top:10px;color:#929cac;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">好友榜</div><div class="note">全服组队组合 · 至少一起玩 10 场 · 按场次排序 · 共 {total} 组</div></div><div class="region">{_escape(region)}</div></div>
<div class="list">{_rows(entries)}</div><div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div>
</div></body></html>"""


async def render_friends_card(payload: dict[str, object], *, region: str) -> bytes:
    return await render_html_to_bytes(
        render_friends_html(payload, region=region),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
