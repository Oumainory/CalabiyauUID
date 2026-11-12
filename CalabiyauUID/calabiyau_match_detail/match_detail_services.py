"""指定对局详情查询与卡片编排。"""

from pathlib import Path

from gsuid_core.pool import to_thread

from ..utils.api.dakanu import DakanuError, DakanuMatch, fetch_profile, fetch_match_detail
from ..utils.downloader import resolve_image
from ..utils.helper.maps import MapInfo, resolve_map
from ..utils.helper.assets import image_data_uri, local_map_slug_image
from ..utils.helper.player_data import load_player_snapshot
from ..utils.helper.role_images import load_role_images
from ..utils.helper.resolve_player import region_label
from ..utils.render.html.match_detail_card import render_match_detail_card


def _map_url(slug: str) -> str:
    return f"https://www.dakanu.com/maps-wide/{slug}.webp"


def _read_image_uri(path: Path) -> str:
    return image_data_uri(path.read_bytes(), path.suffix)


async def _load_map_image(map_info: MapInfo | None) -> str:
    if map_info is None:
        return ""
    path = await resolve_image(_map_url(map_info.slug), local_map_slug_image(map_info.slug))
    if path is None:
        return ""
    return await to_thread(_read_image_uri)(path)


def _read(source: object, *keys: str) -> object | None:
    if not isinstance(source, dict):
        return None
    for key in keys:
        value = source.get(key)
        if value is not None and value != "":
            return value
    return None


def _valid_value(value: object, kind: str) -> bool:
    if kind == "score":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind in {"map", "duration", "time"}:
        return isinstance(value, int) and not isinstance(value, bool) and value > 0
    if kind == "result":
        return isinstance(value, str) and value in {"win", "lose", "draw"}
    return isinstance(value, str) and bool(value.strip())


def _has_value(summary: object, detail: object, keys: tuple[str, ...], kind: str) -> bool:
    return any(_valid_value(_read(source, *keys), kind) for source in (summary, detail))


def _has_score_pair(summary: object, detail: object) -> bool:
    for source in (summary, detail):
        viewer_scores = (_read(source, "myScore", "viewerScore"), _read(source, "opponentScore", "enemyScore"))
        team_scores = (
            _read(source, "teamAScore", "scoreA", "blueScore", "leftScore"),
            _read(source, "teamBScore", "scoreB", "redScore", "rightScore"),
        )
        scores = _read(source, "scores", "teamScores")
        if all(_valid_value(value, "score") for value in viewer_scores) or all(
            _valid_value(value, "score") for value in team_scores
        ):
            return True
        if isinstance(scores, list) and len(scores) >= 2 and all(_valid_value(value, "score") for value in scores[:2]):
            return True
    return False


def _needs_match_fallback(detail: dict[str, object]) -> bool:
    summary = detail.get("summary")
    return any(
        (
            not _has_value(summary, detail, ("modeLabel", "modeName", "mode"), "text"),
            not _has_value(summary, detail, ("mapId", "map_id"), "map"),
            not _has_score_pair(summary, detail),
            not _has_value(summary, detail, ("durationSeconds", "duration", "playTime"), "duration"),
            not _has_value(summary, detail, ("playedAt", "timestamp", "time"), "time"),
            not _has_value(summary, detail, ("result", "outcome"), "result"),
        )
    )


def _match_for_room(matches: object, room_id: str) -> DakanuMatch | None:
    if not isinstance(matches, list):
        return None
    for match in matches:
        if isinstance(match, dict) and str(match.get("roomId", "")) == room_id:
            return match
    return None


def _profile_match(profile: object, room_id: str) -> DakanuMatch | None:
    if not isinstance(profile, dict):
        return None
    for key in ("matches", "historyMatches"):
        match = _match_for_room(profile.get(key), room_id)
        if match is not None:
            return match
    return None


def _viewer_fallback(detail: dict[str, object], room_id: str) -> dict[str, object] | None:
    value = detail.get("viewerFallback")
    if not isinstance(value, dict):
        return None
    value_room_id = value.get("roomId")
    if value_room_id is not None and str(value_room_id) != room_id:
        return None
    nested_match = value.get("match")
    nested_summary = nested_match.get("summary") if isinstance(nested_match, dict) else None
    if isinstance(nested_match, dict):
        nested_room_id = nested_match.get("roomId")
        if nested_room_id is not None and str(nested_room_id) != room_id:
            nested_summary = None
    candidates = (value, nested_match, value.get("summary"), nested_summary)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_room_id = candidate.get("roomId")
        if candidate_room_id is not None and str(candidate_room_id) != room_id:
            continue
        has_match_data = any(
            _valid_value(candidate.get(key), kind)
            for key, kind in (
                ("modeLabel", "text"),
                ("modeName", "text"),
                ("mode", "text"),
                ("mapId", "map"),
                ("map_id", "map"),
                ("myScore", "score"),
                ("opponentScore", "score"),
                ("durationSeconds", "duration"),
                ("playedAt", "time"),
                ("result", "result"),
            )
        ) or _has_score_pair(candidate, candidate)
        if has_match_data:
            return candidate
    return None


async def _find_viewer_match(viewer_id: str, room_id: str, region: str) -> DakanuMatch | None:
    snapshot = await load_player_snapshot(viewer_id, region=region)
    if snapshot is not None:
        match = _profile_match(snapshot.profile, room_id)
        if match is not None:
            return match
    try:
        profile = await fetch_profile(viewer_id, region=region)
    except DakanuError:
        return None
    return _profile_match(profile, room_id)


def _merge_match_fallback(detail: dict[str, object], match: dict[str, object]) -> dict[str, object]:
    enriched = dict(detail)
    source_summary = detail.get("summary")
    summary = dict(source_summary) if isinstance(source_summary, dict) else {}
    fields = (
        ("modeLabel", ("modeLabel", "modeName", "mode"), ("modeLabel", "modeName", "mode"), "text"),
        ("mapId", ("mapId", "map_id"), ("mapId", "map_id"), "map"),
        ("myScore", ("myScore", "viewerScore"), ("myScore", "viewerScore"), "score"),
        ("opponentScore", ("opponentScore", "enemyScore"), ("opponentScore", "enemyScore"), "score"),
        (
            "durationSeconds",
            ("durationSeconds", "duration", "playTime"),
            ("durationSeconds", "duration", "playTime"),
            "duration",
        ),
        ("playedAt", ("playedAt", "timestamp", "time"), ("playedAt", "timestamp", "time"), "time"),
        ("result", ("result", "outcome"), ("result", "outcome"), "result"),
    )
    changed = False
    for output_key, aliases, detail_aliases, kind in fields:
        current = _read(summary, *aliases)
        if not _valid_value(current, kind):
            current = _read(detail, *detail_aliases)
        candidate = match.get(output_key)
        if not _valid_value(current, kind) and _valid_value(candidate, kind):
            summary[output_key] = candidate
            changed = True
    if changed:
        enriched["summary"] = summary
    return enriched


def _role_ids(detail: dict[str, object]) -> set[int]:
    teams = detail.get("teams")
    if not isinstance(teams, list):
        return set()
    role_ids: set[int] = set()
    for team in teams:
        if not isinstance(team, dict) or not isinstance(team.get("players"), list):
            continue
        for player in team["players"]:
            if not isinstance(player, dict):
                continue
            role_id = player.get("roleId")
            if isinstance(role_id, int) and not isinstance(role_id, bool):
                role_ids.add(role_id)
    return role_ids


async def build_match_detail_card(room_id: str, viewer_id: str, *, region: str = "cn") -> bytes:
    detail = await fetch_match_detail(viewer_id, room_id, region=region)
    if detail is None:
        raise DakanuError(f"没有找到对局「{room_id}」的详情，或站点暂未收录该场对局。")
    if _needs_match_fallback(detail):
        match = _viewer_fallback(detail, room_id)
        if match is not None:
            detail = _merge_match_fallback(detail, match)
        if _needs_match_fallback(detail):
            match = await _find_viewer_match(viewer_id, room_id, region)
            if match is not None:
                detail = _merge_match_fallback(detail, match)
    summary = detail.get("summary")
    map_value = _read(summary, "mapId", "map_id")
    if map_value is None:
        map_value = _read(detail, "mapId", "map_id")
    map_id = map_value if isinstance(map_value, int) and not isinstance(map_value, bool) else None
    map_info = resolve_map(map_id) if map_id is not None else None
    map_image = await _load_map_image(map_info)
    role_images = await load_role_images(_role_ids(detail))
    return await render_match_detail_card(
        detail,
        room_id=room_id,
        viewer_id=viewer_id,
        region=region_label(region),
        role_images=role_images,
        map_image=map_image,
    )
