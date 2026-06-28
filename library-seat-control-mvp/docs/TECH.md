# 智慧校园图书馆智能位控系统 MVP 技术说明

## 安装

```bash
pip install -r requirements.txt
```

如果暂时没有安装 YOLO 或没有真实图片，可以直接用 mock 数据跑通。

## Step 1：目标检测

Mock 运行：

```bash
python3 -m src.detection.yolo_detector --mock --output output/detections.json
```

真实 YOLOv8 运行：

```bash
python3 -m src.detection.yolo_detector --image path/to/library.jpg --model yolov8n.pt --output output/detections.json
```

输出示例：

```json
{
  "source": "mock",
  "detections": [
    {"label": "laptop", "category": "object", "bbox": [78, 118, 154, 166]},
    {"label": "person", "category": "person", "bbox": [268, 68, 392, 232]}
  ]
}
```

## Step 2：座位映射

```bash
python3 -m src.seat_mapping.mapper \
  --seats src/data/seats.json \
  --detections output/detections.json \
  --output output/mapped_seats.json
```

规则：检测框中心点落入座位 polygon，或检测框与座位 ROI 有足够重叠，即认为该检测属于该座位。

## Step 3：状态机

```bash
python3 -m src.state_machine.rules \
  --mapped output/mapped_seats.json \
  --previous output/seat_status.json \
  --interval-minutes 5 \
  --output output/seat_status.json
```

状态规则：

- 有人：`OCCUPIED`，无人有物累计清零。
- 无人有物且累计小于 20 分钟：`POSSIBLY_OCCUPIED`。
- 无人有物且累计大于等于 20 分钟：`SUSPICIOUS`。
- 无人无物：`FREE`。

## Step 4：Dashboard

```bash
streamlit run src/dashboard/app.py
```

Dashboard 读取：

- `output/seat_status.json`
- `output/crowd_status.json`

页面默认 5 秒刷新。

## Step 5：人流统计

```bash
python3 -m src.utils.crowding \
  --gate-flow src/data/gate_flow.csv \
  --capacity 220 \
  --output output/crowd_status.json
```

拥挤等级：

- 使用率 < 40%：`low`
- 使用率 < 75%：`medium`
- 其余：`high`

## 一键跑完整链路

```bash
python3 -m src.main --mock
```

为了演示 20 分钟规则，可以运行：

```bash
python3 -m src.main --mock --interval-minutes 20
```

## 与现有对接文档的字段差异

当前 MVP 使用需求里的大写状态值。若要对接现有 Redis/MySQL 文档，可做如下映射：

- `FREE` -> `free`
- `OCCUPIED` -> `occupied`
- `POSSIBLY_OCCUPIED` -> `occupied`
- `SUSPICIOUS` -> `suspected`

