# 开发者手册

## 环境与依赖

项目使用 Python 3.11+ 作为课程目标环境，当前代码也兼容 Python 3.9+；不需要安装第三方包。

## 运行、测试和覆盖率

```bash
python3 main.py
python3 -m unittest discover -v
python3 -m trace --count --summary --coverdir .coverage --module unittest discover > coverage_report.txt
```

模型代码在独立的 `model` 包中。控制器、CLI、存储和视图分别位于 `controller/`、`cli/`、`storage/`、`view/`。`.pim` 文件为 UTF-8 JSON，包含 `schema_version`、`next_id` 和 `pirs`。
