"""玩家数据刷新：合并同一 UID 的并发请求并写入本地快照。"""

import time
import asyncio
from dataclasses import dataclass

import httpx

from ..api.dakanu import DakanuError, DakanuProfile, fetch_clan, fetch_leisure, refresh_profile, fetch_season_data
from .player_data import PlayerSnapshot, has_player_data, load_player_snapshot, save_player_snapshot


@dataclass(frozen=True)
class RefreshResult:
    player_id: str
    snapshot: PlayerSnapshot
    from_cache: bool


_locks: dict[str, asyncio.Lock] = {}
_inflight: dict[str, asyncio.Task[RefreshResult]] = {}
_background_tasks: set[asyncio.Task[object]] = set()


def _lock_for(player_id: str) -> asyncio.Lock:
    lock = _locks.get(player_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[player_id] = lock
    return lock


def track_background(task: asyncio.Task[object]) -> None:
    """持有后台任务强引用，避免事件循环只保留弱引用时被回收。"""
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _snapshot_from_profile(player_id: str, profile: DakanuProfile, region: str) -> PlayerSnapshot:
    leisure = await fetch_leisure(player_id, region=region)
    if leisure is None:
        try:
            season = await fetch_season_data(player_id, 0, region=region)
        except DakanuError:
            season = None
        season_leisure = season.get("leisure") if season is not None else None
        if isinstance(season_leisure, dict):
            fallback: dict[str, object] = {}
            for current_key, top_key, target in (
                ("currentRank", "topRank", "segment"),
                ("currentScore", "topScore", "score"),
                ("currentStar", "topStar", "star"),
            ):
                value = season_leisure.get(current_key)
                if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                    value = season_leisure.get(top_key)
                if isinstance(value, int) and not isinstance(value, bool):
                    fallback[target] = value
            for key in ("topRank", "topScore", "topStar"):
                value = season_leisure.get(key)
                if isinstance(value, int) and not isinstance(value, bool):
                    fallback[key] = value
            leisure = fallback or None
    clan = await fetch_clan(profile["player"]["clanId"], region=region)
    snapshot = PlayerSnapshot(
        profile=profile,
        leisure=leisure,
        clan=clan,
        saved_at=int(time.time()),
        region=region,
    )
    await save_player_snapshot(snapshot)
    return snapshot


async def _refresh_uncached(player_id: str, region: str) -> RefreshResult:
    try:
        profile = await refresh_profile(player_id, region=region)
        snapshot = await _snapshot_from_profile(player_id, profile, region)
    except (httpx.HTTPError, OSError) as exc:
        raise RuntimeError("连接战绩站失败，请稍后重试。") from exc
    return RefreshResult(player_id=player_id, snapshot=snapshot, from_cache=False)


async def refresh_player_data(player_id: str, *, force: bool = False, region: str = "cn") -> RefreshResult:
    """读取或刷新玩家数据；force=False 时优先使用本地快照。"""
    key = f"{region}:{player_id}"
    inflight = _inflight.get(key)
    if inflight is not None:
        return await asyncio.shield(inflight)

    lock = _lock_for(key)
    async with lock:
        inflight = _inflight.get(key)
        if inflight is not None:
            return await asyncio.shield(inflight)
        if not force:
            snapshot = await load_player_snapshot(player_id, region=region)
            if snapshot is not None and has_player_data(player_id, region):
                return RefreshResult(player_id=player_id, snapshot=snapshot, from_cache=True)

        task = asyncio.create_task(_refresh_uncached(player_id, region))
        _inflight[key] = task
        try:
            return await asyncio.shield(task)
        finally:
            if _inflight.get(key) is task:
                _inflight.pop(key, None)
