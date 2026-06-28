# Midterm Report Outline

本大纲用于整理课程中期报告。报告应明确说明：当前项目是课程 MVP 原型，Dashboard 使用 mock / 示例数据，尚未接入学校真实系统。

## 1. Project Overview and Problem Statement

### 1.1 项目背景

- 图书馆自习座位资源紧张。
- 传统人工巡查难以及时发现长期占座、空座未释放等问题。
- 智慧校园场景下，可以结合图像识别、座位映射和规则状态机，建立可解释的座位状态管理原型。

### 1.2 用户和利益相关方

- 学生：希望快速查看空闲座位和区域拥挤程度。
- 图书馆管理员：希望定位异常座位，辅助现场巡查。
- 数据建设成员：负责后续数据字段、闸机数据、仓库结构适配。
- 图像算法成员：负责检测模型、识别字段和摄像头视角适配。
- 课程老师 / 导师：关注项目范围、技术路线、实现证据和伦理边界。

### 1.3 核心痛点

- 空座与占座状态不可见。
- 物品占座缺少可解释判断依据。
- 不同摄像头坐标系不能直接合并。
- 数据申请和隐私边界影响真实系统接入进度。

### 1.4 项目范围

- 当前阶段聚焦端到端 MVP。
- 核心链路：检测结果 -> 座位映射 -> 状态机 -> Dashboard。
- 不做生产级权限系统、真实 API、高并发服务或真实部署。

## 2. Requirements and Success Criteria

### 2.1 学生端需求

- 查看数据来源和更新时间。
- 查看当前馆内人数、容量、空闲座位数和拥挤等级。
- 查看楼层 / 区域概览。
- 按楼层、区域、摄像头视角查看座位布局。
- 不展示检测细节、原始图像和个人身份信息。

### 2.2 管理员端需求

- 查看异常座位统计。
- 查看 `POSSIBLY_OCCUPIED` 和 `SUSPICIOUS` 座位列表。
- 选择异常座位后定位到对应 `floor + zone + camera_id` 布局图。
- 查看检测依据，例如是否有人、是否有物、无人有物持续时间。
- 当前阶段不实现管理员操作按钮和处理闭环。

### 2.3 非功能需求

- 使用 Python / Streamlit / JSON / CSV 保持 MVP 简单可运行。
- 不依赖复杂后端和数据库。
- 不伪造真实数据、不伪造预测、不展示个人身份信息。
- 测试覆盖字段兼容、异常数据、polygon 分组和管理员异常排序。

### 2.4 成功指标

- 能运行 Dashboard。
- 能展示学生视图和管理员视图。
- 能从统一数据层读取座位、人流和布局数据。
- 能通过自动测试和编译检查。
- 能提供可追溯 evidence。

## 3. Technical Approach and Architecture

### 3.1 总体技术路线

- Python 作为核心开发语言。
- YOLOv8 / mock 检测作为 detection 层。
- Polygon ROI 作为 seat mapping 层。
- 规则状态机作为座位状态判断核心。
- CSV / JSON 作为 MVP 数据载体。
- Streamlit 作为前端 Dashboard。

### 3.2 数据流

```text
image/mock detection
  -> detections.json
  -> seat mapping
  -> mapped_seats.json
  -> state machine
  -> seat_status.json
  -> data_provider.py
  -> Streamlit Dashboard
```

人流链路：

```text
gate_flow.csv/mock crowd data
  -> crowd_status.json
  -> data_provider.py
  -> crowd metrics and trend chart
```

### 3.3 YOLO / CV 识别链路

- 目标类别包括人、书包、电脑、书本、水杯等。
- 当前 MVP 支持 mock 检测输出，也保留 YOLOv8 调用入口。
- 中期阶段不声称已经完成真实环境模型训练或上线部署。

### 3.4 Polygon seat mapping

- 每个座位使用唯一 `seat_id`。
- 每个座位具有 polygon / ROI。
- 坐标系按 `floor + zone + camera_id` 分组。
- 不同 `camera_id` 的 polygon 不混合绘制。

### 3.5 状态机

- `FREE`：无人无物。
- `OCCUPIED`：有人。
- `POSSIBLY_OCCUPIED`：有物无人但未达到阈值。
- `SUSPICIOUS`：有物无人持续时间达到规则阈值。
- `UNAVAILABLE`：不可用座位。

### 3.6 人流分析

- 当前使用模拟闸机 / crowd JSON。
- 输出当前人数、容量、拥挤等级、历史趋势。
- 没有真实 `forecast_30m` 时显示“预测数据暂不可用”。

### 3.7 Streamlit Dashboard

- `app.py` 负责页面组织。
- `data_provider.py` 负责数据读取、兼容和校验。
- `components.py` 负责学生视图和管理员视图。
- `seat_layout.py` 负责安全 SVG / polygon 座位图。
- `styles.py` 负责状态文案和颜色。

### 3.8 为什么当前 MVP 使用 Python

- 与 YOLOv8、OpenCV、数据处理生态兼容。
- Streamlit 能快速形成可演示 Dashboard。
- JSON / CSV 能降低数据依赖，便于课程中期展示。
- 避免过早引入 Java、微服务、权限系统和数据库复杂度。

## 4. Progress and Implemented Work

### 4.1 PRD

- 已形成 MVP 目标、范围、非目标和验收标准。
- 证据：`docs/PRD.md`。

### 4.2 数据申请

- 已有数据请求 / 对接类文档。
- 证据：`相关文档/智慧校园_数据请求文档.md`、`模块对接说明.md`。
- 提交前需确认是否允许纳入仓库或报告附件。

### 4.3 技术调查

- 已形成技术说明。
- 证据：`docs/TECH.md`。

### 4.4 数据适配层

- 已实现 `data_provider.py`。
- 支持字段兼容、错误与警告、polygon 合并、`camera_id` 补齐。

### 4.5 学生视图

- 已实现数据状态、核心指标、区域概览、座位布局和人流趋势。

### 4.6 管理员视图

- 已实现基础查看与定位能力。
- 不实现管理员操作按钮和假处理状态。

### 4.7 Polygon 座位图

- 已按 `floor + zone + camera_id` 分组。
- 已使用 SVG `viewBox` 自适应坐标范围。
- 已对外部文本做转义，不展示原始摄像头图像。

### 4.8 测试

- 已有 50 个 unittest 用例。
- 覆盖数据兼容、crowd 边界、polygon、安全 SVG、学生视图聚合、管理员异常逻辑。

### 4.9 README 和验收文档

- 已更新 README。
- 已生成前端验收报告、evidence package 和 Git 安全检查清单。

## 5. Evidence and Evaluation

### 5.1 截图证据

- 待人工补充学生端和管理员端截图。
- 清单见 `docs/evidence/manual_capture_checklist.md`。

### 5.2 测试结果

- `python3 -m unittest discover`
- 当前结果记录在 `docs/final_midterm_check.md`。

### 5.3 前端验收报告

- 证据：`docs/frontend_acceptance_report.md`。

### 5.4 OpenCV baseline / 技术调查结论

- 当前技术路线保留 OpenCV / YOLOv8。
- 中期报告中应谨慎表述为“技术路线和 MVP 接口已准备”，不声称完成真实模型训练。

### 5.5 当前 MVP 效果

- 已能运行 Streamlit Dashboard。
- 已能展示座位状态、区域概览、polygon 布局、人流趋势和管理员异常定位。
- 当前效果基于 mock / 示例数据。

## 6. Challenges, Risks, and Limitations

- 数据申请不确定性。
- 摄像头图像涉及隐私和数据合规。
- mock 数据不能代表真实业务分布。
- 未接入真实 API 和数据库。
- 无管理员处理闭环。
- 无真实 `forecast_30m`。
- YOLO 模型在真实图书馆环境中的泛化能力仍需验证。
- 不同摄像头坐标系需要严格按 `camera_id` 隔离。

## 7. Plan to Final Delivery

- 获取合规数据或确认可用的脱敏示例数据。
- 用真实检测输出替换 mock 检测结果。
- 训练、校准或评估 YOLO 检测效果。
- 接入真实或更接近真实的闸机数据。
- 决定是否实现 `forecast_30m`，避免伪造预测。
- 决定是否做管理员处理闭环，若做则先定义后端字段。
- 准备最终 Demo 截图、录屏和讲稿。

## 8. Team Roles and Individual Contributions

报告中可使用以下结构，但最终内容必须由团队人工确认：

- 周煜航：待确认具体角色与交付物。
- 李明泽：待确认具体角色与交付物。
- 朱昱洁：待确认具体角色与交付物。
- 课程老师 / 导师支持：需求边界、数据合规和技术路线指导。

贡献表模板见 `docs/contribution_table_template.md`。

## 9. AI / Tool-use Disclosure

- 使用 ChatGPT / Codex 辅助项目讨论、文档整理、代码生成、测试生成和前端重构建议。
- AI 输出经过人工审查、单元测试、编译检查、健康检查和禁止项搜索。
- 团队不把 AI 输出直接当作未经验证的事实。
- disclosure 草稿见 `docs/ai_tool_use_disclosure.md`。
