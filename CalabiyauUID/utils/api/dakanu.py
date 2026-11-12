"""Dakanu 公开读取接口。"""

import asyncio
from collections import OrderedDict
from copy import deepcopy
from threading import Lock
import time
from typing import NotRequired, TypedDict, TypeGuard

import httpx

from gsuid_core.pool import to_thread
from gsuid_core.logger import logger

BASE_URL = "https://www.dakanu.com"
_REFRESH_POLL_INTERVAL = 2.0
_REFRESH_TIMEOUT = 300.0
_CACHE_MAX_ENTRIES = 200
_SEARCH_CACHE_TTL = 600.0
_PROFILE_CACHE_TTL = 90.0

_response_cache: OrderedDict[tuple[str, str], tuple[float, object]] = OrderedDict()
_response_cache_lock = Lock()


class DakanuPlayer(TypedDict):
    id: str
    nickname: str
    clanId: str
    previousNames: list[str]
    level: int
    exp: int
    laud: int
    avatarId: int
    borderId: int
    privacyStatus: str
    accountVerified: bool


class DakanuPlayerSuggestion(TypedDict):
    playerId: str
    nickname: str
    exact: NotRequired[bool]
    level: NotRequired[int]


class DakanuPresence(TypedDict):
    state: str
    onlineStatus: str | None
    lastOnlineAt: int | None
    lastActiveAt: int | None


class DakanuRank(TypedDict):
    segment: int
    topSegment: int
    historicalSegment: int
    historicalSegmentSeason: int
    historicalSegmentPos: int | None
    divisionScore: int
    topDivisionScore: int
    gradeScore: int
    topGradeScore: int
    rankPos: int | None
    topRankPos: int | None
    likeCount: int


class DakanuSummary(TypedDict):
    rounds: int
    wins: int
    losses: int
    winRate: float
    kills: int
    assists: int
    deaths: int
    kd: float
    kda: float
    damage: int
    avgDamage: float
    roundAveDamage: float
    avgKill: float
    avgAssist: float
    avgDeath: float
    mvpCount: int
    mvpRate: float
    headshotRate: float


class DakanuMode(TypedDict):
    mode: str
    label: str
    rounds: int
    wins: int
    winRate: float
    kd: float
    avgDamage: float
    roundAveDamage: float
    avgKill: float
    avgAssist: float
    avgDeath: float
    headshotRate: float
    mvpCount: int
    mvpRate: float


class DakanuRole(TypedDict):
    roleId: int
    name: str
    count: int
    wins: int
    winRate: float
    kills: int
    deaths: int
    kd: float
    damage: int
    avgDamage: float
    maxKill: int
    maxDamage: int


class DakanuMatch(TypedDict):
    roomId: str
    mode: str
    modeLabel: str
    playMode: str
    mapId: int
    roleId: int
    result: str
    myScore: int | None
    opponentScore: int | None
    durationSeconds: int
    playedAt: int
    myRanking: int | None
    mvp: bool
    svp: bool
    divisionScore: int | None
    divisionScoreDelta: int | None
    kills: int
    deaths: int
    assists: int
    teamKills: int | None


class DakanuMatchPlayer(TypedDict):
    playerId: str
    nickname: str
    avatarId: int
    teamId: str
    teamLabel: str
    roleId: int
    roleName: str
    kills: int
    knockdowns: int | None
    assists: int
    deaths: int
    damage: int
    score: int
    personalScore: int | None
    strategyScore: int | None
    teamworkScore: int | None
    result: str
    mvp: bool
    svp: bool
    isTarget: bool


class DakanuMatchTeam(TypedDict):
    id: str
    label: str
    players: list[DakanuMatchPlayer]


class DakanuMatchDetail(TypedDict, total=False):
    ok: bool
    roomId: str
    summary: object | None
    teams: list[DakanuMatchTeam]
    rounds: list[object]
    hasDetail: bool
    viewerPlayerId: str | None
    scoreboardViewerPlayerId: str | None
    upstreamCode: int
    viewerFallback: object | None
    cached: bool


class DakanuRefreshError(TypedDict):
    message: str
    code: str
    status: int


class DakanuRefreshJob(TypedDict, total=False):
    state: str
    startedAt: int
    finishedAt: int
    error: DakanuRefreshError
    warning: dict[str, str]


class DakanuRefreshResponse(TypedDict):
    ok: bool
    job: DakanuRefreshJob


class DakanuMeta(TypedDict):
    cached: bool
    source: str
    currentSeason: str
    matchesTotal: int
    detailsAvailable: int
    warnings: list[str]
    fetchedAt: int
    stale: str | None
    observedMatches: int
    lastCheckedAt: int


class DakanuTeamUp(TypedDict):
    playerId: str
    nickname: str
    avatarId: int
    teamedGames: int
    teamedWins: int
    teamedLosses: int
    teamedDraws: int
    teamedWinRate: float
    lastWinAt: int | None
    latestRoomId: str | None


class DakanuRival(TypedDict):
    playerId: str
    nickname: str
    avatarId: int
    games: int
    wins: int
    losses: int
    draws: int
    winRate: float
    lastPlayedAt: int | None
    latestRoomId: str | None


class DakanuProfile(TypedDict):
    player: DakanuPlayer
    presence: DakanuPresence
    rank: DakanuRank
    summary: DakanuSummary
    modes: list[DakanuMode]
    roles: list[DakanuRole]
    matches: list[DakanuMatch]
    historyMatches: list[DakanuMatch]
    teamUps: list[DakanuTeamUp]
    rivals: list[DakanuRival]
    meta: DakanuMeta


class DakanuProfileResponse(TypedDict):
    ok: bool
    profile: DakanuProfile


class DakanuSearchResponse(TypedDict):
    suggestions: list[DakanuPlayerSuggestion]


class DakanuClanIcon(TypedDict):
    bgId: int
    bgColor: int
    imageId: int
    imageColor: int


class DakanuClan(TypedDict):
    clanId: str
    name: str
    level: int
    memberCount: int
    icon: DakanuClanIcon
    intro: str


class DakanuClanSearch(TypedDict):
    ok: bool
    count: int
    clans: list[DakanuClan]


class DakanuFavoriteMode(TypedDict):
    mode: str
    label: str


class DakanuLeisure(TypedDict, total=False):
    score: int
    segment: int
    star: int
    starScore: int
    battles: int
    wins: int
    winRate: float
    mvpCount: int
    favoriteModes: list[DakanuFavoriteMode]
    favoriteRoles: list[int]


_ROLE_SLUGS: dict[int, str] = {
    101: "michele",
    105: "audrey",
    107: "maddelena",
    108: "nobunaga",
    109: "reiichi",
    110: "bai_mo",
    112: "fuchsia",
    115: "flavia",
    119: "eika",
    120: "fragrans",
    121: "yugiri",
    122: "mara",
    123: "leona",
    124: "kokona",
    125: "qian_dai",
    126: "nono",
    128: "lawine",
    130: "xi",
    131: "yvette",
    132: "ming",
    133: "meredith",
    137: "kanami",
    146: "celestia",
    205: "galatea",
}


def role_image_url(role_id: int) -> str:
    """按角色 ID 返回站点角色立绘地址；未知角色返回空串。"""
    slug = _ROLE_SLUGS.get(role_id)
    return f"{BASE_URL}/roles/{slug}.webp" if slug else ""


class DakanuError(Exception):
    """Dakanu 请求失败，message 可直接向用户说明原因。"""


def _cache_get(key: tuple[str, str]) -> object | None:
    now = time.monotonic()
    with _response_cache_lock:
        entry = _response_cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= now:
            del _response_cache[key]
            return None
        _response_cache.move_to_end(key)
        return deepcopy(value)


def _cache_set(key: tuple[str, str], value: object, ttl: float) -> None:
    now = time.monotonic()
    with _response_cache_lock:
        expired = [cache_key for cache_key, (expires_at, _) in _response_cache.items() if expires_at <= now]
        for cache_key in expired:
            _response_cache.pop(cache_key, None)
        _response_cache[key] = (now + ttl, deepcopy(value))
        _response_cache.move_to_end(key)
        while len(_response_cache) > _CACHE_MAX_ENTRIES:
            _response_cache.popitem(last=False)


def _request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    **kwargs: object,
) -> httpx.Response:
    """对超时和 5xx 最多重试一次，其他状态码原样交给调用方处理。"""
    for attempt in range(2):
        try:
            response = client.request(method, url, **kwargs)
        except httpx.TimeoutException:
            if attempt == 1:
                raise
            continue
        if response.status_code >= 500 and attempt == 0:
            continue
        return response
    raise RuntimeError("unreachable retry state")


def _is_search_response(value: object) -> TypeGuard[DakanuSearchResponse]:
    return isinstance(value, dict) and isinstance(value.get("suggestions"), list)


def _normalize_suggestions(values: list[object]) -> list[DakanuPlayerSuggestion]:
    suggestions: list[DakanuPlayerSuggestion] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        raw_player_id = value.get("playerId")
        if isinstance(raw_player_id, bool) or not isinstance(raw_player_id, (str, int)):
            continue
        player_id = str(raw_player_id)
        nickname = value.get("nickname")
        if not player_id.isdigit() or not isinstance(nickname, str) or not nickname.strip():
            continue
        suggestion: DakanuPlayerSuggestion = {"playerId": player_id, "nickname": nickname}
        exact = value.get("exact")
        level = value.get("level")
        if isinstance(exact, bool):
            suggestion["exact"] = exact
        if isinstance(level, int) and not isinstance(level, bool):
            suggestion["level"] = level
        suggestions.append(suggestion)
    return suggestions


def _is_profile_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    return "profile" in value and isinstance(value["profile"], dict)


@to_thread
def _fetch_profile_sync(player_id: str, use_cache: bool = True) -> DakanuProfile:
    """读取玩家缓存档案；不在查询链路里触发上游刷新。"""
    cache_key = ("profile", player_id)
    if use_cache:
        cached = _cache_get(cache_key)
        if isinstance(cached, dict):
            profile: DakanuProfile = cached
            return profile
    url = f"{BASE_URL}/api/summoner/{player_id}/cache"
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = _request_with_retry(client, "GET", url)
    except httpx.TimeoutException as exc:
        raise DakanuError("读取战绩缓存超时，请稍后再试。") from exc
    if response.status_code == 204:
        raise DakanuError("没有找到这个玩家的战绩缓存。")
    if response.status_code == 404:
        raise DakanuError("没有找到这个玩家的战绩缓存。")
    if response.status_code == 429:
        raise DakanuError("查询过于频繁，请稍后再试。")
    if response.status_code >= 500:
        raise DakanuError("战绩站暂时无法读取数据，请稍后再试。")
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·战绩总览] 读取玩家 {player_id} 返回 HTTP {response.status_code}")
        raise DakanuError("读取战绩失败，请稍后再试。")
    try:
        payload: object = response.json()
    except ValueError:
        logger.warning(f"[卡拉彼丘·战绩总览] 玩家 {player_id} 返回非 JSON 响应")
        raise DakanuError("战绩数据格式异常，请稍后再试。") from None
    if not _is_profile_response(payload):
        logger.warning(f"[卡拉彼丘·战绩总览] 玩家 {player_id} 响应结构异常")
        raise DakanuError("战绩数据格式异常，请稍后再试。")
    profile = payload["profile"]
    _cache_set(cache_key, profile, _PROFILE_CACHE_TTL)
    return profile


async def fetch_profile(player_id: str, *, use_cache: bool = True) -> DakanuProfile:
    """在线程池读取玩家缓存档案，避免阻塞事件循环。"""
    return await _fetch_profile_sync(player_id, use_cache)


@to_thread
def _search_players_sync(query: str) -> list[DakanuPlayerSuggestion]:
    cache_key = ("search", query.casefold())
    cached = _cache_get(cache_key)
    if isinstance(cached, list):
        return cached
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = _request_with_retry(
                client,
                "GET",
                f"{BASE_URL}/api/search/players",
                params={"q": query},
            )
    except httpx.TimeoutException as exc:
        raise DakanuError("玩家搜索超时，请稍后再试。") from exc
    if response.status_code == 429:
        raise DakanuError("查询过于频繁，请稍后再试。")
    if response.status_code >= 500:
        raise DakanuError("战绩站暂时无法搜索玩家，请稍后再试。")
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·玩家搜索] 搜索返回 HTTP {response.status_code}")
        raise DakanuError("搜索玩家失败，请稍后再试。")
    try:
        payload: object = response.json()
    except ValueError:
        raise DakanuError("玩家搜索数据格式异常，请稍后再试。") from None
    if not _is_search_response(payload):
        raise DakanuError("玩家搜索数据格式异常，请稍后再试。")
    suggestions = _normalize_suggestions(payload["suggestions"])
    if suggestions:
        _cache_set(cache_key, suggestions, _SEARCH_CACHE_TTL)
    return suggestions


async def search_players(query: str) -> list[DakanuPlayerSuggestion]:
    """按昵称搜索玩家；仅缓存结构有效的成功响应。"""
    return await _search_players_sync(query)


def _is_match_detail_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    if "roomId" not in value or not isinstance(value["roomId"], str):
        return False
    if "teams" not in value or not isinstance(value["teams"], list):
        return False
    return "rounds" in value and isinstance(value["rounds"], list)


@to_thread
def _fetch_match_detail_sync(player_id: str, room_id: str) -> DakanuMatchDetail | None:
    url = f"{BASE_URL}/api/match/{room_id}"
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = _request_with_retry(client, "GET", url, params={"player": player_id})
    except httpx.TimeoutException as exc:
        raise DakanuError("读取对局详情超时，请稍后再试。") from exc
    if response.status_code == 404:
        return None
    if response.status_code == 429:
        raise DakanuError("对局详情查询过于频繁，请稍后再试。")
    if response.status_code >= 500:
        raise DakanuError("战绩站暂时无法读取对局详情，请稍后再试。")
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·最近对局] 读取对局 {room_id} 返回 HTTP {response.status_code}")
        return None
    try:
        payload: object = response.json()
    except ValueError:
        logger.warning(f"[卡拉彼丘·最近对局] 对局 {room_id} 返回非 JSON 响应")
        return None
    if not _is_match_detail_response(payload):
        logger.warning(f"[卡拉彼丘·最近对局] 对局 {room_id} 响应结构异常")
        return None
    details: DakanuMatchDetail = payload
    return details


async def fetch_match_detail(player_id: str, room_id: str) -> DakanuMatchDetail | None:
    """读取单场对局详情；无详情时返回 None。"""
    return await _fetch_match_detail_sync(player_id, room_id)


def _is_refresh_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    return "job" in value and isinstance(value["job"], dict)


@to_thread
def _start_refresh_sync(player_id: str) -> DakanuRefreshJob:
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = _request_with_retry(client, "POST", f"{BASE_URL}/api/summoner/{player_id}/refresh")
    except httpx.TimeoutException as exc:
        raise DakanuError("启动数据刷新超时，请稍后再试。") from exc
    if response.status_code == 404:
        raise DakanuError("没有找到该玩家的战绩数据。")
    if response.status_code == 429:
        raise DakanuError("查询过于频繁，请稍后再试。")
    if response.status_code >= 500:
        raise DakanuError("战绩站暂时无法查询，请稍后再试。")
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·刷新数据] 启动玩家 {player_id} 刷新返回 HTTP {response.status_code}")
        raise DakanuError("启动数据刷新失败，请稍后再试。")
    try:
        payload: object = response.json()
    except ValueError:
        logger.warning(f"[卡拉彼丘·刷新数据] 玩家 {player_id} 刷新响应不是 JSON")
        raise DakanuError("战绩数据格式异常，请稍后再试。") from None
    if not _is_refresh_response(payload):
        logger.warning(f"[卡拉彼丘·刷新数据] 玩家 {player_id} 刷新响应结构异常")
        raise DakanuError("战绩数据格式异常，请稍后再试。")
    return payload["job"]


async def start_profile_refresh(player_id: str) -> DakanuRefreshJob:
    return await _start_refresh_sync(player_id)


@to_thread
def _fetch_refresh_status_sync(player_id: str) -> DakanuRefreshJob:
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = _request_with_retry(client, "GET", f"{BASE_URL}/api/summoner/{player_id}/refresh")
    except httpx.TimeoutException as exc:
        raise DakanuError("读取刷新状态超时，请稍后再试。") from exc
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·刷新数据] 读取玩家 {player_id} 刷新状态返回 HTTP {response.status_code}")
        raise DakanuError("读取刷新状态失败，请稍后再试。")
    try:
        payload: object = response.json()
    except ValueError:
        logger.warning(f"[卡拉彼丘·刷新数据] 玩家 {player_id} 刷新状态不是 JSON")
        raise DakanuError("战绩数据格式异常，请稍后再试。") from None
    if not _is_refresh_response(payload):
        logger.warning(f"[卡拉彼丘·刷新数据] 玩家 {player_id} 刷新状态结构异常")
        raise DakanuError("战绩数据格式异常，请稍后再试。")
    return payload["job"]


async def fetch_refresh_status(player_id: str) -> DakanuRefreshJob:
    return await _fetch_refresh_status_sync(player_id)


async def refresh_profile(player_id: str) -> DakanuProfile:
    """启动刷新并等待缓存可读；缓存仍未生成时抛出 DakanuError。"""
    job = await start_profile_refresh(player_id)
    deadline = asyncio.get_running_loop().time() + _REFRESH_TIMEOUT
    while job["state"] == "running":
        if asyncio.get_running_loop().time() >= deadline:
            raise DakanuError("刷新仍在进行，请稍后用 kq战绩总览 查看。")
        await asyncio.sleep(_REFRESH_POLL_INTERVAL)
        job = await fetch_refresh_status(player_id)
    if job["state"] == "failed":
        error = job["error"]
        message = error["message"].strip()
        raise DakanuError(message or "战绩刷新失败，请稍后再试。")

    for _ in range(5):
        try:
            return await fetch_profile(player_id, use_cache=False)
        except DakanuError as exc:
            if str(exc) != "没有找到这个玩家的战绩缓存。":
                raise
        await asyncio.sleep(_REFRESH_POLL_INTERVAL)
    raise DakanuError("刷新已完成，但暂时没有读到玩家缓存。")


def _is_clan_search(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    return "clans" in value and isinstance(value["clans"], list)


@to_thread
def _fetch_clan_sync(clan_id: str) -> DakanuClan | None:
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = _request_with_retry(
                client,
                "GET",
                f"{BASE_URL}/api/clans/search",
                params={"clan_id": clan_id, "limit": 1},
            )
    except httpx.TimeoutException:
        logger.warning(f"[卡拉彼丘·战绩总览] 读取战队 {clan_id} 超时")
        return None
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·战绩总览] 读取战队 {clan_id} 返回 HTTP {response.status_code}")
        return None
    try:
        payload: object = response.json()
    except ValueError:
        logger.warning(f"[卡拉彼丘·战绩总览] 战队 {clan_id} 返回非 JSON 响应")
        return None
    if not _is_clan_search(payload):
        return None
    for clan in payload["clans"]:
        if not isinstance(clan, dict):
            continue
        if clan.get("clanId") != clan_id:
            continue
        return clan
    return None


async def fetch_clan(clan_id: str) -> DakanuClan | None:
    """按 clanId 读取战队信息；读取失败时不打断总览。"""
    if not clan_id:
        return None
    return await _fetch_clan_sync(clan_id)


def _is_leisure_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    return "leisure" in value and isinstance(value["leisure"], dict)


@to_thread
def _fetch_leisure_sync(player_id: str) -> DakanuLeisure | None:
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = _request_with_retry(
                client,
                "GET",
                f"{BASE_URL}/api/summoner/{player_id}/leisure",
                params={"season_id": 0},
            )
    except httpx.TimeoutException:
        logger.warning(f"[卡拉彼丘·战绩总览] 读取玩家 {player_id} 挑战赛数据超时")
        return None
    if response.status_code == 204:
        return None
    if response.status_code != 200:
        logger.warning(f"[卡拉彼丘·战绩总览] 读取玩家 {player_id} 挑战赛数据返回 HTTP {response.status_code}")
        return None
    try:
        payload: object = response.json()
    except ValueError:
        logger.warning(f"[卡拉彼丘·战绩总览] 玩家 {player_id} 挑战赛数据不是 JSON")
        return None
    if not _is_leisure_response(payload):
        return None
    return payload["leisure"]


async def fetch_leisure(player_id: str) -> DakanuLeisure | None:
    """读取挑战赛数据；接口无数据时返回 None。"""
    return await _fetch_leisure_sync(player_id)
