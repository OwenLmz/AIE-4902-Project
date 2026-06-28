# Evidence Index

日期：2026-06-26

本索引用于连接中期报告章节、代码文件、测试结果、截图和录屏证据。

## 1. 已有文档证据

| 证据 | 路径 | 对应报告章节 | 说明 |
| --- | --- | --- | --- |
| PRD | `docs/PRD.md` | 1, 2, 4 | 项目目标、范围、验收标准 |
| 技术说明 | `docs/TECH.md` | 3, 4, 5 | 技术路线、运行方式 |
| 数据申请 / 对接说明 | `相关文档/智慧校园_数据请求文档.md`, `模块对接说明.md` | 1, 6, 7 | 数据需求与对接背景，提交前需人工确认 |
| UI 审计 | `ui-audit.md` | 4, 5 | 前端问题识别和改进依据 |
| UI 重构计划 | `ui-refactor-plan.md` | 4, 7 | 前端重构范围和分步实施计划 |
| 管理员视图核验 | `step3a-verification.md` | 4, 5 | Step 3A 管理员视图逐项验证 |
| 前端验收报告 | `docs/frontend_acceptance_report.md` | 5, 6 | 当前前端验收结果 |
| 中期 evidence package | `docs/midterm_evidence_package.md` | 5, 7 | 模块证据、截图和录屏建议 |
| Git 安全检查 | `docs/git_safety_checklist.md` | 5, 6 | 提交前敏感文件检查 |
| README | `README.md` | 3, 4, 5 | 项目说明、运行方式、隐私边界 |
| AI 使用声明 | `docs/ai_tool_use_disclosure.md` | 9 | AI / tool-use disclosure |

## 2. 已有代码证据

| 证据 | 路径 | 对应报告章节 | 说明 |
| --- | --- | --- | --- |
| Dashboard 入口 | `src/dashboard/app.py` | 3, 4 | 页面标题、tabs、自动刷新、数据加载 |
| 数据统一层 | `src/dashboard/data_provider.py` | 3, 4, 5 | 字段兼容、校验、错误和警告 |
| 状态文案与颜色 | `src/dashboard/styles.py` | 3, 4 | 状态中文名、拥挤等级 |
| 页面组件 | `src/dashboard/components.py` | 3, 4, 5 | 学生视图、管理员视图、概览和趋势 |
| Polygon 座位图 | `src/dashboard/seat_layout.py` | 3, 4, 5 | SVG 座位图、camera_id 分组、高亮 |
| 检测层 | `src/detection/yolo_detector.py` | 3, 4 | YOLO / mock 检测 |
| 座位映射 | `src/seat_mapping/mapper.py` | 3, 4 | 检测框到 seat_id 映射 |
| 状态机 | `src/state_machine/rules.py` | 3, 4 | 座位状态规则 |
| 人流统计 | `src/utils/crowding.py` | 3, 4 | crowd baseline |
| 测试目录 | `tests/` | 5 | 自动测试证据 |

## 3. 已有测试证据

| 检查项 | 命令 | 当前结果 | 对应报告章节 |
| --- | --- | --- | --- |
| unittest | `python3 -m unittest discover` | 通过，50 tests | 5 |
| py_compile | `python3 -m py_compile src/dashboard/app.py src/dashboard/data_provider.py src/dashboard/components.py src/dashboard/styles.py src/dashboard/seat_layout.py` | 通过 | 5 |
| Streamlit 健康检查 | `curl -I http://localhost:8501` | `HTTP/1.1 200 OK` | 5 |

最终记录见 `docs/final_midterm_check.md`。

## 4. 待人工补充截图

截图保存目录：

`docs/evidence/screenshots/`

| 文件名 | 内容 | 对应报告章节 |
| --- | --- | --- |
| `student_summary.png` | 学生端数据来源与核心指标 | 5 |
| `student_area_overview.png` | 楼层与区域概览 | 5 |
| `student_seat_layout.png` | Polygon 座位布局 | 5 |
| `student_crowd_trend.png` | 人流趋势图 | 5 |
| `admin_summary.png` | 管理概览 | 5 |
| `admin_anomaly_table.png` | 异常座位列表 | 5 |
| `admin_seat_highlight.png` | 异常座位高亮定位 | 5 |
| `admin_anomaly_detail.png` | 异常座位详情 | 5 |

可选补充：

- `student_seat_detail.png`：学生端座位详情。

## 5. 待人工补充录屏

| 文件名 | 内容 | 对应报告章节 |
| --- | --- | --- |
| `dashboard_walkthrough.mp4` | 学生视图到管理员视图的完整 Dashboard 操作流程 | 5 |

录屏脚本见 `docs/evidence/manual_capture_checklist.md`。

## 6. 证据使用提醒

- 不要把 mock 数据描述为真实生产数据。
- 不要声称已接入学校真实系统。
- 不要提交或展示原始摄像头图像、真实闸机记录、个人身份信息、密钥或模型权重。
- 贡献表需要团队人工确认后再放入最终报告。
