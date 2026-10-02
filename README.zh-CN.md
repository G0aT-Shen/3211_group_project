# COMP3211 个人信息管理系统

[English](README.md) | **中文**

Python 标准库实现的命令行个人信息管理系统，支持文本、任务、事件、联系人，以及类型/字段搜索、编辑、打印、删除和 `.pim` 保存/加载。

## 运行与验证

支持 Python 3.9+。已在 macOS 的 Python 3.9.6 和 3.12.14 验证，无运行时第三方依赖。

当前本地验证（2026 年 10 月 1 日代码审查修复）：Python 3.9.6 和 3.12.14 下均有 73 项自动化测试通过；最新测得模型行覆盖率 436/438（99.54%，包含未执行行）。草稿归档解压后也通过全部 73 项测试。仓库中的覆盖率文本、PDF 和 PPTX 仍为此前生成的快照，最终提交前请按开发手册重新生成。GitHub Actions 运行 `35303259313` 已在 Python 3.9、3.11 和 3.12 上通过更早版本的测试、覆盖率检查与 `compileall`。

```bash
python3 main.py
python3 -m unittest discover -v
python3 tools/check_coverage.py
```

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
