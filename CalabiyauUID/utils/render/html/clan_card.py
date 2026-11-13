"""战队资料卡片。"""

import html
from collections.abc import Mapping

from gsuid_core.utils.html_render import render_html_to_bytes

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _member_list(payload: dict[str, object] | None) -> list[object]:
    if payload is None:
        return []
    members = payload.get("members")
    if not isinstance(members, list):
        data = payload.get("data")
        members = data.get("members") if isinstance(data, dict) else []
    return members if isinstance(members, list) else []


def _avatar(member: dict[str, object], avatar_images: Mapping[int, str]) -> str:
    avatar_id = member.get("avatarId")
    image = avatar_images.get(avatar_id, "") if isinstance(avatar_id, int) and not isinstance(avatar_id, bool) else ""
    if image:
        content = f'<img src="{_escape(image)}" alt="">'
    else:
        nickname = member.get("nickname") or member.get("name") or "未公开昵称"
        content = f'<span>{_escape(str(nickname)[:1] or "?")}</span>'
    return f'<span class="member-avatar">{content}</span>'


def _members_html(
    payload: dict[str, object] | None,
    avatar_images: Mapping[int, str],
) -> str:
    if payload is None:
        return '<div class="empty">成员列表暂不可用</div>'
    members = _member_list(payload)
    if not members:
        if payload.get("refreshing") is True:
            return '<div class="empty">成员列表正在更新，请稍后重试</div>'
        return '<div class="empty">暂无可展示的成员</div>'
    rows: list[str] = []
    for member in members[:32]:
        if not isinstance(member, dict):
            continue
        nickname = member.get("nickname") or member.get("name") or "未公开昵称"
        level = member.get("level")
        level_text = f"Lv.{level}" if isinstance(level, int) and not isinstance(level, bool) else "—"
        position = member.get("position")
        position_is_leader = isinstance(position, int) and not isinstance(position, bool) and position == 1
        is_leader = member.get("isLeader") is True or member.get("leader") is True or position_is_leader
        leader = '<span class="leader">队长</span>' if is_leader else ""
        rows.append(
            f'<article class="member">{_avatar(member, avatar_images)}'
            f'<div class="member-name">{_escape(nickname)}{leader}</div>'
            f'<span class="member-level">{level_text}</span></article>'
        )
    return "".join(rows) or '<div class="empty">暂无可展示的成员</div>'


def _recruit_text(clan: dict[str, object]) -> list[str]:
    values: list[str] = []
    for key, label in (
        ("recruitment", "招募"),
        ("recruiting", "招募"),
        ("recruitStatus", "招募"),
        ("recruitmentStatus", "招募"),
        ("isRecruiting", "招募"),
    ):
        value = clan.get(key)
        if isinstance(value, bool):
            values.append(f"{label}{'开放' if value else '关闭'}")
            break
        if isinstance(value, str) and value.strip():
            values.append(f"{label}{value.strip()}")
            break
        if isinstance(value, dict):
            status = value.get("status") or value.get("label") or value.get("text")
            if isinstance(status, str) and status.strip():
                values.append(f"{label}{status.strip()}")
                break
            opened = value.get("open", value.get("enabled"))
            if isinstance(opened, bool):
                values.append(f"{label}{'开放' if opened else '关闭'}")
                break
    for key in ("rankRequirement", "rankLimit", "minRank", "requiredRank", "rankRestriction"):
        value = clan.get(key)
        if isinstance(value, dict):
            value = value.get("label") or value.get("name") or value.get("tier")
        if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value).strip():
            values.append(f"段位限制 {value}")
            break
    return values


def _count_label(clan: dict[str, object], members: dict[str, object] | None) -> str:
    listed_count = None
    if members is not None:
        for key in ("total", "memberCount", "count"):
            value = members.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                listed_count = value
                break
    if listed_count is None and members is not None and _member_list(members):
        listed_count = len(_member_list(members))
    if listed_count is None:
        listed_count = clan.get("memberCount")
    if isinstance(listed_count, int) and not isinstance(listed_count, bool):
        return f"{listed_count} 人"
    return "人数暂不可用"


def render_clan_html(
    clan: dict[str, object],
    members: dict[str, object] | None,
    *,
    region: str,
    avatar_images: Mapping[int, str] | None = None,
    banner_image: str = "",
) -> str:
    name = clan.get("name") or "未命名战队"
    clan_id = clan.get("clanId") or clan.get("id") or "—"
    level = clan.get("level")
    level_text = f"Lv.{level}" if isinstance(level, int) and not isinstance(level, bool) else "等级暂不可用"
    intro = clan.get("intro") or "暂无简介"
    extra = _recruit_text(clan)
    recruit_html = "".join(f'<span class="tag">{_escape(item)}</span>' for item in extra)
    count_label = _count_label(clan, members)
    images = avatar_images or {}
    banner_html = (f'<img class="banner-art" src="{_escape(banner_image)}" alt="">' if banner_image else "") + '<div class="banner-veil"></div>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>战队查询</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:radial-gradient(ellipse at 8% 0%,rgba(109,153,208,.2),transparent 36%),radial-gradient(ellipse at 92% 20%,rgba(232,189,131,.14),transparent 28%),linear-gradient(145deg,#e3eaf3,#d8e2ee 52%,#e9edf3);color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:20px 24px 12px;background:repeating-linear-gradient(135deg,rgba(95,123,158,.025) 0,rgba(95,123,158,.025) 1px,transparent 1px,transparent 8px),linear-gradient(145deg,rgba(248,250,253,.88),rgba(225,233,243,.82))}}
.header{{position:relative;isolation:isolate;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:124px;margin-bottom:13px;padding:20px;overflow:hidden;border:1px solid rgba(255,255,255,.84);border-radius:14px;background:linear-gradient(120deg,#dce6f0,#cad8e7 55%,#e9e2d8);box-shadow:0 8px 22px rgba(39,55,80,.1)}}
.banner-art{{position:absolute;inset:0;z-index:-2;width:100%;height:100%;object-fit:cover;object-position:center 48%;opacity:.9}}
.banner-veil{{position:absolute;inset:0;z-index:-1;background:linear-gradient(90deg,rgba(245,248,252,.9) 0%,rgba(245,248,252,.66) 46%,rgba(245,248,252,.42) 100%)}}
.title{{color:#263247;font-size:23px;font-weight:750;line-height:1.2;overflow-wrap:anywhere}}
.id{{margin-top:6px;color:#66768b;font:10px "Mono",monospace}}
.region{{padding:5px 9px;border:1px solid rgba(255,255,255,.8);border-radius:7px;background:rgba(232,241,255,.92);color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.overview{{padding:14px 16px;border:1px solid #cad6e4;border-radius:14px;background:linear-gradient(145deg,rgba(247,250,253,.86),rgba(221,231,241,.78));box-shadow:0 8px 24px rgba(39,55,80,.08)}}
.stats{{display:flex;gap:10px;margin-bottom:10px}}
.stat{{display:flex;align-items:baseline;gap:5px;padding:6px 9px;border:1px solid #dfe6ef;border-radius:8px;background:rgba(255,255,255,.52);color:#748297;font-size:9px}}
.stat b{{color:#354258;font-size:14px;font-variant-numeric:tabular-nums}}
.intro{{padding-top:10px;border-top:1px solid #e0e7ef;color:#566379;font-size:12px;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}}.tag{{padding:4px 7px;border-radius:6px;background:#fff3e8;color:#a76222;font-size:9px}}
.members{{overflow:hidden;margin-top:12px;border:1px solid #cad6e4;border-radius:14px;background:linear-gradient(155deg,rgba(246,249,252,.84),rgba(219,229,239,.78));box-shadow:0 8px 24px rgba(39,55,80,.08)}}
.members-head{{display:flex;justify-content:space-between;padding:11px 14px;border-bottom:1px solid #e1e7ef;color:#344156;font-size:13px;font-weight:700}}
.members-head span{{color:#8491a3;font-size:9px;font-weight:400}}
.member{{display:flex;align-items:center;gap:10px;min-height:42px;padding:5px 13px;border-bottom:1px solid rgba(202,214,228,.82);background:rgba(255,255,255,.39)}}
.member:nth-child(even){{background:rgba(218,229,241,.4)}}.member:last-child{{border-bottom:0}}
.member-avatar{{display:flex;width:31px;height:31px;flex:none;align-items:center;justify-content:center;overflow:hidden;border:2px solid rgba(255,255,255,.9);border-radius:50%;background:#dce5ef;color:#53657b;font-size:11px;font-weight:700;box-shadow:0 2px 5px rgba(40,56,78,.12)}}
.member-avatar img{{display:block;width:100%;height:100%;object-fit:cover}}
.member-name{{display:flex;flex:1;align-items:center;gap:7px;min-width:0;overflow:hidden;color:#344156;font-size:11px;font-weight:650;text-overflow:ellipsis;white-space:nowrap}}
.leader{{flex:none;padding:2px 5px;border-radius:4px;background:#f3e6c7;color:#91671d;font-size:8px;font-weight:700}}
.member-level{{width:66px;flex:none;color:#60718a;font-size:10px;font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}}
.empty{{padding:24px;color:#7f8da1;text-align:center;font-size:12px}}
.footer{{padding-top:10px;color:#78869a;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header">{banner_html}<div><div class="title">{_escape(name)}</div><div class="id">战队 ID {_escape(clan_id)}</div></div><div class="region">{_escape(region)}</div></div>
<div class="overview"><div class="stats"><span class="stat">等级 <b>{_escape(level_text)}</b></span><span class="stat">成员 <b>{_escape(count_label)}</b></span></div>
<div class="intro">{_escape(intro)}</div><div class="tags">{recruit_html}</div></div>
<div class="members"><div class="members-head">成员列表<span>最多展示 32 位</span></div>{_members_html(members, images)}</div>
<div class="footer">Created &amp; Power by GsCore &amp; Design by Oumainory &amp; Data by 白泉幽奈</div></div></body></html>"""


async def render_clan_card(
    clan: dict[str, object],
    members: dict[str, object] | None,
    *,
    region: str,
    avatar_images: Mapping[int, str] | None = None,
    banner_image: str = "",
) -> bytes:
    return await render_html_to_bytes(
        render_clan_html(
            clan,
            members,
            region=region,
            avatar_images=avatar_images,
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
