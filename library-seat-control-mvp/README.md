# 智慧校园图书馆智能位控系统 MVP

这是一个面向课程 / 中期验收的图书馆智能座位管理 MVP。项目重点不是训练模型，而是跑通完整数据链路：

图像或 mock 检测结果 -> 座位映射 -> 座位状态机 -> 人流统计 -> Streamlit Dashboard。

## 当前 MVP 功能

- YOLOv8 / mock 目标检测：识别 `person` 与书包、电脑、书本、水杯等物品。
- 座位映射：用 `seat_id + polygon` 将检测结果映射到具体座位。
- 座位状态机：
  - `FREE`：空闲；
  - `OCCUPIED`：使用中；
  - `POSSIBLY_OCCUPIED`：有物无人，暂不可用；
  - `SUSPICIOUS`：疑似占座；
  - `UNAVAILABLE`：不可用。
- 人流统计 baseline：基于模拟闸机数据输出馆内人数和拥挤等级。
- 学生视图：
  - 数据来源与更新时间；
  - 当前人数 / 容量、空闲座位、拥挤等级、未来趋势提示；
  - 楼层与区域概览；
  - Polygon 座位布局；
  - 人流趋势图。
- 管理员视图基础版：
  - 管理概览；
  - 异常座位列表；
  - 异常座位选择；
  - Polygon 高亮定位；
  - 异常座位详情。

当前管理员视图只做查看与定位，不实现确认占座、标记误判、暂不处理、操作日志或假处理状态。

## 技术栈

- Python
- Ultralytics YOLOv8
- OpenCV
- Streamlit
- pandas
- JSON / CSV
- unittest

## 项目结构

```text
src/
  detection/        # YOLO / mock 检测逻辑
  seat_mapping/     # seat_id + polygon 映射
  state_machine/    # 座位状态机
  data/             # 示例座位与模拟闸机数据
  api/              # 预留 API 目录
  dashboard/        # Streamlit Dashboard
  utils/            # IO 与人流统计工具

docs/
  PRD.md
  TECH.md
  frontend_acceptance_report.md
  midterm_evidence_package.md
  git_safety_checklist.md

tests/
  fixtures/         # 独立测试夹具
  test_*.py

output/             # 本地运行输出，不建议提交 Git
```

## 数据来源说明

当前项目使用 mock / 示例数据：

- `src/data/seats.json`：示例座位布局与 polygon；
- `src/data/gate_flow.csv`：模拟闸机数据；
- `output/seat_status.json`：运行生成或已有的座位状态；
- `output/crowd_status.json`：运行生成或已有的人流状态。

Dashboard 通过 `src/dashboard/data_provider.py` 统一读取和清洗数据，UI 层不伪造默认人数、容量或预测数据。

## 如何准备 mock 数据

如果已有 `output/seat_status.json` 和 `output/crowd_status.json`，可以直接启动 Dashboard。

如需重新生成 mock 输出，可运行端到端 mock 流程：

```bash
python3 -m src.main --mock
```

注意：该命令会更新 `output/*.json`，并可能根据状态机逻辑累积无人有物持续时间。测试不会依赖这些运行输出，而是使用 `tests/fixtures/` 中的独立测试数据。

## 如何运行测试

```bash
python3 -m unittest discover
```

当前验收结果：

```text
Ran 50 tests in 0.001s
OK
```

## 如何启动 Streamlit Dashboard

```bash
streamlit run src/dashboard/app.py
```

打开本地页面后，可以查看：

- 学生视图；
- 管理员视图；
- 5 秒自动刷新开关。

服务可用性也可以用以下命令检查：

```bash
curl -I http://localhost:8501
```

## 页面功能说明

### 学生视图

- 显示“模拟数据，仅用于原型验证”；
- 显示座位数据与人流数据更新时间；
- 显示当前馆内人数 / 总容量、空闲座位数、拥挤等级、未来 30 分钟趋势；
- 按楼层与区域展示区域概览；
- 按 `floor + zone + camera_id` 显示座位布局图；
- 不混合不同摄像头坐标系；
- 不展示检测细节、polygon 原始坐标、模型置信度或个人身份信息。

### 管理员视图

- 显示管理概览；
- 显示暂不可用与疑似占座数量；
- 显示实际座位使用率；
- 显示异常最多区域；
- 显示异常座位列表；
- 支持选择异常座位并高亮定位；
- 显示异常座位详情和检测依据。

管理员视图当前不提供处理按钮，不生成 `processing_status`、`operator`、`action_time`、`action_result`、`admin_note` 等假字段。

## 隐私保护说明

当前 MVP 不展示：

- 原始摄像头图像；
- 真实监控截图；
- 姓名；
- 学号；
- 校园卡号；
- 个人身份信息；
- 模型置信度；
- 密钥或环境变量。

不应提交到 Git 的内容包括：

- 原始视频；
- 真实监控抽帧；
- 真实闸机记录；
- 个人数据；
- 模型权重；
- `.env`；
- `.streamlit/secrets.toml`；
- `output/` 运行结果；
- 保密协议文件，除非小组明确确认可以提交。

## 当前 limitations

- 当前主要使用 mock 数据，不代表真实图书馆生产数据。
- 未接入真实摄像头、真实闸机和真实 API。
- 未实现管理员操作闭环。
- 未实现权限系统。
- 未训练自定义模型。
- 未做生产级部署、高并发或安全审计。

## Midterm evidence

中期证据材料见：

- `docs/frontend_acceptance_report.md`
- `docs/midterm_evidence_package.md`
- `docs/git_safety_checklist.md`

建议最终提交前按 `docs/midterm_evidence_package.md` 中的截图清单补充人工截图和录屏。
