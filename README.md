# RepiKo
 一个基于 OneBot 的复读机

## 安装

- 安装 Python 3.10
- 克隆此分支
- 安装 [PDM](https://pdm.fming.dev/latest/)，然后 `pdm install`

- 运行一个 [OneBot](https://onebot.dev/) 实现，如 [go-cqhttp](https://docs.go-cqhttp.org/)
- 初次运行会在 `./config` 下生成一些配置文件，可按需修改
- ~~通过某些手段使程序正常运行（逃~~

#### 可选部分

- 新建 `font` 目录，放入喜欢的字体（对应修改配置）
- 安装 ygopro 或从[仓库](https://github.com/mycard/ygopro/tree/server)获取相关文件
<!-- - `pdm install -G svg`
  如果失败，尝试先安装 [cairo](https://www.cairographics.org/download/) -->
- `pdm install -G img`

## 运行

- `pdm run app`
  详细可参照 `bot.bat` 或 `bot.py`


> 有待修缮
