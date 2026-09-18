# 部署与实施记录

[English](deploy_readme.md) | **中文**

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

## 2026-09-18：按原始要求与评分标准完善（0.2）

1. 重新逐条核对原始课程 PDF 的 US1–US11、五项交付物和 Appendix A 评分标准。保留原始规划，给 `docs/system_design.md` 加历史版本说明；课程允许 Python/Java，Python 3.11 不是课程强制版本，JUnit 也并非被课程禁止。
2. 新建 `model/factory.py`、`model/manager.py`、`model/search.py`，将集合、ID、字段规则和搜索 AST/解析全部集中到独立 model 包。controller 和旧 cli 搜索路径保留兼容导出，模型不依赖控制台或文件 IO。
3. PIR 实例构造后禁止普通属性修改和删除；返回字段副本、只读集合视图。新增时返回分配 ID 后的新对象，编辑完整验证后原子替换，失败不修改旧记录，也不消耗 ID。
4. 修复非法 print/delete ID 崩溃、未知编辑字段误报成功、带引号多词搜索失真等实际问题。拒绝重复/缺失/未知/不兼容字段，统一大小写、start 别名、严格分钟精度日期、ASCII 正整数 ID 和命令参数数量。
5. 搜索支持所有文本/时间字段、类型、逻辑优先级和括号。字段、操作符和日期在遍历记录之前验证；空集合也不接受非法条件。明确缺失字段、否定、Unicode casefold 语义，并限制命令长度、搜索长度及嵌套深度。
6. `.pim` 使用严格 UTF-8 JSON：精确 schema、唯一 ID/JSON 键、递增 next_id、禁止非有限数字及符号链接，文件上限 10 MiB。保存采用同目录临时文件、flush/fsync 和 os.replace；加载完整验证后才替换当前状态。
7. 覆盖文件、加载丢弃未保存数据、退出丢弃修改均增加确认；EOF 提示未保存状态，Ctrl-C 取消当前输入。补全 help、用户手册和输出说明。
8. 最终边界检查复现长文件名导致的未捕获 OSError，新增 3 项先失败后通过的回归测试，修复路径检查、覆盖检查和临时文件清理失败的异常边界。清理失败会报告残留临时路径，旧目标文件保持不变；真实 CLI 的长文件名 save/load 后继续 help/exit 流程已验证。
9. 测试扩充到 55 项，涵盖各字段编辑、日期边界、逻辑组合、损坏文件、原子替换失败、取消确认、实际子进程 US1–US11 流程、标准库导入、model 分层约束和覆盖率报告缺失回退。已在 CPython 3.9.6 与 3.12.14 运行通过。配置 GitHub Actions 的 3.9/3.11/3.12 测试矩阵。
10. 更正旧覆盖率摘要：旧 trace 用法未把未执行行计入分母，原先的“100%”不能作为完整覆盖证明。`tools/check_coverage.py` 使用 show_missing=True，当前实际 model 行覆盖率为 411/413（99.52%），包含抽象方法/Protocol 声明的未执行行，不声称分支覆盖率。根目录同时提供 `coverage_report.txt` 和 PDF。
11. 编写编号 SRS、当前设计/API 合约、完整用户/开发者手册、US 与 SRS 双向核对表、评分验收清单、AI 辅助记录和汇报脚本。更新两个独立 Mermaid 文件；设计 PDF 包含架构图、类关系图、同一示例中的搜索与更新时序图和从 Python AST 生成的签名清单。
12. 生成并检查 PDF 文档、6 页可编辑 PPTX 与汇报 PDF。按 PDF/演示稿技能进行逐页渲染核验，修正继承/依赖箭头、标题分页和演示稿验证临时路径。作者工具依赖与纯标准库应用隔离，不作为应用运行依赖或正式源码包依赖。
13. `tools/demo_session.py` 从真实 main.py 子进程采集输出，生成有明确来源说明的控制台演示 MP4，时长 124 秒（2:04），1600×1000。使用视频解码器抽查开头、中段和结尾画面。该视频无配音，不替代要求真人持续露脸、展示学生证的组员汇报录像。
14. 新建交付检查与打包工具：检查文档、视频格式/时长、真实人工核验字段和未填成员标记；材料不完整时拒绝生成 FINAL，允许显式 `--draft` 生成带未完成清单的 REVIEW_DRAFT。提交包排除 .git、缓存、个人 .pim 数据、私有构建材料及作者工具；个人证件/声明原件目录不进入 Git。
15. 更新 README 的运行命令、架构、验证数字、文档/视频链接和打包方式。用户已确认：组员姓名/分工、贡献比例、Lecture 04 资料暂缺，保留待填；未编造审批、签名、身份或贡献比例。
16. 本轮从本地提交 `0bbc0d2` 继续完善；提交与远程同步状态以 Git 历史和 `origin/main` 为准。正式交付仍需下面列出的团队材料，当前成果属于可运行、可审阅版本，不承诺课程满分。
17. 最终审阅包已通过 ZIP 完整性检查；解压到独立临时目录后，55 项测试、覆盖率生成与 compileall 再次通过，模型覆盖率仍为 411/413。正式打包模式已验证会因缺少团队材料而拒绝执行；当前交付为 REVIEW_DRAFT，并附未完成事项清单。

## 2026-09-18：GitHub Actions Python 3.11 覆盖率兼容修复（0.3）

1. 检查 GitHub Actions 运行 `35301951751` 的原始作业日志。Python 3.11 的 54 项应用测试全部通过，唯一失败发生在 `python tools/check_coverage.py`：标准库 `trace` 未为 `model/__init__.py` 生成 `.cover` 文件，旧脚本抛出 `RuntimeError: Missing coverage for __init__.py`。Python 3.12 的测试、覆盖率和 compileall 均成功；矩阵 fail-fast 取消的作业不视为测试失败。
2. 为缺失报告增加回归测试：覆盖率工具现在将未生成 `.cover` 的源码按零命中计入可执行行分母，不再把不同 Python 版本的 `trace` 输出差异误判为程序错误。每次运行前清理旧的 `model.*.cover`，防止过期报告掩盖问题。
3. 将 GitHub Actions 矩阵设为 `fail-fast: false`，确保一个环境失败时仍收集其他 Python 版本的独立结果；更新 `actions/checkout` 和 `actions/setup-python` 到官方 v7 主版本。
4. 自动化测试总数更新为 55；覆盖率保持 411/413（99.52%）。同步更新 README、覆盖率文本/PDF和 6 页演示稿。
5. 提交 `954c3a2` 推送后，GitHub Actions 运行 `35303259313` 完成：Python 3.9、3.11、3.12 三个作业均成功，各自通过 55 项测试、覆盖率脚本和 compileall。托管 CI 状态据此更新。

## 2026-09-18：代码侧中英清理与双语文档（0.4）

1. 核实全部交付源码（`model`、`cli`、`controller`、`storage`、`view`、`tests`、`tools` 下的 `.py`）早已为纯英文：此前提交 `2d2d594`（"Use English CLI messages and help placeholders"）已完成翻译，故任何源码文件均无需改动。
2. 仅存的中文位于过期的自动生成产物中，采用“重新生成”而非手改：
   - `output/demo/session.json` —— 用 `tools/demo_session.py` 从当前英文 `main.py` 重新采集。
   - `output/demo/system_demo.mp4` —— 将 Pillow 装入隔离的受管虚拟环境，用 `tools/render_demo_frames.py` 渲染帧，再用 `tools/encode_demo.swift` 编码；产出 124 秒、1600×1000 的全英文 MP4。
   - 删除源码目录下 22 个过期 `.cover` 追踪文件与 `.coverage/` 缓存（均被 Git 忽略，可再生）。
3. 坑：`encode_demo.swift` 直接写已存在的目标路径会报 AVFoundation "Cannot Save (-11823)"，需先编码到临时路径再移动覆盖。
4. 确认课程要求中“仅使用 Java/Python 标准库”一条约束的是实现本体：`model`、`controller`、`cli`、`storage`、`view`、`main.py` 只用 Python 标准库。两个非 Python 工具脚本（`tools/build_slides.mjs` 生成 PPTX、`tools/encode_demo.swift` 生成 MP4）属构建/演示工具，已被打包白名单与提交包排除；打包的 4 个工具脚本只用标准库。
5. 新增双语文档：`README.md`（英文，默认）配 `README.zh-CN.md`，`deploy_readme.md`（英文）配 `deploy_readme.zh-CN.md`。每份文件均链接到对应语言版本，便于在 GitHub 上切换中英。
6. 将提交 `7f9745c`（"Regenerate demo transcript and video in English"）推送至 `origin/main`，并验证本地与远程 HEAD 一致。

## 后续正式提交检查清单

- [x] Python 3.9.6 / 3.12.14 完整测试通过，生成真实行覆盖率报告
- [x] SRS、当前设计/API、用户/开发者手册及需求覆盖表提供 PDF
- [x] 6 页汇报 PPTX/PDF、124 秒系统演示 MP4
- [x] 源码与演示产物全英文；README 与实施日志中英双语
- [ ] 核对 Lecture 04 精确章节结构；如教师要求自动提醒，确认 alarm 语义
- [ ] 填写组员姓名、职责、共同商定的贡献比例
- [ ] 使用官方 Honour Declaration，如实声明 AI 辅助并由组员签署
- [ ] 录制不超过 5 分钟的真人汇报，每人至少 1 分钟且满足露脸/学生证要求
- [ ] 团队复核代码与文档，填写真实 review_status 后生成最终 ZIP
- [x] 推送后核验 GitHub Actions 托管 CI（运行 `35303259313`，Python 3.9/3.11/3.12 均成功）
