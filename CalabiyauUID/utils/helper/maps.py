"""地图 ID 与站点地图信息的对应关系。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MapInfo:
    slug: str
    name: str
    mode: str


_MAPS: tuple[MapInfo, ...] = (
    MapInfo("map-01", "404基地", "爆破模式"),
    MapInfo("map-02", "88区", "爆破模式"),
    MapInfo("map-03", "欧拉港口", "爆破模式"),
    MapInfo("map-04", "风曳镇", "爆破模式"),
    MapInfo("map-05", "空间实验室", "爆破模式"),
    MapInfo("map-06", "柯西街区", "爆破模式"),
    MapInfo("map-07", "科斯迷特", "爆破模式"),
    MapInfo("map-08", "2号仓库", "团竞模式"),
    MapInfo("map-09", "鹿鹿潮玩区", "团竞模式"),
    MapInfo("map-10", "水下发电厂", "团竞模式"),
    MapInfo("map-11", "码头小镇", "团竞模式"),
    MapInfo("map-12", "花明弓道馆", "团竞模式"),
    MapInfo("map-13", "离境区", "推车模式"),
    MapInfo("map-14", "亚克萨工厂", "推车模式"),
    MapInfo("map-15", "簌雪东区", "推车模式"),
    MapInfo("map-16", "洛希街区", "晶源感染"),
    MapInfo("map-17", "迦纳古城", "晶源感染"),
    MapInfo("map-18", "极地研究所", "晶源感染"),
    MapInfo("map-19", "奥卡努斯", "爆破模式"),
    MapInfo("map-20", "莱布伦城", "爆破模式"),
)

_MAP_BY_SLUG: dict[str, MapInfo] = {map_info.slug: map_info for map_info in _MAPS}
_EXPLICIT_MAP_SLUGS: dict[int, str] = {
    200: "map-01",
    201: "map-02",
    202: "map-03",
    203: "map-05",
    204: "map-04",
    205: "map-06",
    206: "map-07",
    207: "map-19",
    208: "map-20",
    11001: "map-16",
    11002: "map-17",
    11003: "map-18",
    11004: "map-05",
    11005: "map-03",
    11006: "map-18",
}
_MODE_NAMES: dict[int, str] = {
    1: "团竞模式",
    2: "爆破模式",
    3: "推车模式",
    4: "晶源感染",
    5: "晶源感染",
    9: "晶源感染",
    30: "团竞模式",
}


def resolve_map(map_id: int) -> MapInfo | None:
    """按站点规则解析地图；无法识别时返回 None。"""
    if map_id in _EXPLICIT_MAP_SLUGS:
        slug = _EXPLICIT_MAP_SLUGS[map_id]
        if slug in _MAP_BY_SLUG:
            return _MAP_BY_SLUG[slug]
        return None

    mode_code = map_id // 100
    if mode_code not in _MODE_NAMES:
        return None
    mode_name = _MODE_NAMES[mode_code]
    mode_maps = [map_info for map_info in _MAPS if map_info.mode == mode_name]
    if not mode_maps:
        return None
    index = (map_id % 100 - 1) % len(mode_maps)
    return mode_maps[index]
