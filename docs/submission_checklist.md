# 提交前清单

## 已完成的本地工作

- Python 源码、三关、中文图形界面、动画、失败与重开、提示和关卡选择。
- 44 个自动测试通过，老师的 T01—T06 均有覆盖。
- 64 次实际 pygame 鼠标事件回放，保存截图、GIF 与状态变化。
- 本机 Windows 图形驱动下源码和 EXE 启动成功。
- 分阶段的本地 Git 提交，以及 README、AIGC、测试报告、博客稿与代码讲解。

## 需要本人完成/提供的信息

- [ ] 双击 `ArrowGame.exe` 实际试玩三个关卡，记录结果。自动回放不代替正式要求中的本人试玩。
- [ ] 核对博客学号。当前根据此前提供的信息预填为 **102401314**，姓名为曾炜毅。
- [ ] 阅读 `code_guide.md`，确保能说明核心算法、AI 的作用及实际改动。
- [ ] 按真实耗时填写 `psp.md`，差异为“实际 − 预计”；预算 5.25 小时是事前建议值，不是已经发生的个人用时。
- [ ] 按实际理解和试玩经历修改博客“心得体会”。
- [x] 在 GitHub 建立空白公开仓库：[k0n0y/arrow-game](https://github.com/k0n0y/arrow-game)。
- [x] 上传并验证仓库的源码、图片和开发提交历史，原有五次提交完整保留。
- [x] 把真实仓库链接写入博客首表。现有 Git 记录须保留，不要重新初始化后一次性上传。
- [ ] 发布博客时上传 `docs/images/` 的截图/GIF，并替换 Markdown 中本地相对图片路径。
- [ ] 将最终博客 URL 提交到班级作业页，确认页面显示提交成功。

## GitHub 上传（在原项目目录保留历史）

远端仓库已经创建并上传，原项目目录已配置 `origin` 和 GitHub 登录。后续修改提交后可执行：

```powershell
git push -u origin main
```

如收到 `remote origin already exists`，先 `git remote -v` 核对，不要盲目覆盖远端。
需使用 GitHub 正常登录授权；不要将密码或 Token 写进项目。

源码包中的 `ArrowGame-history.bundle` 保存本次开发历史。换到其他目录恢复：

```powershell
git clone ArrowGame-history.bundle ArrowGame
cd ArrowGame
git remote remove origin
git remote add origin https://github.com/k0n0y/arrow-game.git
git push -u origin main
```

## 当前在线状态

公开仓库源码、图片和原有开发历史已上传并核验：[k0n0y/arrow-game](https://github.com/k0n0y/arrow-game)。核验快照记录见 `evidence/github_publication.json`。博客园发布和班级作业提交尚未记录成功证据。
