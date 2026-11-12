"""战绩总览的账号解析、本地快照读取与渲染编排。"""

import re
import base64
from copy import deepcopy
from pathlib import Path

from gsuid_core.models import Event

from ..utils.api.dakanu import DakanuError, role_image_url, fetch_season_data, fetch_ranking_seasons
from ..utils.downloader import resolve_image
from ..utils.helper.assets import (
    local_role_image,
    local_tier_image,
    local_frame_image,
    local_medal_image,
    local_avatar_image,
    local_baseplate_image,
    local_challenge_tier_image,
)
from ..utils.helper.refresh import refresh_player_data
from ..utils.helper.player_data import PlayerSnapshot, load_player_snapshot
from ..utils.helper.resolve_player import resolve_player_query_context
from ..utils.render.html.summary_card import (
    SummaryAssets,
    tier_index,
    render_summary_card,
    challenge_tier_index,
)


async def resolve_player_id(ev: Event, *, raw_text: str | None = None) -> tuple[str, str, str | None]:
    """按 UID、昵称、@ 用户、当前账号的顺序解析查询目标。"""
    return await resolve_player_query_context(ev, allow_at=True, raw_text=raw_text)


def extract_season_tag(raw_text: str) -> tuple[str, str | None]:
    match = re.search(r"(?<!\S)(S\d+EP\d+)(?!\S)", raw_text, re.IGNORECASE)
    if match is None:
        return raw_text, None
    cleaned = f"{raw_text[:match.start()]} {raw_text[match.end():]}".strip()
    return " ".join(cleaned.split()), match.group(1).upper()


async def ensure_player_snapshot(player_id: str, *, refresh: bool = False, region: str = "cn") -> PlayerSnapshot:
    return (await refresh_player_data(player_id, force=refresh, region=region)).snapshot


async def render_snapshot_card(
    snapshot: PlayerSnapshot,
    *,
    season_id: int | None = None,
    season_label: str | None = None,
    region: str | None = None,
) -> bytes:
    region = region or snapshot.region
    profile = snapshot.profile
    leisure = snapshot.leisure
    if season_id is None and leisure is None:
        try:
            current_season = await fetch_season_data(profile["player"]["id"], 0, region=region)
        except DakanuError:
            current_season = None
        season_leisure = current_season.get("leisure") if current_season is not None else None
        if isinstance(season_leisure, dict):
            leisure = _normalize_season_leisure(season_leisure)
    if season_id is not None:
        season = await fetch_season_data(profile["player"]["id"], season_id, region=region)
        if season is None:
            label = season_label or f"赛季 ID {season_id}"
            raise DakanuError(f"没有找到 {label} 的生涯数据。该赛季可能尚未收录或站点暂时不可用。")
        profile, leisure = _season_profile(profile, season, season_label)
    avatar_id = profile["player"]["avatarId"]
    avatar_url = f"https://www.dakanu.com/avatars/{avatar_id}.webp"
    baseplate_url = f"https://www.dakanu.com/baseplates-lg/{avatar_id}.webp"
    frame_url = f"https://www.dakanu.com/frames-pc/{profile['player']['borderId']}.webp"
    avatar_path = await resolve_image(avatar_url, local_avatar_image(avatar_id))
    baseplate_path = await resolve_image(baseplate_url, local_baseplate_image(avatar_id))
    frame_path = await resolve_image(frame_url, local_frame_image(profile["player"]["borderId"]))
    rank_tier = tier_index(profile["rank"]["segment"])
    top_tier = tier_index(profile["rank"]["topSegment"])
    tier_path = local_tier_image(rank_tier) if rank_tier else None
    top_tier_path = local_tier_image(top_tier) if top_tier else None
    challenge_tier = challenge_tier_index(leisure["segment"]) if leisure is not None and "segment" in leisure else 0
    challenge_path = local_challenge_tier_image(challenge_tier) if challenge_tier else None
    if avatar_path is None or (rank_tier and tier_path is None) or (top_tier and top_tier_path is None):
        raise DakanuError("玩家图片读取失败，请稍后再试。")
    role_paths: list[Path | None] = []
    for role in profile["roles"][:5]:
        role_id = role["roleId"]
        role_url = role_image_url(role_id)
        role_paths.append(await resolve_image(role_url, local_role_image(role_id)))

    medal_images: list[str] = []
    medals = profile["player"].get("medals", [])
    for medal in medals[:6] if isinstance(medals, list) else []:
        if not isinstance(medal, dict):
            medal_images.append("")
            continue
        medal_id = medal.get("id")
        if isinstance(medal_id, bool) or not isinstance(medal_id, int):
            medal_images.append("")
            continue
        try:
            path = await resolve_image(
                f"https://www.dakanu.com/medals/{medal_id}.webp",
                local_medal_image(medal_id),
            )
            medal_images.append(_data_uri(path.read_bytes(), path.suffix) if path is not None else "")
        except Exception:
            medal_images.append("")

    assets = SummaryAssets(
        avatar=_data_uri(avatar_path.read_bytes(), avatar_path.suffix),
        tier_icon=_data_uri(tier_path.read_bytes(), tier_path.suffix) if tier_path is not None else "",
        top_tier_icon=_data_uri(top_tier_path.read_bytes(), top_tier_path.suffix) if top_tier_path is not None else "",
        challenge_icon=_data_uri(challenge_path.read_bytes(), challenge_path.suffix)
        if challenge_path is not None
        else "",
        baseplate=_data_uri(baseplate_path.read_bytes(), baseplate_path.suffix) if baseplate_path is not None else "",
        frame=_data_uri(frame_path.read_bytes(), frame_path.suffix) if frame_path is not None else "",
        role_images=tuple(_data_uri(path.read_bytes(), path.suffix) if path is not None else "" for path in role_paths),
        clan_name=snapshot.clan["name"] if snapshot.clan is not None else "",
        leisure=leisure,
        medals=tuple(medals[:6]) if isinstance(medals, list) else (),
        medal_images=tuple(medal_images),
        region=region,
        season_label=season_label,
    )
    return await render_summary_card(profile, assets)


async def build_summary_card(player_id: str, *, region: str = "cn") -> bytes:
    """只读本地快照渲染；没有快照时提示先刷新。"""
    snapshot = await load_player_snapshot(player_id, region=region)
    if snapshot is None:
        raise DakanuError("本地还没有这个玩家的战绩。\n请先发送 kq刷新数据 拉取。")
    return await render_snapshot_card(snapshot, region=region)


async def resolve_season_label(label: str, *, region: str = "cn") -> tuple[int, str] | None:
    """按站点赛季列表查找标签对应的 season_id。"""
    payload = await fetch_ranking_seasons(region=region)
    seasons = payload.get("seasons", [])
    if not isinstance(seasons, list):
        return None
    normalized = label.strip().casefold()
    for season in seasons:
        if not isinstance(season, dict):
            continue
        season_label = season.get("label")
        season_id = season.get("season_id")
        if (
            isinstance(season_label, str)
            and season_label.casefold() == normalized
            and isinstance(season_id, int)
            and not isinstance(season_id, bool)
        ):
            return season_id, season_label
    return None


def _season_profile(profile: dict[str, object], season: dict[str, object], label: str | None):
    """把赛季接口的生涯统计并入现有总览卡数据结构。"""
    result = deepcopy(profile)
    summary = season.get("summary")
    modes = season.get("modes")
    roles = season.get("roles")
    season_label = season.get("seasonLabel")
    if isinstance(summary, dict):
        result["summary"] = {**result.get("summary", {}), **summary}
    if isinstance(modes, list):
        result["modes"] = modes
    if isinstance(roles, list):
        names = {
            role.get("roleId"): role.get("name")
            for role in result.get("roles", [])
            if isinstance(role, dict) and isinstance(role.get("name"), str)
        }
        result["roles"] = [
            {**role, "name": names.get(role.get("roleId"), f"角色 {role.get('roleId', '')}")}
            for role in roles
            if isinstance(role, dict)
        ]
    rank = result.get("rank")
    final = season.get("final")
    top = season.get("top")
    if isinstance(rank, dict) and isinstance(top, dict):
        selected = {**rank}
        final_segment = final.get("segment") if isinstance(final, dict) else None
        final_score = final.get("divisionScore") if isinstance(final, dict) else None
        final_position = final.get("rankPosition") if isinstance(final, dict) else None
        top_segment = top.get("segment")
        top_score = top.get("divisionScore")
        top_position = top.get("rankPosition")
        if isinstance(final_segment, int) or isinstance(top_segment, int):
            selected["segment"] = final_segment if isinstance(final_segment, int) else top_segment
        if isinstance(final_score, int) or isinstance(top_score, int):
            selected["divisionScore"] = final_score if isinstance(final_score, int) else top_score
        selected["rankPos"] = final_position if isinstance(final_position, int) else None
        if isinstance(top_segment, int):
            selected["topSegment"] = top_segment
        if isinstance(top_score, int):
            selected["topDivisionScore"] = top_score
        selected["topRankPos"] = top_position if isinstance(top_position, int) else None
        result["rank"] = selected
    meta = result.get("meta")
    display_label = label or (season_label if isinstance(season_label, str) else "")
    if isinstance(meta, dict) and display_label:
        meta["currentSeason"] = display_label
    result["historyMatches"] = []
    season_leisure = season.get("leisure")
    leisure = _normalize_season_leisure(season_leisure) if isinstance(season_leisure, dict) else None
    return result, leisure


def _normalize_season_leisure(value: dict[str, object]) -> dict[str, object] | None:
    leisure: dict[str, object] = {}
    for current_key, top_key, target in (
        ("currentRank", "topRank", "segment"),
        ("currentScore", "topScore", "score"),
        ("currentStar", "topStar", "star"),
    ):
        item = value.get(current_key)
        if not isinstance(item, int) or isinstance(item, bool) or item <= 0:
            item = value.get(top_key)
        if isinstance(item, int) and not isinstance(item, bool):
            leisure[target] = item
    for key in ("topRank", "topScore", "topStar"):
        item = value.get(key)
        if isinstance(item, int) and not isinstance(item, bool):
            leisure[key] = item
    return leisure or None


def _data_uri(content: bytes, suffix: str) -> str:
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix.lower(), "image/webp")
    return f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"
