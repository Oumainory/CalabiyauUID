"""Dakanu 公开读取接口。"""

import time
import asyncio
from copy import deepcopy
from typing import TypedDict, TypeGuard, NotRequired
from threading import Lock
from collections import OrderedDict
from urllib.parse import quote, urlencode

import httpx

from gsuid_core.pool import to_thread
from gsuid_core.logger import logger

BASE_URL = "https://www.dakanu.com"
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
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
    medals: NotRequired[list[dict[str, object]]]


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
    recruitment: NotRequired[object]
    rankRequirement: NotRequired[object]


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
    available: bool
    retryAfterSeconds: int
    topRank: int
    topScore: int
    topStar: int


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


def _region_headers(region: str) -> dict[str, str]:
    """按 Dakanu 前端约定使用 X-Karabi-Region 请求头。"""
    normalized = region.strip().lower()
    if normalized not in {"cn", "global"}:
        normalized = "cn"
    return {**_DEFAULT_HEADERS, "X-Karabi-Region": normalized}


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
def _fetch_profile_sync(player_id: str, use_cache: bool = True, region: str = "cn") -> DakanuProfile:
    """读取玩家缓存档案；不在查询链路里触发上游刷新。"""
    region = region if region in {"cn", "global"} else "cn"
    cache_key = ("profile", f"{region}:{player_id}")
    if use_cache:
        cached = _cache_get(cache_key)
        if isinstance(cached, dict):
            profile: DakanuProfile = cached
            return profile
    url = f"{BASE_URL}/api/summoner/{player_id}/cache"
    try:
        with httpx.Client(
            timeout=30.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
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


async def fetch_profile(player_id: str, *, use_cache: bool = True, region: str = "cn") -> DakanuProfile:
    """在线程池读取玩家缓存档案，避免阻塞事件循环。"""
    return await _fetch_profile_sync(player_id, use_cache, region)


@to_thread
def _search_players_sync(query: str, region: str = "cn") -> list[DakanuPlayerSuggestion]:
    region = region if region in {"cn", "global"} else "cn"
    cache_key = ("search", f"{region}:{query.casefold()}")
    cached = _cache_get(cache_key)
    if isinstance(cached, list):
        return cached
    try:
        with httpx.Client(
            timeout=30.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
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


async def search_players(query: str, *, region: str = "cn") -> list[DakanuPlayerSuggestion]:
    """按昵称搜索玩家；仅缓存结构有效的成功响应。"""
    return await _search_players_sync(query, region)


def _is_match_detail_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    if "roomId" not in value or not isinstance(value["roomId"], str):
        return False
    if "teams" not in value or not isinstance(value["teams"], list):
        return False
    return "rounds" not in value or isinstance(value["rounds"], list)


@to_thread
def _fetch_match_detail_sync(player_id: str | None, room_id: str, region: str = "cn") -> DakanuMatchDetail | None:
    url = f"{BASE_URL}/api/match/{quote(room_id, safe='')}"
    params = {"player": player_id} if player_id else None
    try:
        with httpx.Client(
            timeout=30.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
            response = _request_with_retry(client, "GET", url, params=params)
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
    if not isinstance(details.get("rounds"), list):
        details["rounds"] = []
    return details


async def fetch_match_detail(
    player_id: str | None,
    room_id: str,
    *,
    region: str = "cn",
) -> DakanuMatchDetail | None:
    """读取单场对局详情；无详情时返回 None。"""
    return await _fetch_match_detail_sync(player_id, room_id, region)


def _is_refresh_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    return "job" in value and isinstance(value["job"], dict)


@to_thread
def _start_refresh_sync(player_id: str, region: str = "cn") -> DakanuRefreshJob:
    try:
        with httpx.Client(
            timeout=30.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
            response = _request_with_retry(client, "POST", f"{BASE_URL}/api/summoner/{player_id}/refresh")
    except httpx.TimeoutException as exc:
        raise DakanuError("启动数据刷新超时，请稍后再试。") from exc
    if response.status_code == 404:
        raise DakanuError("没有找到该玩家的战绩数据。")
    if response.status_code == 429:
        raise DakanuError("查询过于频繁，请稍后再试。")
    if response.status_code >= 500:
        raise DakanuError("战绩站暂时无法查询，请稍后再试。")
    if response.status_code not in (200, 202):
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


async def start_profile_refresh(player_id: str, *, region: str = "cn") -> DakanuRefreshJob:
    return await _start_refresh_sync(player_id, region)


@to_thread
def _fetch_refresh_status_sync(player_id: str, region: str = "cn") -> DakanuRefreshJob:
    try:
        with httpx.Client(
            timeout=30.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
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


async def fetch_refresh_status(player_id: str, *, region: str = "cn") -> DakanuRefreshJob:
    return await _fetch_refresh_status_sync(player_id, region)


async def refresh_profile(player_id: str, *, region: str = "cn") -> DakanuProfile:
    """启动刷新并等待缓存可读；缓存仍未生成时抛出 DakanuError。"""
    job = await start_profile_refresh(player_id, region=region)
    deadline = asyncio.get_running_loop().time() + _REFRESH_TIMEOUT
    while job["state"] == "running":
        if asyncio.get_running_loop().time() >= deadline:
            raise DakanuError("刷新仍在进行，请稍后用 kq战绩总览 查看。")
        await asyncio.sleep(_REFRESH_POLL_INTERVAL)
        job = await fetch_refresh_status(player_id, region=region)
    if job["state"] == "failed":
        error = job["error"]
        message = error["message"].strip()
        raise DakanuError(message or "战绩刷新失败，请稍后再试。")

    for _ in range(5):
        try:
            return await fetch_profile(player_id, use_cache=False, region=region)
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
def _fetch_clan_sync(clan_id: str, region: str = "cn") -> DakanuClan | None:
    try:
        with httpx.Client(
            timeout=20.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
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


async def fetch_clan(clan_id: str, *, region: str = "cn") -> DakanuClan | None:
    """按 clanId 读取战队信息；读取失败时不打断总览。"""
    if not clan_id:
        return None
    return await _fetch_clan_sync(clan_id, region)


def _is_leisure_response(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if "ok" not in value or value["ok"] is not True:
        return False
    return "leisure" in value and isinstance(value["leisure"], dict)


@to_thread
def _fetch_leisure_sync(player_id: str, region: str = "cn") -> DakanuLeisure | None:
    try:
        with httpx.Client(
            timeout=20.0, follow_redirects=True, headers=_region_headers(region)
        ) as client:
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
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return None
    leisure = payload.get("leisure")
    if payload.get("available") is False or not isinstance(leisure, dict):
        return None
    return leisure


async def fetch_leisure(player_id: str, *, region: str = "cn") -> DakanuLeisure | None:
    """读取挑战赛数据；接口无数据时返回 None。"""
    return await _fetch_leisure_sync(player_id, region)


@to_thread
def _fetch_public_json_sync(
    path: str,
    params: dict[str, str | int] | None = None,
    region: str = "cn",
    cache_group: str = "",
    cache_ttl: float = 0.0,
) -> object | None:
    """读取 Dakanu 的公开 JSON 接口，并按区服和完整参数短暂缓存。"""
    normalized_region = region if region in {"cn", "global"} else "cn"
    query_key = urlencode(sorted((params or {}).items()))
    cache_key = (cache_group or "public", f"{normalized_region}:{path}?{query_key}")
    if cache_ttl:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True, headers=_region_headers(normalized_region)) as client:
            response = _request_with_retry(client, "GET", f"{BASE_URL}{path}", params=params)
    except httpx.TimeoutException as exc:
        raise DakanuError("查询战绩站超时，请稍后再试。") from exc
    if response.status_code in (204, 404):
        return None
    if response.status_code == 429:
        raise DakanuError("查询过于频繁，请稍后再试。")
    if response.status_code >= 500:
        raise DakanuError("战绩站暂时无法读取数据，请稍后再试。")
    if response.status_code not in (200, 202):
        logger.warning(f"[卡拉彼丘·公开查询] {path} 返回 HTTP {response.status_code}")
        raise DakanuError("读取战绩站数据失败，请稍后再试。")
    try:
        payload: object = response.json()
    except ValueError as exc:
        raise DakanuError("战绩站返回的数据格式异常，请稍后再试。") from exc
    is_refreshing = isinstance(payload, dict) and payload.get("refreshing") is True
    if cache_ttl and response.status_code == 200 and not is_refreshing:
        _cache_set(cache_key, payload, cache_ttl)
    return payload


async def _fetch_public_json(
    path: str,
    *,
    params: dict[str, str | int] | None = None,
    region: str = "cn",
    cache_group: str = "",
    cache_ttl: float = 0.0,
) -> object | None:
    return await _fetch_public_json_sync(path, params, region, cache_group, cache_ttl)


def _is_ok_list(payload: object, key: str) -> bool:
    return isinstance(payload, dict) and payload.get("ok") is True and isinstance(payload.get(key), list)


async def fetch_ranking_types(*, region: str = "cn") -> dict[str, object]:
    payload = await _fetch_public_json(
        "/api/rankings/types", region=region, cache_group="rank-types", cache_ttl=1800
    )
    if not _is_ok_list(payload, "types"):
        raise DakanuError("暂时无法读取排行榜类型，请稍后再试。")
    return payload


async def fetch_ranking_seasons(*, region: str = "cn") -> dict[str, object]:
    payload = await _fetch_public_json(
        "/api/rankings/seasons", region=region, cache_group="rank-seasons", cache_ttl=600
    )
    if not isinstance(payload, dict) or payload.get("ok") is not True or not isinstance(payload.get("seasons"), list):
        raise DakanuError("暂时无法读取赛季列表，请稍后再试。")
    return payload


async def fetch_rankings(
    type_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    season_id: int | None = None,
    region: str = "cn",
) -> dict[str, object]:
    params: dict[str, str | int] = {"type": type_id, "page": page, "page_size": page_size}
    if season_id is not None and season_id > 0:
        params["season_id"] = season_id
    payload = await _fetch_public_json(
        "/api/rankings", params=params, region=region, cache_group="rankings", cache_ttl=300
    )
    if not _is_ok_list(payload, "entries"):
        raise DakanuError("暂时无法读取排行榜，请稍后再试。")
    return payload


async def fetch_role_ranking(*, ranked_only: bool = True, region: str = "cn") -> dict[str, object]:
    params: dict[str, str | int] = {"min_games": 3}
    if not ranked_only:
        params["all"] = 1
    payload = await _fetch_public_json(
        "/api/roles/ranking", params=params, region=region, cache_group="role-ranking", cache_ttl=120
    )
    if not _is_ok_list(payload, "entries"):
        raise DakanuError("暂时无法读取超弦体排行，请稍后再试。")
    if not isinstance(payload.get("mapStats"), list):
        payload["mapStats"] = []
    return payload


async def fetch_friend_ranking(
    *,
    page: int = 1,
    page_size: int = 20,
    region: str = "cn",
) -> dict[str, object]:
    params: dict[str, str | int] = {
        "sort": "games",
        "min_games": 10,
        "page": page,
        "page_size": page_size,
    }
    payload = await _fetch_public_json(
        "/api/friends/ranking", params=params, region=region, cache_group="friend-ranking", cache_ttl=300
    )
    if not _is_ok_list(payload, "entries"):
        raise DakanuError("暂时无法读取好友榜，请稍后再试。")
    return payload


async def search_clans(
    *,
    name: str | None = None,
    clan_id: str | None = None,
    limit: int = 10,
    region: str = "cn",
) -> dict[str, object]:
    params: dict[str, str | int] = {"limit": limit}
    if name and name.strip():
        params["name"] = name.strip()
    if clan_id and clan_id.strip():
        params["clan_id"] = clan_id.strip()
    if not name and not clan_id:
        raise DakanuError("请提供战队名称或战队 ID。")
    payload = await _fetch_public_json(
        "/api/clans/search", params=params, region=region, cache_group="clan-search", cache_ttl=300
    )
    if not _is_ok_list(payload, "clans"):
        raise DakanuError("暂时无法搜索战队，请稍后再试。")
    return payload


async def fetch_clan_members(clan_id: str, *, region: str = "cn") -> dict[str, object] | None:
    path = f"/api/clans/{quote(clan_id, safe='')}/members"
    payload = await _fetch_public_json(path, region=region, cache_group="clan-members", cache_ttl=300)
    if payload is None:
        return None
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return None
    members = payload.get("members")
    if payload.get("refreshing") is True and (not isinstance(members, list) or not members):
        await asyncio.sleep(2)
        payload = await _fetch_public_json(path, region=region, cache_group="clan-members", cache_ttl=300)
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            return None
    return payload


async def fetch_season_data(player_id: str, season_id: int, *, region: str = "cn") -> dict[str, object] | None:
    payload = await _fetch_public_json(
        f"/api/summoner/{quote(player_id, safe='')}/seasons",
        params={"season_id": season_id},
        region=region,
        cache_group="season-data",
        cache_ttl=300,
    )
    if payload is None:
        return None
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return None
    season = payload.get("season")
    return season if isinstance(season, dict) else None
