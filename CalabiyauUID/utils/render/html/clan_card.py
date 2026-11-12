"""战队资料静态卡片。"""

import html

from gsuid_core.utils.html_render import render_html_to_bytes

_CARD_WIDTH = 760


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _members_html(payload: dict[str, object] | None) -> str:
    if payload is None:
        return '<div class="empty">成员列表暂不可用</div>'
    members = payload.get("members")
    if not isinstance(members, list):
        data = payload.get("data")
        members = data.get("members") if isinstance(data, dict) else []
    if not isinstance(members, list) or not members:
        if payload.get("refreshing") is True:
            return '<div class="empty">成员列表正在更新，请稍后重试</div>'
        return '<div class="empty">暂无可展示的成员</div>'
    rows: list[str] = []
    for index, member in enumerate(members[:32], 1):
        if not isinstance(member, dict):
            continue
        nickname = member.get("nickname") or member.get("name") or "未公开昵称"
        level = member.get("level")
        position = member.get("position") or member.get("title") or member.get("role")
        is_leader = bool(member.get("isLeader") or member.get("leader"))
        meta = []
        if isinstance(level, int) and not isinstance(level, bool):
            meta.append(f"Lv.{level}")
        if isinstance(position, int) and not isinstance(position, bool):
            meta.append("队长" if position == 1 else f"位置 {position}")
        elif isinstance(position, str) and position:
            meta.append(position)
        if is_leader and "队长" not in meta:
            meta.append("队长")
        rows.append(
            f'<div class="member"><span class="member-pos">{index:02d}</span>'
            f'<span class="member-name">{_escape(nickname)}</span>'
            f'<span class="member-meta">{_escape(" · ".join(meta) or "成员")}</span></div>'
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


def render_clan_html(clan: dict[str, object], members: dict[str, object] | None, *, region: str) -> str:
    name = clan.get("name") or "未命名战队"
    clan_id = clan.get("clanId") or "—"
    level = clan.get("level", "—")
    member_count = clan.get("memberCount", "—")
    intro = clan.get("intro") or "暂无简介"
    extra = _recruit_text(clan)
    recruit_html = "".join(f'<span class="tag">{_escape(item)}</span>' for item in extra)
    listed_count = members.get("total", members.get("memberCount", members.get("count"))) if members else None
    count_label = f"共 {listed_count} 人" if isinstance(listed_count, int) else f"{member_count} 人"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>战队查询</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:100%;background:#eceff4;color:#172033;font-family:"MiSans","Microsoft YaHei",sans-serif}}
.card{{width:100%;padding:22px 24px 12px;background:linear-gradient(135deg,#f8fafc 0%,#e5ebf4 100%)}}
.header{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:4px 2px 14px}}
.title{{font-size:23px;font-weight:750;color:#263247}}.id{{margin-top:5px;color:#8994a6;font:11px "Mono",monospace}}
.region{{padding:5px 9px;border-radius:7px;background:#edf3ff;color:#356fd1;font-size:11px;font-weight:700;white-space:nowrap}}
.overview{{padding:14px 16px;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.06)}}
.stats{{display:flex;gap:20px;margin-bottom:10px;color:#778498;font-size:11px}}.stats b{{color:#354258;font-size:15px}}
.intro{{padding-top:10px;border-top:1px solid #edf0f5;color:#566379;font-size:12px;line-height:1.6;white-space:pre-wrap}}
.tags{{display:flex;gap:6px;margin-top:9px}}.tag{{padding:4px 7px;border-radius:6px;background:#fff3e8;color:#a76222;font-size:10px}}
.members{{overflow:hidden;margin-top:12px;border:1px solid #dce3ec;border-radius:14px;background:#fff;box-shadow:0 8px 24px rgba(39,55,80,.06)}}
.members-head{{display:flex;justify-content:space-between;padding:11px 14px;border-bottom:1px solid #edf0f5;color:#344156;font-size:13px;font-weight:700}}
.members-head span{{color:#929cac;font-size:10px;font-weight:400}}
.member{{display:flex;align-items:center;gap:10px;min-height:31px;padding:5px 13px;border-bottom:1px solid #f0f2f6;font-size:10px}}.member:last-child{{border-bottom:0}}
.member-pos{{width:22px;flex:none;color:#a67d39;font:700 10px "Mono",monospace}}.member-name{{flex:1;min-width:0;overflow:hidden;color:#344156;font-weight:650;text-overflow:ellipsis;white-space:nowrap}}
.member-meta{{color:#8994a6;white-space:nowrap}}.empty{{padding:24px;color:#98a2b2;text-align:center;font-size:12px}}
.footer{{padding-top:10px;color:#929cac;font-size:10px;text-align:center}}
</style></head><body><div class="card">
<div class="header"><div><div class="title">{_escape(name)}</div><div class="id">战队 ID {_escape(clan_id)}</div></div><div class="region">{_escape(region)}</div></div>
<div class="overview"><div class="stats"><span>等级 <b>{_escape(level)}</b></span><span>{_escape(count_label)}</span></div>
<div class="intro">{_escape(intro)}</div><div class="tags">{recruit_html}</div></div>
<div class="members"><div class="members-head">成员列表<span>最多展示 32 位</span></div>{_members_html(members)}</div>
<div class="footer">Data by 白泉幽奈 · Dakanu</div></div></body></html>"""


async def render_clan_card(clan: dict[str, object], members: dict[str, object] | None, *, region: str) -> bytes:
    return await render_html_to_bytes(
        render_clan_html(clan, members, region=region),
        max_width=1520,
        dpi=192,
        root_max_width=_CARD_WIDTH,
        default_font_size=14,
        allow_refit=True,
        image_format="png",
        lang="zh",
    )
