"""插件数据与资源目录。"""

from pathlib import Path

from gsuid_core.data_store import get_res_path

DATA_DIR: Path = get_res_path("CalabiyauUID")
RESOURCE_DIR: Path = get_res_path("resourse")
ASSET_DIR: Path = RESOURCE_DIR / "assets"
