# 一箭又一箭 · Arrow by Arrow

使用 Python + pygame-ce 实现的单格箭头解谜游戏。观察每支箭头前方的整条路径，按合适顺序消除全部箭头。

项目仓库：[k0n0y/arrow-game](https://github.com/k0n0y/arrow-game)。

![开始界面](docs/images/01_menu.png)

## 运行

### Windows 可执行版

下载 [Windows 游戏程序 ArrowGame.exe](https://github.com/k0n0y/arrow-game/raw/refs/heads/main/ArrowGame.exe)，或在交付压缩包中双击 `ArrowGame.exe`，无需自行安装 Python。适用于 Windows 10/11 x64；已在当前 Windows 11 主机验证启动，其他机器尚未实测。启动器 `RunGame.cmd` 也会优先打开可执行文件。

### 源代码版

开发与验证环境：Windows 11 x64、Python 3.13.15、pygame-ce 2.5.8、pytest 9.1.1。

```powershell
git clone https://github.com/k0n0y/arrow-game.git
cd arrow-game
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ArrowGame.py
```

无需 API Key、账号或网络游戏服务。创建环境和首次下载依赖需要联网，安装后运行不需要联网。
图形和箭头由代码绘制，无需额外图片素材。中文使用 Windows 自带微软雅黑；在其他系统运行源码需要安装可用的中文字体（例如 Noto Sans CJK），其他系统未进行本次实测。

## 操作和规则

| 操作 | 作用 |
|---|---|
| 鼠标左键 | 点击箭头或界面按钮 |
| Enter | 菜单开始 / 通关后下一关 |
| H | 高亮一个当前可以消除的箭头，不扣失误数 |
| R | 重新开始当前关卡，恢复棋盘、3 次机会和计时 |
| Esc | 返回主菜单 |

- 箭头只能沿自身方向飞出。需要检查一直到边缘的整条行/列，不能只看相邻格子。
- 路径畅通：箭头飞出并消除；有其他箭头阻挡：保留原箭头，晃动、变色并扣 1 次机会。
- 每关有 3 次失误机会，耗尽后失败，可重试。
- 点击空格、间隙或棋盘外不扣机会。动画期间棋盘暂停接收点击，避免重复触发。
- 清空棋盘显示通关，点击“下一关”继续；第三关结束显示“全部通关”。

## 功能和关卡

三关分别为 4×4 / 11 支箭、5×5 / 18 支箭、6×6 / 27 支箭，每关均有上下左右四种方向。固定布局由逆向插入算法生成，并经过可解性与逐步移除验证。

扩展功能：关卡选择、提示高亮、本关计时、流畅飞出/碰撞动画、Windows 可执行程序。
提示和求解工具使用确定性算法，不调用大模型，也不称为 AI 自动求解。

![游戏界面](docs/images/02_playing.png)
![演示 GIF](docs/images/demo.gif)

GIF 为实际 pygame 事件回放生成的渲染帧，省略部分中间操作并调整播放节奏；不代表学生本人试玩时长。

## 测试与复现

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools/verify.py
.\.venv\Scripts\python.exe tools/capture_evidence.py
```

测试包含老师指定的 T01—T06、四方向与远距离障碍、负索引与棋盘边界、死锁、重开隔离、动画输入锁、完整三关事件回放。
额外将全部 625 种 2×2 棋盘与独立搜索算法核对，并验证 45 个生成关卡。
详见 [测试报告](docs/test_report.md) 和 `evidence/test_output.txt`，不要仅凭程序可启动判断规则正确。

重新打包：

```powershell
.\.venv\Scripts\python.exe tools/build_exe.py
```

输出位于 `dist/ArrowGame.exe`。开发依赖包含 Pillow（仅用于生成 GIF）、Markdown（仅用于博客预览），游戏本身只依赖 pygame-ce。

## 项目结构

```text
ArrowGame.py               界面、输入、动画和主循环
game_logic.py              规则、关卡校验、状态机和确定性求解
levels.py                  三个不可变关卡模板
tests/                     规则与 pygame 事件测试
tools/                     复现、截图、打包和文档生成工具
docs/images/               实际渲染截图与演示 GIF
docs/blog.md               博客园 Markdown 稿
docs/blog.html             本地阅读预览
docs/test_report.md        测试结果与证据边界
docs/code_guide.md         核心代码讲解与答辩准备
docs/psp.md                PSP 预算与个人参与时间参考估算
docs/submission_checklist.md  发布与本人验收清单
aigc_log.md                真实开发阶段记录
evidence/                  测试日志、事件回放、启动验证
```

## AIGC、来源和状态

本项目在 Codex 辅助下独立实现。界面、箭头和关卡均由本项目代码创建，未使用商业游戏素材或复制他人的完整项目。

- 正式要求：用户提供的 6 张截图，对应 [个人作业（二）](https://edu.cnblogs.com/campus/fzu/2026-01SoftwareEngineeringandSoftwareEngineeringPractice/homework/16718)。
- 背景参考：用户最初提供 [PIG— 的作业博客](https://www.cnblogs.com/PIG1/p/23001643)，用于了解任务背景；未使用其项目源码、图片、PSP 时间或经验描述。
- 实际 AI 作用、修正与验证：[aigc_log.md](aigc_log.md)。
- GitHub 已发布至 [k0n0y/arrow-game](https://github.com/k0n0y/arrow-game)，原有开发提交历史完整保留；公开文件及图片的核验记录见 `evidence/github_publication.json`（记录的是其中标明的提交快照）。博客园发布和班级作业提交尚未完成。

本人已提供三关通关截图，均未使用提示；界面分别显示 8 秒、12 秒、18 秒。原始图片见 `docs/images/manual/`，记录见 [测试报告](docs/test_report.md)。本人另确认失败重试和中途重开均正常，并报告本次完整试玩约 2 分钟。PSP 现采用用户选用的参考估算，合计 152 分钟（约 2.53 小时），未逐项计时；只有试玩约 2 分钟由本人报告，其余数值和活动完成情况待按实际经历核对。个人心得与后续实际投入可继续补充。
