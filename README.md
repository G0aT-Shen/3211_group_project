# COMP3211 Personal Information Management System

这是 COMP3211 软件工程课程项目的命令行个人信息管理系统（PIM）。项目采用 Python 标准库实现，按 MVC + 分层结构组织代码，支持文本、任务、事件和联系人四类个人信息记录。

## 环境

- Python 3.9+ 可运行；课程目标环境为 Python 3.11+
- 仅使用 Python 标准库，无第三方依赖

## 运行

```bash
python3 main.py
```

在 `pim>` 提示符下可使用：

```text
add text "买牛奶"
add task "提交报告" --deadline 2026-11-19 20:00
add event "组会" --start 2026-10-12 09:00 --alarm 2026-10-12 08:30
add contact --name 张三 --address "香港红磡" --mobile 61234567
edit 1 --text "买咖啡"
search "type = task && deadline < 2026-12-01"
print all
print 1
delete 1
save [文件名]
load 文件名
help
exit
```

`.pim` 文件使用带 `schema_version`、`next_id` 和 `pirs` 的 JSON 格式。

## 测试与覆盖率

```bash
python3 -m unittest discover -v
python3 -m trace --count --summary --coverdir .coverage --module unittest discover > coverage_report.txt
```

需求映射见 [requirements_coverage.md](requirements_coverage.md)，系统设计见 [docs/system_design.md](docs/system_design.md)。每次实施记录见 [deploy_readme.md](deploy_readme.md)。
