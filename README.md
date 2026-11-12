# CalabiyauUID

<p align="center">
  <a href="ICON.png">
    <img src="ICON.png" width="162" height="162" alt="CalabiyauUID">
  </a>
</p>
<h1 align="center">CalabiyauUID 0.1.0</h1>
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

本仓库是 [sssysy/CalabiyauUID](https://github.com/sssysy/CalabiyauUID) 的修改版，基于原作者的 `b6eb773` 版本继续补全功能，并沿用 GPL-3.0 许可证。插件的原始设计与代码版权归原作者 [sssysy](https://github.com/sssysy) 所有。

主要改动：

- 新增 `kq切换`：在已绑定账号间切换，可指定 UID，也可按顺序切到下一个
- 新增 `kq帮助`：按早柚插件通用风格生成的命令帮助图
- `kq绑定`、`kq战绩总览`、`kq历史战绩`、`kq刷新数据` 支持用昵称查询（精确匹配优先，其次前缀匹配，有重名时列出候选）
- 战绩总览卡新增「常组队友」和「常遇对手」，没有数据时不显示
- 请求 dakanu 时带上常见浏览器请求头，避免被识别为自动化请求而返回 429
- 增加搜索缓存（约 10 分钟）、档案缓存（约 90 秒），超时或 5xx 时重试一次
- 指定玩家查询时，本地没有快照会先读取站点缓存
- 修复刷新接口返回 HTTP 202（已受理）时被误判为失败，导致绑定提示「暂时没有读到玩家缓存」
- 修复帮助图示例重复显示 `kq` 前缀

## 丨安装提醒

> **注意：该插件为 [早柚核心(gsuid_core)](https://github.com/Genshin-bots/gsuid_core) 的扩展，具体安装方式可参考上方安装文档**
>
> 🚧 项目快速迭代中，有漏洞可提issue或pr 🚧

> [!CAUTION]
> 项目还在早期开发阶段，部分功能可能报错或不可用！如遇到请等待后续更新

## 丨命令列表

<details><summary>绑定登录</summary>

| 命令 | 说明 |
|------|:------:|
| `kq绑定 1234567` / `kq绑定 玩家昵称` | 绑定卡拉彼丘(国服)账号，支持 UID 或昵称 |
| `kq解绑 1234567` | 解绑卡拉彼丘(国服)账号 |
| `kq查看` | 查看当前已绑定的卡拉彼丘(国服)账号 |
| `kq切换 1234567` | 在已绑定账号间切换到指定 UID |
| `kq切换` | 按绑定顺序切换到下一个账号 |
| `kq战绩总览` | 查看当前账号的生涯总览卡片，也可 @ 用户查询 |
| `kq战绩总览 1234567` / `kq战绩总览 玩家昵称` | 查看指定 UID 或昵称的生涯总览卡片 |
| `kq历史战绩` | 查看当前账号最近 8 场对局 |
| `kq历史战绩 1234567` / `kq历史战绩 玩家昵称` | 查看指定 UID 或昵称最近 8 场对局 |
| `kq刷新数据` | 刷新当前账号战绩 |
| `kq刷新数据 1234567` / `kq刷新数据 玩家昵称` | 刷新指定 UID 或昵称的战绩 |
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
