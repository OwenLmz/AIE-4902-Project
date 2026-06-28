# 智慧校园图书馆智能位控系统 MVP PRD

## 目标

做一个可运行的端到端 MVP，验证核心链路：

图像 -> YOLO 检测结果 -> 座位 ROI 映射 -> 状态机 -> Dashboard。

## MVP 范围

- 输入一张图，输出 person / backpack / laptop / book / bottle / cup 检测 JSON。
- 用 `seat_id + polygon` 把检测框映射到座位。
- 输出四类座位状态：`FREE`、`OCCUPIED`、`POSSIBLY_OCCUPIED`、`SUSPICIOUS`。
- 有物无人累计达到 20 分钟后标记 `SUSPICIOUS`。
- 用模拟闸机 CSV 计算拥挤等级：`low`、`medium`、`high`。
- Streamlit Dashboard 每 5 秒刷新。

## 非目标

- 不训练模型。
- 不接入数据库、Redis、权限系统、微服务。
- 不做生产级部署和高并发设计。

## 验收标准

- 能运行 `python3 -m src.main --mock`。
- 能生成 `output/detections.json`、`output/mapped_seats.json`、`output/seat_status.json`、`output/crowd_status.json`。
- 能运行 `streamlit run src/dashboard/app.py` 查看座位状态和拥挤程度。

