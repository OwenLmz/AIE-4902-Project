# 智慧校园图书馆智能位控系统中期报告草稿

日期：2026-06-26

## 1. 项目概述

本项目面向智慧校园场景，目标是构建一个“图书馆智能位控系统”的课程 MVP 原型。项目关注的问题是：图书馆自习座位资源有限，但学生常常难以及时知道哪些座位真正空闲，管理员也难以及时识别长期有物无人、疑似占座的情况。

当前项目不追求生产级系统，而是验证一条可运行的数据闭环：

```text
图像或 mock 检测结果 -> 座位映射 -> 座位状态机 -> 人流分析 -> Streamlit Dashboard
```

系统核心不是单独训练模型，而是将 AI 检测、座位空间映射、时序规则和前端可视化连接起来。当前 Dashboard 使用 mock / 示例数据进行原型验证，尚未接入学校真实摄像头、真实闸机系统或真实后端 API。

## 2. 需求与成功标准

学生端主要需求是快速查看图书馆座位状态，包括当前馆内人数、图书馆容量、空闲座位数、拥挤等级、楼层区域概览和座位布局图。学生端不展示检测细节，不展示摄像头原图，不展示个人身份信息。

管理员端当前定位为“查看与定位”基础版，主要需求是查看暂不可用和疑似占座座位，选择异常座位后定位到对应楼层、区域和摄像头视角下的 Polygon 座位图，并查看检测依据，例如是否检测到人、是否检测到物品、无人有物持续时间和最后更新时间。

当前阶段明确不实现管理员确认占座、标记误判、暂不处理、操作日志和处理状态，因为这些功能需要真实后端字段和持久化设计支持。为了避免误导，本 MVP 不在前端伪造这些处理结果。

本阶段成功标准包括：

- Dashboard 可以运行；
- 学生视图和管理员视图均可展示；
- 数据通过统一 `data_provider.py` 进入页面；
- 不显示无意义指标、随机业务数据、假处理状态和敏感信息；
- 自动测试、编译检查和 Streamlit 健康检查通过；
- 中期 evidence 可追溯到代码、文档、测试或截图。

## 3. 技术路线与系统架构

项目采用 Python 为主的 MVP 技术路线。检测层使用 YOLOv8 / mock 检测，座位映射使用 `seat_id + polygon`，座位状态判断使用规则状态机，人流统计使用模拟闸机数据或 crowd JSON，前端展示使用 Streamlit。

当前项目结构如下：

- `src/detection/`：检测逻辑，支持 YOLOv8 和 mock 输出；
- `src/seat_mapping/`：座位映射逻辑；
- `src/state_machine/`：座位状态机；
- `src/utils/`：IO 和人流统计；
- `src/dashboard/`：Streamlit Dashboard；
- `tests/`：自动测试；
- `docs/`：PRD、技术说明、验收与中期报告材料。

数据流上，检测结果会先输出为 JSON，再经过座位映射得到每个座位的检测情况。状态机根据“是否有人”“是否有物品”“无人有物持续时间”等信息输出座位状态。Dashboard 通过 `data_provider.py` 读取 `output/seat_status.json`、`output/crowd_status.json` 和 `src/data/seats.json`，统一字段后再交给页面组件展示。

座位布局图使用 Polygon 绘制。由于不同摄像头的图像坐标系不同，当前实现按 `floor + zone + camera_id` 分组渲染，避免把不同摄像头的 polygon 强行合并到同一坐标系中。

## 4. 当前已完成工作

### 4.1 PRD 与技术文档

项目已形成 MVP PRD 和技术说明，明确了项目目标、非目标、状态机规则和运行方式。对应证据包括 `docs/PRD.md` 和 `docs/TECH.md`。

### 4.2 数据适配层

Dashboard 数据统一层位于 `src/dashboard/data_provider.py`。该模块负责读取座位状态、人流状态和座位布局数据，并统一字段模型。它支持旧字段兼容，例如 `object_unattended_minutes`、`suspect_duration`、`latest.total_in_library` 和 `current_num`。它也会返回 `errors` 和 `warnings`，避免页面在数据缺失或异常时显示误导性默认值。

### 4.3 学生视图

学生视图已实现数据来源状态、核心指标、楼层与区域概览、楼层 / 区域筛选、Polygon 座位布局、人流趋势图和座位列表预览。学生端只显示对学生有意义的信息，不显示 `has_person`、`has_object`、`unattended_minutes`、polygon 原始坐标或个人身份信息。

### 4.4 管理员视图

管理员视图已实现基础查看与定位能力。当前页面包括管理员状态区、管理概览、异常座位列表、异常座位选择器、Polygon 高亮定位图和异常座位详情。异常列表只包含 `POSSIBLY_OCCUPIED` 和 `SUSPICIOUS`，并按疑似占座优先、无人有物持续时间更长优先、更新时间更新优先排序。

管理员视图不包含确认占座、标记误判、暂不处理等操作按钮，也不生成 `processing_status`、`action_result`、`operator`、`admin_note` 等假字段。

### 4.5 Polygon 座位布局

Polygon 座位布局由 `src/dashboard/seat_layout.py` 生成。该模块会校验 polygon 至少包含三个有效坐标点，对外部文本进行 HTML 转义，使用 SVG `viewBox` 自动适配坐标范围，并同时用颜色和文字表达座位状态。页面不展示原始摄像头图像，也不展示 polygon 原始坐标。

### 4.6 测试与验收

当前项目已有 50 个 unittest 测试，覆盖数据字段兼容、拥挤等级边界、无效容量、文件不存在、JSON 损坏、polygon 合并、不同 `camera_id` 分组、未知状态、学生端区域概览、管理员异常统计和排序等逻辑。

前端验收报告位于 `docs/frontend_acceptance_report.md`，中期证据包位于 `docs/midterm_evidence_package.md`。

## 5. Evidence 与评估结果

当前 evidence 包括：

- PRD：`docs/PRD.md`
- 技术说明：`docs/TECH.md`
- 前端验收报告：`docs/frontend_acceptance_report.md`
- Step 3A 管理员视图核验：`step3a-verification.md`
- 中期 evidence package：`docs/midterm_evidence_package.md`
- README：`README.md`
- 自动测试：`tests/`
- Git 安全检查：`docs/git_safety_checklist.md`

最终中期检查结果记录在 `docs/final_midterm_check.md`。当前测试、编译和 Streamlit 健康检查均通过。

截图和录屏仍需人工补充。截图应覆盖学生端核心指标、区域概览、Polygon 座位布局、人流趋势，以及管理员端管理概览、异常列表、高亮定位和异常详情。录屏应展示从学生视图到管理员视图的完整 Dashboard 操作流程，并说明当前系统不展示原始图像、不识别个人身份、不提供管理员处理按钮。

## 6. 挑战、风险与限制

当前最大限制是数据仍为 mock / 示例数据，不能代表真实图书馆环境。学校真实摄像头和闸机数据涉及隐私、数据权限和安全边界，需要在合规前提下获取或使用脱敏数据。

图像识别方面，YOLOv8 在真实图书馆环境中的效果还需要进一步验证，特别是遮挡、视角变化、物品类别相似、光照变化等情况。座位映射方面，不同摄像头坐标系必须严格隔离，不能将不同 `camera_id` 的 polygon 混合绘制。

系统功能方面，当前没有接入真实 API，没有管理员处理闭环，也没有真实 `forecast_30m` 预测模型。当前 Dashboard 在预测缺失时只显示“预测数据暂不可用”，不会伪造预测线或预测数字。

## 7. Final Delivery 计划

下一阶段建议首先补充人工截图和录屏，形成可用于汇报的 evidence。随后需要与图像算法同学确认真实检测 JSON 字段，与数据建设同学确认数据仓库字段和闸机数据格式。如果可以获得合规数据，则逐步替换 mock 数据，校准 YOLO 检测效果，并验证状态机在真实数据上的稳定性。

如果最终展示确实需要管理员处理闭环，应先设计后端字段和持久化逻辑，再实现操作按钮，避免仅在前端 session 中伪造处理状态。

## 8. 团队分工与贡献说明

当前团队成员包括周煜航、李明泽、朱昱洁。最终报告中的具体贡献需要团队人工确认，不能直接用模板替代真实贡献记录。贡献表模板已整理在 `docs/contribution_table_template.md`。

已知分工方向包括：前端设计与座位状态规则识别、图像识别算法、数据仓库建设。中期报告中应将每位成员的已完成任务与具体文件、文档、截图或测试证据对应起来。

## 9. AI / Tool-use Disclosure

本项目使用 ChatGPT / Codex 辅助项目讨论、PRD 整理、数据申请文档整理、前端重构建议、代码生成、测试生成和中期文档整理。AI 输出经过人工审查、单元测试、编译检查、Streamlit 健康检查、禁止项搜索和功能边界审查。

团队对最终提交内容的正确性、安全性和原创性负责，不把 AI 输出直接当作未经验证的事实。完整 disclosure 草稿见 `docs/ai_tool_use_disclosure.md`。
