"""Generate the blog and test report from checked-in source and real evidence."""

import html
import inspect
import json
from pathlib import Path
import sys

import markdown

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from game_logic import first_blocker

summary = json.loads((ROOT / "evidence/test_summary.json").read_text(encoding="utf-8"))
source = json.loads((ROOT / "evidence/source_smoke.json").read_text(encoding="utf-8"))
exe = json.loads((ROOT / "evidence/exe_smoke.json").read_text(encoding="utf-8"))
replay = json.loads((ROOT / "evidence/ui_replay.json").read_text(encoding="utf-8"))
assert summary["failures"] == summary["errors"] == summary["skipped"] == 0
assert source["status"] == exe["status"] == "ok"
manual = json.loads((ROOT / "evidence/manual_playtest.json").read_text(encoding="utf-8"))
manual_rows = "\n".join(
    f"| {item['level']} · {item['name']} | {item['displayed_seconds']} 秒 | {item['clicks']} | {item['hints']} | {item['remaining_lives']}/3 | {'全部通关' if item['result'] == 'all_clear' else '本关通过'} |"
    for item in manual["levels"]
)
manual_table = "| 关卡 | 界面显示用时 | 点击次数 | 提示次数 | 剩余机会 | 界面结果 |\n|---|---:|---:|---:|---|---|\n" + manual_rows
manual_images = "\n\n".join(
    f"![本人试玩：第 {item['level']} 关通关截图]({item['screenshot'].removeprefix('docs/')})"
    for item in manual["levels"]
)
manual_note = "三关界面计时合计 38 秒。这不包含启动、阅读规则、重复尝试、截图整理等总用时，不能直接作为 PSP 的测试与修改耗时。"
manual_confirmation = "本人随后确认：失误机会耗尽后的重新挑战，以及游戏中途重新开始恢复棋盘和 3 次机会，两项测试均正常。本次完整试玩（包括熟悉规则、重试与截图）实际投入约 2 分钟，按本人估算记录。"

test_table = """| 编号 | 操作/测试场景 | 预期结果 | 实际结果 | 是否通过 |
|---|---|---|---|---|
| T01 | 点击前方无遮挡箭头 | 飞出并消失，剩余箭头数减 1 | 四方向规则正确；事件测试验证删除、飞出动画和输入锁 | 通过 |
| T02 | 点击有阻挡的箭头，包括远距离障碍 | 箭头保留，失误机会减 1，显示碰撞反馈 | 四方向远处障碍均检测；棋盘不变，生命 3→2，红色/晃动反馈 | 通过 |
| T03 | 点击边界朝外箭头 | 消失且不越界 | 上下左右边界的规则和鼠标事件均通过，机会保持 3 | 通过 |
| T04 | 消除全部箭头，点击下一关 | 显示通关并进入下一关 | 三关按顺序通过，第三关显示全部通关 | 通过 |
| T05 | 连续三次误点 | 失败并可重试 | 生命变为 0，停止棋盘操作，重试恢复 | 通过 |
| T06 | 游戏中重开当前关 | 布局和失误数恢复 | 当前关索引保留、原始布局恢复、生命 3、计时/动画/提示清空 | 通过 |"""

report = f"""# 测试报告

自动化验证日期：2026-09-16。环境：{summary['os']}，Python {summary['python']}，pygame-ce 2.5.8。本人试玩材料收到日期见后文。

`python tools/verify.py` 实际结果：**{summary['tests']} passed**，0 failures / 0 errors / 0 skipped。
JUnit 记录的测试套件耗时为 {summary['suite_time_seconds']:.3f} 秒；它不等于个人开发耗时。

{test_table}

## 补充验证

- 独立搜索算法核对全部 625 种 2×2 棋盘的路径判断和可解性。
- 4×4、5×5、6×6 各 15 个种子，共 45 个生成布局，逐步移除验证全部可解。
- 三个正式关卡均包含 U/D/L/R，箭头数量分别为 11、18、27。
- 菜单、空格、越界、格子间隙、动画期间的重复点击和关闭事件。
- `tools/capture_evidence.py` 回放了 {len(replay['actions'])} 次鼠标事件，保存 10 张界面截图、39 帧 GIF 和状态日志。
- 源码实际启动：SDL driver={source['driver']}，frozen={source['frozen']}，状态 {source['state']}。
- EXE 实际启动：SDL driver={exe['driver']}，frozen={exe['frozen']}，状态 {exe['state']}，退出码 0。

## 发现的问题和修正

画面检查发现默认中文字体不能正确显示勾号，结果页出现方框；已改为几何线段绘制，并重新生成截图、运行测试与打包。该问题说明逻辑测试通过仍需要检查实际画面。

## 证据和边界

- 原始测试输出：`evidence/test_output.txt`；机器可读结果：`tests.xml`、`test_summary.json`。
- UI 动作与解序列：`evidence/ui_replay.json`。坐标和解序列采用 0 起点。
- 源码和可执行文件启动：`evidence/source_smoke.json`、`evidence/exe_smoke.json`。
- `docs/images/` 根目录中的截图由同一 pygame 程序在 SDL dummy 显示驱动下经过真实事件回放渲染；本人提供的截图另存于 `docs/images/manual/`。
- Windows 驱动测试证明本机能启动和绘制。完整流程由自动事件测试验证，尚不证明其他电脑兼容性。

## 本人三关试玩记录

用户于 {manual['received_date']} 提供了三张实际游戏窗口截图，分别显示第一关通过、第二关通过和第三关全部通关。此日期为收到材料的日期，截图本身未记录操作日期。原图保持不变，并在 `evidence/manual_playtest.json` 中保存 SHA-256 校验值。

{manual_table}

{manual_images}

{manual_note}

{manual_confirmation}

| 手动检查 | 预期结果 | 本人实际反馈 | 证据形式 |
|---|---|---|---|
| T05：失误耗尽后重新挑战 | 失败后可重新挑战 | 已测试，正常 | 本人文字确认 |
| T06：游戏中途重开 | 棋盘恢复初始布局、机会恢复为 3 | 已测试，正常 | 本人文字确认 |

截图直接支持三个关卡的通关结果、点击次数、提示次数与剩余机会；T05、T06 的手动结果来自本人补充确认。静态结果截图不单独证明动画细节或完整点击过程。
"""
(ROOT / "docs/test_report.md").write_text(report, encoding="utf-8")

psp = (ROOT / "docs/psp.md").read_text(encoding="utf-8")
psp_table = psp[psp.index("| 任务"):psp.index("\n\n说明")]
blog = f"""# 一箭又一箭：使用 Python 与 Codex 完成箭头解谜游戏

| 项目 | 内容 |
|---|---|
| 这个作业属于哪个课程 | [2026-01 软件工程与软件工程实践](https://edu.cnblogs.com/campus/fzu/2026-01SoftwareEngineeringandSoftwareEngineeringPractice) |
| 这个作业要求在哪里 | [个人作业（二）：一箭又一箭](https://edu.cnblogs.com/campus/fzu/2026-01SoftwareEngineeringandSoftwareEngineeringPractice/homework/16718) |
| 这个作业的目标 | 使用 Python 和 AIGC 完成“一箭又一箭”小游戏，验证规则、记录开发过程并使用 Git 管理项目 |
| 学号 | 102401314 |
| GitHub 仓库 | [k0n0y/arrow-game](https://github.com/k0n0y/arrow-game) |

> 本稿记录 Codex 辅助开发、本地自动测试和本人提供的三关通关截图。PSP 已按本人要求补充回忆估算，其中试玩约 2 分钟由本人报告，其他阶段为助手估计；个人心得仍可结合实际理解补充。

## 一、项目展示

本项目采用 Python + pygame-ce，实现基础单格箭头玩法。所有界面元素、箭头和关卡均由本项目代码生成，不使用原商业游戏素材。

### 1. 开始界面

开始页面展示规则入口、开始按钮及三关选择。可从第一关开始，也可直接选择关卡练习。

![开始界面](images/01_menu.png)

### 2. 游戏与碰撞反馈

游戏界面显示当前关卡、棋盘、剩余箭头、剩余失误次数、本关用时、提示和重开按钮。

![游戏界面](images/02_playing.png)

下面的向下箭头前方有其他箭头，即使相邻格为空也不能飞出。误点后原箭头保留、格子变红并晃动，机会由 3 次变为 2 次。

![碰撞反馈](images/03_collision.png)

路径畅通时播放飞出动画，箭头数量减一。

![成功飞出后的棋盘](images/05_removed.png)

### 3. 失败、通关与完成

![失败与重试](images/06_failed.png)

![当前关卡通过](images/07_level_clear.png)

![全部通关](images/10_all_clear.png)

### 4. 演示 GIF

![操作演示](images/demo.gif)

以上为实际 pygame 程序通过脚本投递鼠标事件后的渲染结果。GIF 对部分中间操作进行了省略并调整播放节奏，界面计时来自模拟步长，不作为个人试玩速度或开发耗时。

### 5. 本人实际试玩

以下是本人提供的游戏窗口截图，与上方自动回放截图分别保存。材料收到日期为 {manual['received_date']}。

{manual_table}

三关均有通关结果截图，提示次数均为 0。第一关显示剩余 2 次机会，第二、三关各剩余 3 次机会。

{manual_images}

{manual_note}

{manual_confirmation}

## 二、项目简介

### 游戏规则

1. 棋盘由网格组成，每个格子为空或包含上下左右之一的箭头。
2. 点击箭头后沿自身方向检查，直到棋盘边缘。
3. 没有其他箭头阻挡时，当前箭头飞出并消除；有阻挡时保留并扣一次机会。
4. 每关初始有 3 次机会，耗尽后失败；清空棋盘后通关。
5. 重开恢复当前关卡的初始棋盘和全部机会。

### 关卡和界面设计

| 关卡 | 名称 | 大小 | 箭头数量 | 初始可消除箭头 |
|---|---|---|---:|---:|
| 1 | 初见方向 | 4×4 | 11 | 5 |
| 2 | 交错之间 | 5×5 | 18 | 7 |
| 3 | 顺序的答案 | 6×6 | 27 | 13 |

每关均包含四种方向。关卡规模逐步增大；难度感受还需要结合本人试玩评价。界面采用深色背景和不同颜色箭头，右侧集中展示规则、进度和反馈。

### 主要功能和扩展

基础功能覆盖开始、点击消除、碰撞、三次失误、通关、失败、下一关和重开。扩展包括选关、提示高亮、本关计时和 Windows 可执行版。
提示只通过确定性规则查找当前可消除箭头，没有在线调用大模型。图形与逻辑解耦，方便独立测试。

## 三、实现思路

### 数据结构与模块划分

`levels.py` 使用字符串元组保存不可变关卡，U/D/L/R 分别表示四方向，`.` 表示空格。开始游戏时将其复制为二维列表，因此重开不会受到已消除箭头的影响。

`game_logic.py` 实现路径检测、可解性检查和游戏状态；`ArrowGame.py` 实现图形、按钮、鼠标命中、动画与计时。测试无需启动实际桌面窗口也能检查核心规则。

### 核心路径检测

方向通过行列增量统一处理：U=(-1,0)、D=(1,0)、L=(0,-1)、R=(0,1)。从箭头前方第一个格子开始扫描，边界检查在访问数组之前执行。

以下代码摘自本项目实际实现：

```python
{inspect.getsource(first_blocker).strip()}
```

`can_exit()` 先用 `has_arrow()` 排除空格和越界，再检查 `first_blocker()` 是否返回 None。例如 `R..U` 会找到最右侧的 U，因此不能飞出；`R...` 可直接离开。
单次扫描最坏时间为 O(max(R,C))，额外空间为 O(1)。

### 可解关卡

关卡由逆向插入法构造：每次只加入一支当前能直接飞出的箭头。按相反插入顺序删除，即得到一个合法解序列。最终冻结为三个关卡模板，启动时再次校验。

还使用 `solve()` 独立寻找消除顺序。因为删除箭头只会减少障碍，任何当前可执行的消除操作都不会让其他箭头更难离开，所以可以反复删除可消除箭头而不需要回溯。

### 状态与动画

状态包括 MENU、PLAYING、WON、LOST、COMPLETE。只有 PLAYING 允许操作棋盘；非最后关清空进入 WON，最后关清空进入 COMPLETE；生命为 0 进入 LOST。

规则立即决定成功或失败，再由界面根据结果播放约 0.48 秒动画。飞出时位置随时间移动；碰撞时沿箭头方向小幅往返并显示红色提示。动画期间屏蔽棋盘重复点击，重开会同时清除动画。

## 四、AIGC 使用过程

本次使用 **Codex**。以下四条来自同一任务的不同实际开发阶段，不是事后虚构的独立对话。用户提供需求并纠正来源，初始代码和测试由 AI 辅助实现。

| 子任务 | AIGC 技术 | AI 提供的内容 | 实际效果 | 人工参与/修改 |
|---|---|---|---|---|
| 需求澄清 | Codex | 整理 11 项游戏功能、T01—T06 和材料要求，设计模块结构 | 明确最初博客为同学示例，正式截图成为验收依据 | 用户提供正确链接与 6 张截图 |
| 路径与关卡 | Codex | 四方向整条射线扫描、状态机、逆向构造和独立测试 | 首轮 32 项通过；发现第一候选关缺少右箭头后重新筛选 | 暂无学生手工代码修改记录，修正由 Codex 执行 |
| 图形与交互 | Codex | 中文界面、飞出与碰撞动画、事件回放测试 | 40 项阶段测试通过，三关鼠标事件流程完成 | 后续本人提供了三关通关截图，均未使用提示 |
| 画面检查和修正 | Codex | 读取程序截图检查布局与图标 | 发现勾号变方框，改为线段绘制；最终 {summary['tests']} 项测试通过 | 不把 AI 修正记作学生手工修正 |

原始开发记录见 `aigc_log.md`。本次明确遇到的问题包括正式页登录拦截、命令行嵌套引号错误、第一候选关方向不全、结果图标缺字；没有沿用他人博客中的调试经历。

## 五、测试结果

环境：Windows 11 x64、Python {summary['python']}、pygame-ce 2.5.8、pytest 9.1.1。

实际运行：

```powershell
.\\.venv\\Scripts\\python.exe tools/verify.py
```

最终结果为 **{summary['tests']} passed**，无失败、错误或跳过。

{test_table}

补充检查包括 625 种 2×2 棋盘的独立算法核对、45 个不同种子生成关卡的完整解序列验证，以及 {len(replay['actions'])} 次 pygame 事件回放。源码和打包 EXE 都在本机 Windows SDL 图形驱动中启动成功。

自动验证证据：`evidence/test_output.txt`、`test_summary.json`、`ui_replay.json`、`source_smoke.json`、`exe_smoke.json`。本人通关证据：`evidence/manual_playtest.json` 与 `docs/images/manual/` 中的三张原图。本人另外确认 T05 失败重试、T06 中途重开测试均正常；该两项手动结果记录为文字确认。其他机器兼容性尚未实测。

## 六、PSP 时间记录

以下预计值在读取正式截图后、核心编码前制定，单位为小时。实际栏按本人要求采用回忆估算：试玩约 2 分钟由本人报告，其余阶段为 Codex 根据可见参与过程估计，均未进行精确计时。

{psp_table}

需求理解估计 10 分钟，AIGC 沟通与记录估计 10 分钟，GitHub 仓库创建和提交材料沟通归入材料整理，估计 5 分钟；三项不重复计算。加上本人报告的试玩约 2 分钟，个人参与合计估计约 27 分钟（0.45 小时）。

Python 学习、界面实现、路径逻辑和关卡设计四项暂估个人投入为 0：这些环节本次主要由 Codex 执行，对话中未见本人独立操作记录。如实际存在额外学习或修改，应继续补入。

原建议预算为完整开发过程预留 5.25 小时，实际估算仅计个人参与，约 -4.80 小时的差异包含 AI 分工与估算口径变化，不代表精确的效率提升。AI 自动运行、跨日等待及尚未进行的博客发布不计入；后续实际参与需继续追加。详细依据见 `evidence/psp_estimate.json`。

## 七、心得体会

从本次实现可以得到三个具体认识：第一，路径判断中的“检查到边缘”是规则正确性的关键，不能以相邻格为空代替；第二，逻辑与界面分离后，自动化测试可以直接检查规则和状态，事件回放再补充交互验证；第三，逻辑通过不等于显示正确，结果图标缺字就是通过实际画面才发现的问题。

AIGC 在需求拆分、代码实现、构造测试和整理文档方面提供了帮助；生成结果仍需要证据检验。本项目记录了真实发现和修改，也保留了多次 Git 提交，便于查看各阶段的变化。

本人提供的截图表明三个关卡均已通过，提示次数均为 0；第一关显示剩余 2 次机会，另外两关为 3 次。

本人另确认失败重试和中途重开均正常，本次试玩共约 2 分钟。

**本人补充区（发布前填写）**：最容易误判的地方、亲自理解或修改了哪段代码，以及最终学到什么。主观体验待本人补充。

## 八、运行与提交说明

可执行版双击 `ArrowGame.exe`。源码版：

```powershell
py -3.13 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe ArrowGame.py
```

GitHub 已发布至 [k0n0y/arrow-game](https://github.com/k0n0y/arrow-game)，并保留原有五次开发提交。发布博客时仍需要将图片上传至博客园并替换本地相对路径；博客园发布与班级提交尚未完成。

### 资料与素材说明

- 作业规则来自本文首表中的正式作业页及用户提供的完整截图。
- 初始背景参考为 [PIG— 的作业博客](https://www.cnblogs.com/PIG1/p/23001643)，未复制其源码、截图或时间记录。
- 本项目无外部美术或音效素材；所有箭头、界面图形和关卡由代码生成。系统中文字体只在运行时调用，没有将商业字体文件复制到仓库。
"""
(ROOT / "docs/blog.md").write_text(blog, encoding="utf-8")
body = markdown.markdown(blog, extensions=["tables", "fenced_code", "toc"])
page = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>一箭又一箭 · 作业博客预览</title>
<style>
body{font-family:'Microsoft YaHei',system-ui,sans-serif;margin:0;background:#f1f4f5;color:#20303b;line-height:1.8}
main{max-width:940px;margin:35px auto;padding:48px;background:white;border-radius:18px}
h1{font-size:32px;line-height:1.4}h2{border-top:1px solid #e1e7ea;padding-top:28px;margin-top:42px}h3{margin-top:28px}
a{color:#117866}img{display:block;max-width:100%;height:auto;margin:20px auto;border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}td,th{border:1px solid #d8e1e5;padding:9px;text-align:left}th{background:#edf5f2}
pre{background:#15232e;color:#e2eee9;padding:20px;border-radius:12px;overflow:auto;line-height:1.6}
code{font-family:Consolas,monospace}blockquote{margin:20px 0;padding:12px 20px;border-left:4px solid #17836e;background:#edf7f3}
@media(max-width:700px){main{margin:0;padding:22px;border-radius:0}table{display:block;overflow:auto}h1{font-size:26px}}
@media print{body{background:white}main{margin:0;padding:0}img{max-height:650px;object-fit:contain}pre{white-space:pre-wrap}h2,h3{break-after:avoid}}
</style></head><body><main>""" + body + "</main></body></html>"
(ROOT / "docs/blog.html").write_text(page, encoding="utf-8")
print(f"Generated blog.md, blog.html, test_report.md from {summary['tests']} passing tests")
