# CalabiyauUID

<p align="center">
  <a href="ICON.png">
    <img src="ICON.png" width="162" height="162" alt="CalabiyauUID">
  </a>
</p>
<h1 align="center">CalabiyauUID</h1>
<h4 align="center">基于 gsuid_core 的 全功能卡拉彼丘插件</h4>

<p align="center">
  <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.12+-blue" alt="Python 3.12+"></a>
  <a href="https://github.com/Genshin-bots/gsuid_core" target="_blank"><img src="https://img.shields.io/badge/gsuid_core-0.11.0+-orange" alt="gsuid_core 0.11.0+"></a>
</p>

<div align="center">
  <a href="https://docs.sayu-bot.com/" target="_blank">安装文档</a> &nbsp; · &nbsp;
  <a href="https://github.com/Genshin-bots/gsuid_core" target="_blank">gsuid_core</a>
</div>

## 丨关于本仓库

本仓库是 [sssysy/CalabiyauUID](https://github.com/sssysy/CalabiyauUID) 的修改版，基于原作者的 `b6eb773` 版本继续补全功能，并沿用 GPL-3.0 许可证。

主要改动：

- 新增 `kq切换`：在已绑定账号间切换，可指定 UID，也可按顺序切到下一个
- 新增 `kq帮助`：按早柚插件通用风格生成的命令帮助图
- `kq绑定`、`kq战绩总览`、`kq历史战绩`、`kq刷新数据` 支持用昵称查询（精确匹配优先，其次前缀匹配，有重名时列出候选）
- 战绩总览卡新增「常组队友」和「常遇对手」，没有数据时不显示
- 新增 Dakanu 公开查询：多类型排行榜、超弦体排行、全服组队好友榜、战队资料与成员、指定对局详情
- 总览支持按站点赛季标签查看生涯数据；战绩总览、历史战绩、刷新、对局、排行榜和公开榜单可指定 `国际服` 或 `国服`
- 总览卡补充在线状态、勋章，并在挑战赛接口冷却时回退读取赛季接口数据
- 请求 dakanu 时带上常见浏览器请求头，避免被识别为自动化请求而返回 429
- 增加搜索缓存（约 10 分钟）、档案缓存（约 90 秒），超时或 5xx 时重试一次
- 指定玩家查询时，本地没有快照会先读取站点缓存
- 修复刷新接口返回 HTTP 202（已受理）时被误判为失败，导致绑定提示「暂时没有读到玩家缓存」
- 修复帮助图示例重复显示 `kq` 前缀

## 丨安装提醒

> **注意：该插件为 [早柚核心(gsuid_core)](https://github.com/Genshin-bots/gsuid_core) 的扩展，具体安装方式可参考上方安装文档**
>
> 🚧 项目快速迭代中，有漏洞可提issue或pr 🚧

## 丨命令列表

<details><summary>绑定登录</summary>

| 命令 | 说明 |
|------|:------:|
| `kq绑定 1234567` / `kq绑定 玩家昵称` | 绑定卡拉彼丘(国服)账号，支持 UID 或昵称 |
| `kq解绑 1234567` | 解绑卡拉彼丘(国服)账号 |
| `kq查看` | 查看当前已绑定的卡拉彼丘(国服)账号 |
| `kq切换 1234567` | 在已绑定账号间切换到指定 UID |
| `kq切换` | 按绑定顺序切换到下一个账号 |
| `kq战绩总览` | 查看当前绑定账号的生涯总览卡片，也可 @ 用户查询 |
| `kq战绩总览 1234567` / `kq战绩总览 玩家昵称` | 查看指定 UID 或昵称的生涯总览卡片，昵称精确匹配优先 |
| `kq战绩总览 S26EP4` | 查看当前绑定账号指定赛季生涯；赛季标签以 Dakanu 为准 |
| `kq战绩总览 玩家昵称 S26EP3 国际服` | 查询指定国际服玩家的指定赛季生涯 |
| `kq历史战绩` | 查看当前绑定账号最近 8 场对局 |
| `kq历史战绩 玩家昵称 国际服` | 查看指定国际服玩家最近 8 场对局 |
| `kq刷新数据` | 刷新当前绑定账号战绩 |
| `kq刷新数据 玩家昵称 国际服` | 刷新指定国际服玩家战绩 |
| `kq排行榜` | 查看当前赛季段位榜前 20 名 |
| `kq排行榜 挑战榜 S26EP4` | 查看指定赛季挑战榜；也可使用 `段位榜`、`团队乱斗榜`、`极限推进榜`、`晶源感染榜` |
| `kq段位榜 国际服` / `kq挑战榜` | 查看对应类型排行榜；支持 `kq团队乱斗榜`、`kq极限推进榜`、`kq晶源感染榜` |
| `kq角色排行` | 查看排位超弦体排行与最多 3 张地图的攻防阵容摘要 |
| `kq角色排行 国际服` / `kq角色排行 全模式` | 指定区服或查看全部模式角色排行 |
| `kq好友榜` | 查看全服组队组合榜（不是社交好友列表） |
| `kq战队 战队名称` / `kq战队 战队ID` | 查看战队资料和成员；重名时按候选中的 ID 查询 |
| `kq对局 对局编号` | 查看指定对局详情，默认使用当前绑定账号作为视角 |
| `kq对局 对局编号 玩家昵称 国际服` | 指定视角玩家和区服；`kq对局详情` 为同义入口 |
| `kq帮助` | 查看插件命令帮助 |

</details>

## 丨其他

- 本项目仅供学习使用，请勿用于商业用途
- [GPL-3.0 License](LICENSE)

## 致谢
| 贡献者 | 引用 |
|:------:|:------:|
| [sssysy](https://github.com/sssysy) | 原插件作者，[CalabiyauUID](https://github.com/sssysy/CalabiyauUID) |
| [CSAHuan](https://github.com/CSAHuan) | 功能参考，[dsh-klbq](https://github.com/CSAHuan/dsh-klbq) |
| [Wuyi 无疑](https://github.com/KimigaiiWuyi) | 框架作者 |
| [gsuid_core](https://github.com/Genshin-bots/gsuid_core) | 插件依赖框架 |
| [dakanu](https://www.dakanu.com/) | 数据查询接口 |
| [白泉幽奈](https://space.bilibili.com/2198) | 数据接口作者 |
| [卡拉彼丘表情包](https://wiki.biligame.com/klbq/%E8%A1%A8%E6%83%85%E5%8C%85) | 帮助图和部分图片表情来源 |
