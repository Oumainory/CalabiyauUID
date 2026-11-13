"""全服常组队组合榜卡片。"""

import html
from collections.abc import Mapping

from gsuid_core.utils.html_render import render_html_to_bytes

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _number(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _avatar(avatar_id: object, nickname: object, avatar_images: Mapping[int, str]) -> str:
    image = avatar_images.get(avatar_id, "") if isinstance(avatar_id, int) and not isinstance(avatar_id, bool) else ""
    if image:
        body = f'<img src="{_escape(image)}" alt="">'
    else:
        body = f'<span>{_escape(str(nickname)[:1] or "?")}</span>'
    return f'<span class="avatar">{body}</span>'


def _record_stat(value: object, label: str) -> str:
    number = _number(value)
    displayed = f"{number:,}" if number is not None else "—"
    return f'<span class="record-stat"><b>{displayed}</b><em>{label}</em></span>'


def _rows(entries: object, avatar_images: Mapping[int, str]) -> str:
    if not isinstance(entries, list):
        return '<div class="empty">暂无达到条件的组队组合</div>'
    output: list[str] = []
    for index, entry in enumerate(entries[:20], 1):
        if not isinstance(entry, dict):
            continue
        position = _number(entry.get("position")) or index
        nickname_a = entry.get("nicknameA") or "未公开昵称"
        nickname_b = entry.get("nicknameB") or "未公开昵称"
        rate = entry.get("winRate")
        win_rate = float(rate) * 100 if isinstance(rate, (int, float)) and not isinstance(rate, bool) else None
        rate_text = f"{win_rate:.1f}%" if win_rate is not None else "—"
        rate_width = max(0, min(100, win_rate or 0))
        output.append(
            f'<article class="entry rank-{position if position <= 3 else "other"}">'
            f'<span class="pos">{position:02d}</span>'
            f'<div class="duo">'
            f'<div class="partner">{_avatar(entry.get("avatarA"), nickname_a, avatar_images)}'
            f'<span class="name">{_escape(nickname_a)}</span></div>'
            '<span class="plus">＋</span>'
            f'<div class="partner">{_avatar(entry.get("avatarB"), nickname_b, avatar_images)}'
            f'<span class="name">{_escape(nickname_b)}</span></div></div>'
            '<div class="records">'
            f'{_record_stat(entry.get("games"), "场")}'
            f'{_record_stat(entry.get("wins"), "胜")}'
            f'{_record_stat(entry.get("losses"), "负")}'
            f'{_record_stat(entry.get("draws"), "平")}'
            '</div>'
            f'<div class="rate"><b>{rate_text}</b><span>组队胜率</span>'
            f'<i><em style="width:{rate_width:.1f}%"></em></i></div></article>'
        )
    return "".join(output) or '<div class="empty">暂无达到条件的组队组合</div>'


def render_friends_html(
    payload: dict[str, object],
    *,
    region: str,
    avatar_images: Mapping[int, str] | None = None,
    banner_image: str = "",
) -> str:
    entries = payload.get("entries")
    total = _number(payload.get("total"))
    total = total if total is not None else len(entries) if isinstance(entries, list) else 0
    images = avatar_images or {}
    banner_html = (f'<img class="banner-art" src="{_escape(banner_image)}" alt="">' if banner_image else "") + '<div class="banner-veil"></div>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>好友榜</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:radial-gradient(ellipse at 8% 0%,rgba(109,153,208,.2),transparent 36%),radial-gradient(ellipse at 92% 20%,rgba(232,189,131,.14),transparent 28%),linear-gradient(145deg,#e3eaf3,#d8e2ee 52%,#e9edf3);color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:20px 24px 12px;background:repeating-linear-gradient(135deg,rgba(95,123,158,.025) 0,rgba(95,123,158,.025) 1px,transparent 1px,transparent 8px),linear-gradient(145deg,rgba(248,250,253,.88),rgba(225,233,243,.82))}}
.header{{position:relative;isolation:isolate;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:104px;margin-bottom:13px;padding:17px 19px;overflow:hidden;border:1px solid rgba(255,255,255,.84);border-radius:14px;background:linear-gradient(120deg,#dce6f0,#cad8e7 55%,#e9e2d8);box-shadow:0 8px 22px rgba(39,55,80,.1)}}
.banner-art{{position:absolute;inset:0;z-index:-2;width:100%;height:100%;object-fit:cover;object-position:center 48%;opacity:.96}}
.banner-veil{{position:absolute;left:0;top:0;bottom:0;z-index:-1;width:47%;max-width:400px;background:linear-gradient(90deg,rgba(245,248,252,.9) 0%,rgba(245,248,252,.78) 60%,rgba(245,248,252,0) 100%)}}
.title{{font-size:23px;font-weight:750;color:#263247}}.note{{margin-top:5px;color:#536375;font-size:11px}}
.region{{padding:5px 9px;border:1px solid rgba(255,255,255,.8);border-radius:7px;background:rgba(232,241,255,.92);color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.list{{overflow:hidden;border:1px solid #cbd6e3;border-radius:14px;background:linear-gradient(155deg,rgba(245,248,252,.82),rgba(218,228,239,.72));box-shadow:0 8px 24px rgba(39,55,80,.1)}}
.entry{{position:relative;display:flex;align-items:center;gap:9px;min-height:65px;padding:7px 11px;border-bottom:1px solid rgba(202,214,228,.82);background:rgba(255,255,255,.39)}}
.entry:nth-child(even){{background:rgba(218,229,241,.4)}}.entry:last-child{{border-bottom:0}}
.entry.rank-1{{min-height:71px;box-shadow:inset 4px 0 #d5aa49;background:rgba(255,250,232,.73)}}.entry.rank-2{{min-height:69px;box-shadow:inset 4px 0 #9da9b8;background:rgba(246,248,251,.76)}}.entry.rank-3{{min-height:67px;box-shadow:inset 4px 0 #bd805c;background:rgba(255,243,235,.74)}}
.pos{{width:28px;flex:none;color:#77869b;font:700 14px "Mono",monospace;text-align:center}}
.rank-1 .pos{{color:#bd8728}}.rank-2 .pos{{color:#7c8797}}.rank-3 .pos{{color:#a96b4d}}
.duo{{display:flex;flex:1;align-items:center;gap:7px;min-width:0}}
.partner{{display:flex;flex:1;align-items:center;gap:6px;min-width:0}}
.avatar{{display:flex;width:37px;height:37px;flex:none;align-items:center;justify-content:center;overflow:hidden;border:2px solid rgba(255,255,255,.9);border-radius:50%;background:#dce5ef;color:#53657b;font-size:13px;font-weight:700;box-shadow:0 2px 6px rgba(40,56,78,.14)}}
.avatar img{{display:block;width:100%;height:100%;object-fit:cover}}
.name{{min-width:0;overflow:hidden;color:#344156;font-size:11px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}}
.plus{{flex:none;color:#8a98ab;font-size:13px;font-weight:700}}
.records{{display:grid;width:176px;flex:none;grid-template-columns:repeat(4,minmax(0,1fr));gap:3px}}
.record-stat{{display:flex;flex-direction:column;align-items:center;gap:2px}}
.record-stat b{{color:#35445b;font-size:11px;font-variant-numeric:tabular-nums}}
.record-stat em{{color:#8d99aa;font-size:8px;font-style:normal}}
.rate{{display:flex;width:83px;flex:none;flex-direction:column;align-items:flex-end;text-align:right}}
.rate>b{{color:#28744d;font-size:17px;font-variant-numeric:tabular-nums;line-height:1.05}}
.rate>span{{margin-top:2px;color:#8491a3;font-size:8px}}
.rate>i{{display:block;width:54px;height:3px;margin-top:5px;overflow:hidden;border-radius:3px;background:#dce5e7}}
.rate>i>em{{display:block;height:100%;border-radius:3px;background:#40a47b}}
.empty{{padding:42px 18px;color:#7f8da1;text-align:center;font-size:13px}}
.footer{{padding-top:10px;color:#78869a;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header">{banner_html}<div><div class="title">好友榜</div><div class="note">全服组队组合 · 至少一起玩 10 场 · 按场次排序 · 共 {total} 组</div></div><div class="region">{_escape(region)}</div></div>
<div class="list">{_rows(entries, images)}</div><div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div>
</div></body></html>"""


async def render_friends_card(
    payload: dict[str, object],
    *,
    region: str,
    avatar_images: Mapping[int, str] | None = None,
    banner_image: str = "",
) -> bytes:
    return await render_html_to_bytes(
        render_friends_html(payload, region=region, avatar_images=avatar_images, banner_image=banner_image),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
