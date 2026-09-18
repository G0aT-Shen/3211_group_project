# 部署与实施记录

本文件按时间顺序记录项目实施、验证和文档更新。时间以本机（Asia/Hong_Kong）为准。

## 2026-09-18

1. 检查本地项目目录，确认原始内容包括课程项目 PDF 和中文项目说明总结。
2. 核对 GitHub 仓库 `G0aT-Shen/3211_group_project`，初始化本地 Git，关联 `origin`，同步 `main` 分支，并验证本地与远程提交一致。
3. 阅读 `docs/system_design.md`。将其中的 Python 3.11+、标准库、MVC 分层、四类 PIR、JSON `.pim`、搜索表达式和 T01–T05 任务分解作为实现蓝图；文档中的设计假设不视为额外用户指令。
4. 创建模型层：`model/` 下的 `PIR` 抽象基类、`TextPIR`、`TaskPIR`、`EventPIR`、`ContactPIR`、领域异常和日期解析工具。
5. 创建控制器和存储层：`PIMManager`、`PIRFactory`、JSON `Storage`，实现单调递增 ID、CRUD、搜索编排、序列化和 `.pim` 文件读写。
6. 创建命令交互和视图层：`CommandParser`、递归下降 `SearchParser`、搜索 AST、`Printer`、`Repl` 和 `main.py`。支持 `contains`、时间比较、`&&`、`||`、`!`、括号和四类 PIR 命令。
7. 创建 12 个标准库 `unittest` 测试，覆盖模型、搜索、控制器和存储；首次运行发现当前 macOS Python 3.9 不兼容 PEP 604 联合类型注解，随后加入延迟注解以兼容 Python 3.9+。
8. 验证结果：`python3 -m unittest discover -v` 通过 12/12；CLI 冒烟测试完成 add、search、edit、print、save、delete、load、exit 全流程。
9. 使用 `python3 -m trace --count --summary --coverdir .coverage --module unittest discover > coverage_report.txt` 生成覆盖率摘要；将 trace 产生的明细目录设为忽略文件，保留根目录摘要作为交付物。
10. 更新 `README.md`，补充环境、运行命令、CLI 示例、测试和覆盖率命令；本文件用于持续记录后续每次改动。
11. 修正 `edit event --start` 到模型 `start_time` 的字段映射，允许搜索表达式末尾空格，并将覆盖率命令改为 `--coverdir .coverage`，避免污染系统 Python 安装目录。
12. 最终验证：12 个单元测试通过；`compileall` 无语法错误；覆盖率摘要成功生成；当前工作区仅包含本次实现、文档和测试新增/修改，未执行远程推送。

## 后续部署检查清单

- [ ] 在 Python 3.11+ 环境重新运行完整测试
- [ ] 生成并审阅 `coverage_report.txt`
- [ ] 补齐 SRS、完整设计文档、用户手册和开发者手册
- [ ] 根据团队分工制作演示 PPT/录像、Honour Declaration 和最终 ZIP
