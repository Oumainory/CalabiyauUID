"""启动后从资源仓库同步素材。"""

import re
import asyncio

from gsuid_core.logger import logger
from gsuid_core.server import on_core_start
from gsuid_core.utils.plugins_update.git_async import (
    GIT_CLONE_TIMEOUT,
    run_git,
    git_clone,
    git_reset_hard,
    git_get_current_commit,
)

from ..utils.paths import RESOURCE_DIR

RESOURCE_REPO_URL = "https://cnb.cool/shiysssysy/CalabiyauUID-resourse"
_RESOURCE_TAG = "[卡拉彼丘·资源更新]"
_update_lock = asyncio.Lock()


def _is_git_repo() -> bool:
    return (RESOURCE_DIR / ".git").is_dir()


async def _detect_default_branch() -> str | None:
    remote = "origin" if _is_git_repo() else RESOURCE_REPO_URL
    retcode, stdout, _ = await run_git(RESOURCE_DIR, "ls-remote", "--symref", remote, "HEAD")
    if retcode != 0:
        return None
    match = re.search(r"ref:\s+refs/heads/(\S+)", stdout)
    return match.group(1) if match is not None else None


async def update_resources() -> bool:
    async with _update_lock:
        branch = await _detect_default_branch()
        if branch is None:
            logger.warning(f"{_RESOURCE_TAG} 无法获取资源仓库默认分支")
            return False

        if not _is_git_repo():
            success, message = await git_clone(
                RESOURCE_REPO_URL,
                RESOURCE_DIR,
                branch=branch,
                depth=1,
                timeout=GIT_CLONE_TIMEOUT,
            )
            if not success:
                logger.warning(f"{_RESOURCE_TAG} 首次克隆失败：{message}")
                return False
            logger.success(f"{_RESOURCE_TAG} 资源仓库首次克隆完成")
            return True

        old_head = await git_get_current_commit(RESOURCE_DIR)
        retcode, stdout, stderr = await run_git(
            RESOURCE_DIR,
            "fetch",
            "--depth=1",
            "--",
            "origin",
            branch,
            timeout=GIT_CLONE_TIMEOUT,
        )
        if retcode != 0:
            logger.warning(f"{_RESOURCE_TAG} 拉取失败：{stderr or stdout}")
            return False

        success, message = await git_reset_hard(RESOURCE_DIR, "FETCH_HEAD")
        if not success:
            logger.warning(f"{_RESOURCE_TAG} 更新失败：{message}")
            return False

        new_head = await git_get_current_commit(RESOURCE_DIR)
        if not new_head:
            logger.warning(f"{_RESOURCE_TAG} 无法读取资源仓库版本")
            return False
        if old_head == new_head:
            logger.info(f"{_RESOURCE_TAG} 资源已是最新")
        else:
            logger.success(f"{_RESOURCE_TAG} 资源更新完成")
        return True


@on_core_start(priority=100)
async def sync_resources_on_start() -> None:
    """启动后同步资源；网络或 git 异常不阻断 Core。"""
    try:
        success = await update_resources()
    except OSError as exc:
        logger.warning(f"{_RESOURCE_TAG} git 不可用：{exc}")
        return
    if not success:
        logger.warning(f"{_RESOURCE_TAG} 启动同步失败，将继续使用本地已有资源")
