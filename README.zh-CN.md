# COMP3211 个人信息管理系统

[English](README.md) | **中文**

Python 标准库实现的命令行个人信息管理系统，支持文本、任务、事件、联系人，以及类型/字段搜索、编辑、打印、删除和 `.pim` 保存/加载。

## 运行与验证

支持 Python 3.9+，无运行时第三方依赖。本轮在 macOS 的 Python 3.9.6 和 3.12.14 验证；上一轮审查版本曾在 Windows 的 Python 3.12.10 和 3.12.14 验证。

当前本地验证（2026 年 10 月 12 日 Windows 适配）：macOS 两套 Python 均通过 133 项测试套件，零失败、零错误，仅真实 Windows CMD 启动器测试跳过。Python 3.12.14 的模型行覆盖率为 436/440（99.09%）。此前 DSH 修复的 Unicode 空白、转义尾空格和 Unicode 前缀文件名问题仍由 22 项回归测试覆盖。本轮加入 UTF-8 启动器、在访问文件前拒绝 Windows 保留设备名和备用数据流、修正子进程测试对默认编码的依赖，并检查中文目录及 CRLF 文件和命令。CI 已配置 Windows、macOS、Ubuntu 与 Python 3.9/3.11/3.12 的矩阵，Windows 作业同时检查启动器。本轮尚待实际 Windows 和远程 CI 验证；现有 PDF/PPTX 仍为较早快照。

```bash
python3 main.py
python3 -m unittest discover -v
python3 tools/check_coverage.py
```

Windows 请先将 ZIP 解压到可写目录，在该目录打开 PowerShell：

```powershell
.\run_windows.cmd
.\run_windows.cmd --check
```

第一条启动应用；第二条运行完整测试、刷新 `coverage_report.txt` 并检查 Python 语法，失败时返回非零状态。脚本从 PATH 或 `py -3` 启动器选择 Python 3.9+，启用 UTF-8；从其他目录启动时也会使用项目目录作为工作目录。在 CMD 中可直接输入 `run_windows.cmd`，也可双击脚本启动应用。无需 pip 安装。手动执行其他命令时，将 `python3` 换为 `py -3 -X utf8`。

应用命令应输入在 `pim>` 提示符后。各系统使用相同的引号和转义规则，因此 Windows 反斜杠路径请用单引号括起；正斜杠路径也可用。例如：`save 'C:\Users\Professor\Desktop\review folder\records.pim'`。目标目录必须已存在；相对路径保存的 `.pim` 文件可在 macOS 与 Windows 互读。Windows 会拒绝 `CON.pim` 等设备名、备用数据流、非法字符、路径组件末尾的空格或句点，以及设备/扩展命名空间路径（`\\.\`、`\\?\`）；请使用普通本地或 UNC 路径。

```text
add text "Buy milk"
add task "Submit report" --deadline 2026-11-19 20:00
add event "Group meeting" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30
add contact --name "Zhang San" --address "Hung Hom, Hong Kong" --mobile "+852 61234567"
search text contains "Buy milk"
search type = task && deadline < 2026-12-01
edit 2 --deadline 2026-11-20 12:00
print all
save records.pim
load records.pim
exit
```

输入 `help` 查看全部用法。覆盖文件、加载替换未保存数据或退出时，按提示输入 `y` 确认。`alarm` 是保存并可搜索的时间字段，本版本不触发系统通知。时间精度为分钟、不含时区；纯日期代表午夜。

## 架构与可靠性

`model` 包集中所有业务模型、ID 管理、字段验证与搜索 AST，独立于 IO。`cli` 负责命令和交互，`storage` 负责严格 JSON 与原子保存，`view` 负责格式化；`controller` 保留为兼容导入入口。

未知/重复字段、非法 ID、错误日期和损坏文件会明确报错。编辑全部验证后才生效；保存失败保留旧文件，加载失败保留当前数据。限制和使用细节见用户手册。

## 文档与提交状态

- [SRS](docs/SRS.md)、[当前设计/API](docs/design.md)、[用户手册](docs/user_manual.md)、[开发者手册](docs/dev_manual.md)
- [US 与 SRS 覆盖表](requirements_coverage.md)、[模型行覆盖率 PDF](coverage_report.pdf) 与 [可重现文本报告](coverage_report.txt)
- [评分验收清单](docs/submission_checklist.md)、[AI 使用记录](docs/ai_usage.md)、[实施日志](deploy_readme.zh-CN.md)（[English](deploy_readme.md)）
- [演示脚本与分工待填项](docs/presentation_script.md)
- [PDF 文档](output/pdf/)、[演示稿 PDF](output/presentation/PIM_presentation.pdf) 与 [可编辑 PPTX](output/presentation/PIM_presentation.pptx)
- [2 分 04 秒实际 CLI 输出演示](output/demo/system_demo.mp4)（无配音；非组员露脸汇报录像）

早期 [system_design.md](docs/system_design.md) 是历史规划，当前实现以 `docs/design.md` 为准。覆盖率工具统计未执行行，不能用原先的 trace 摘要“100%”判断代码质量。

运行 `python3 tools/check_submission.py` 检查交付完整性。成员身份、贡献比例、Lecture 04 结构核对、官方 Honour Declaration 和真人露脸录像仍需组员完成。所有 AI 辅助内容应如实声明；测试通过不等同于保证课程得分。

生成可审阅但非最终版的压缩包：`python3 tools/package_submission.py --draft`。输出位于 `submission/`，包含未完成事项清单；不带 `--draft` 时会拒绝打包不完整的正式提交。按 `docs/review_status.example.json` 记录真实人工核验结果；不要在未检查时将字段改为 true。
