# 用户手册

启动：`python3 main.py`。

## 命令

- `add text "内容"`
- `add task "描述" --deadline YYYY-MM-DD HH:MM`
- `add event "描述" --start YYYY-MM-DD HH:MM --alarm YYYY-MM-DD HH:MM`
- `add contact --name 姓名 --address "地址" --mobile 手机号`
- `edit <id> --field value`（字段按 PIR 类型填写）
- `search "条件"`（支持 `contains`、`= != < <= > >=`、`&& || !` 和括号）
- `print <id>` 或 `print all`
- `delete <id>`
- `save [文件名]`（省略时为 `pim.pim`）
- `load <文件名>`、`help`、`exit`

ID 从 1 开始递增，删除后不会复用。非法命令、未知 ID、缺失字段和损坏文件会输出中文错误提示并返回命令循环。
