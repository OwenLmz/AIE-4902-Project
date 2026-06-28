# 中期提交 Evidence Package

日期：2026-06-26

本文档用于 Midterm Report 引用，整理当前 MVP 已完成内容、证据文件、建议截图和录屏脚本。

## 1. 当前已完成模块清单

| 模块 | 状态 | 主要代码文件 |
| --- | --- | --- |
| YOLO / mock 检测层 | 已完成 MVP | `src/detection/yolo_detector.py` |
| 座位映射层 | 已完成 MVP | `src/seat_mapping/mapper.py` |
| 座位状态机 | 已完成 MVP | `src/state_machine/rules.py` |
| 人流统计 baseline | 已完成 MVP | `src/utils/crowding.py` |
| 端到端 mock 主流程 | 已完成 MVP | `src/main.py` |
| Dashboard 数据统一层 | 已完成 | `src/dashboard/data_provider.py` |
| Dashboard 样式与状态文案 | 已完成 | `src/dashboard/styles.py` |
| Polygon 座位布局 | 已完成 | `src/dashboard/seat_layout.py` |
| 学生视图 | 已完成 MVP | `src/dashboard/components.py` |
| 管理员查看与定位视图 | 已完成基础版 | `src/dashboard/components.py` |
| 自动测试 | 已完成 | `tests/` |

## 2. 每个模块功能说明

### 2.1 检测层

- 支持 mock 检测输出；
- 支持通过 Ultralytics YOLOv8 对图片进行目标检测；
- 输出 `person` 与物品类检测 JSON。

证据类型：

- 代码文件；
- mock 输出 JSON；
- 运行日志；
- 检测 JSON 截图。

### 2.2 座位映射层

- 使用 `seat_id + polygon` 定义座位 ROI；
- 将检测框映射到具体座位；
- 输出每个座位的人和物品检测结果。

证据类型：

- `src/data/seats.json` 中的 polygon 定义；
- 映射输出 JSON；
- 单元测试。

### 2.3 座位状态机

- 根据人和物品检测结果输出座位状态；
- 支持 `FREE`、`OCCUPIED`、`POSSIBLY_OCCUPIED`、`SUSPICIOUS`；
- 支持无人有物持续时间累积；
- 有物无人达到阈值后进入疑似占座。

证据类型：

- 状态机代码；
- `output/seat_status.json` 示例；
- 测试用例；
- Dashboard 状态展示截图。

### 2.4 人流统计 baseline

- 使用模拟闸机数据计算馆内人数；
- 输出容量、当前人数、拥挤等级和历史人流。

证据类型：

- `src/data/gate_flow.csv`；
- `output/crowd_status.json`；
- 人流趋势图截图。

### 2.5 Dashboard 数据统一层

- 统一读取座位、人流、布局 JSON；
- 兼容旧字段：
  - `object_unattended_minutes`
  - `suspect_duration`
  - `latest.total_in_library`
  - `current_num`
- 合并 `camera_id` 与 polygon；
- 返回 `errors` 和 `warnings`；
- 不在 UI 层伪造默认值。

证据类型：

- `src/dashboard/data_provider.py`；
- `tests/test_dashboard_data_provider.py`；
- 空数据与异常数据测试。

### 2.6 学生视图

- 显示数据来源与更新时间；
- 显示核心指标；
- 显示楼层与区域概览；
- 支持楼层 / 区域筛选；
- 显示按摄像头分组的 Polygon 座位布局；
- 显示人流趋势；
- 不展示管理员检测细节或个人身份信息。

证据类型：

- Dashboard 截图；
- `src/dashboard/components.py`；
- `tests/test_dashboard_components.py`。

### 2.7 管理员查看与定位视图

- 显示管理员页面状态区；
- 显示暂不可用、疑似占座、实际座位使用率、异常最多区域；
- 显示异常座位列表；
- 支持选择异常座位；
- 按 `floor + zone + camera_id` 显示定位图；
- 高亮选中异常座位；
- 显示异常座位详情；
- 不提供处理按钮或假处理状态。

证据类型：

- Dashboard 截图；
- `step3a-verification.md`；
- `tests/test_dashboard_components.py`。

## 3. 建议截图清单

当前环境未保存自动截图。请在本地浏览器打开 Streamlit 后人工截图，并保存到：

`docs/evidence/screenshots/`

学生端建议截图：

- `student_summary.png`：数据来源与核心指标；
- `student_area_overview.png`：楼层与区域概览；
- `student_seat_layout.png`：Polygon 座位布局图；
- `student_seat_detail.png`：座位详情；
- `student_crowd_trend.png`：人流趋势图。

管理员端建议截图：

- `admin_summary.png`：管理概览；
- `admin_anomaly_table.png`：异常座位列表；
- `admin_seat_highlight.png`：异常座位高亮定位；
- `admin_anomaly_detail.png`：异常座位详情。

## 4. 建议录屏脚本

1. 打开 Streamlit Dashboard。
2. 展示学生视图的数据来源与核心指标。
3. 切换楼层 / 区域筛选。
4. 选择座位并查看座位详情。
5. 查看人流趋势图。
6. 切换到管理员视图。
7. 查看异常概览。
8. 选择一个异常座位。
9. 展示 Polygon 高亮定位。
10. 展示异常座位详情。
11. 说明当前系统不展示原始图像、不识别个人身份、不提供管理员假处理按钮。

## 5. 测试结果摘要

运行命令：

```bash
python3 -m unittest discover
```

结果：

```text
Ran 50 tests in 0.005s
OK
```

覆盖范围包括：

- 字段兼容；
- crowd level 边界；
- 无效容量；
- 文件不存在与 JSON 损坏；
- polygon 合并与 camera_id 分组；
- 未知状态；
- 学生端区域概览；
- 人流趋势；
- 管理员概览；
- 异常座位排序；
- 选中异常座位高亮；
- 禁止生成假处理字段。

## 6. 与 PRD / 技术路线对应关系

| PRD / 技术路线要求 | 当前实现 |
| --- | --- |
| 图像 -> 检测结果 | `src/detection/yolo_detector.py` |
| 检测结果 -> 座位映射 | `src/seat_mapping/mapper.py` |
| 座位映射 -> 状态机 | `src/state_machine/rules.py` |
| 有物无人 20 分钟 -> 疑似占座 | `src/state_machine/rules.py` |
| 人流拥挤等级 | `src/utils/crowding.py` 与 `src/dashboard/data_provider.py` |
| Dashboard 展示座位状态 | `src/dashboard/app.py` 与 `src/dashboard/components.py` |
| 自动刷新 | `src/dashboard/app.py` |
| 简单可运行 MVP | 本地 JSON / CSV + Streamlit |

## 7. 当前 limitations

- 当前主要使用 mock 数据，不代表真实摄像头和真实闸机数据。
- 未接入真实 API 和数据库。
- 未实现管理员处理闭环。
- 未实现权限系统。
- 未训练自定义模型。
- 未做生产级部署、安全审计或高并发优化。
- 未生成自动浏览器截图，本次证据包提供人工截图清单。

## 8. Final delivery 前剩余任务

- 补充最终演示截图与录屏。
- 与图像算法同学确认真实检测 JSON 字段格式。
- 与数据建设同学确认数据仓库字段映射。
- 决定是否需要管理员处理闭环；若需要，先定义后端字段和持久化逻辑。
- 进行一次端到端演示彩排。
- 清理不应提交的临时文件、缓存文件和敏感文件。
