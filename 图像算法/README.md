# Smart Campus 图像算法模块

这是期中演示版图像算法模块。它负责把本地图片中的 YOLO 检测结果转换成座位状态，并写入 Redis 与 MySQL，供后端和前端读取。

## 交付内容

- CPU 运行 YOLOv8n。
- 从 MySQL `seat_config` 读取座位 ROI。
- 对 `images/` 下图片识别 `person` 和常见占座物品。
- 生成 `has_person`, `has_object`, `status`, `suspect_duration`。
- 写入 Redis `seat:{seat_id}`，TTL 为 120 秒。
- 批量插入 MySQL `seat_status_log`。
- 同步生成 `outputs/latest_seat_status.csv`，方便演示检查。

## 1. 环境安装

在 PowerShell 中进入本目录：

```powershell
cd D:\AIE4902\图像算法
.\setup.ps1
```

`setup.ps1` 会创建 `D:\AIE4902\.image_algo_venv`、安装依赖，并下载 `models/yolov8n.pt`。如果网络下载失败，可以手动下载 `yolov8n.pt` 后放到 `models/` 目录。

注意：脚本会把虚拟环境放在 `D:\AIE4902\.image_algo_venv`，而不是中文目录内部。这是为了避开部分 Windows Python venv 在中文路径下无法启动的问题；代码、配置、模型和输出仍然都在 `图像算法` 文件夹中。

## 2. 配置数据库

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

打开 `.env`，把 `MYSQL_PASSWORD` 改成你本地 MySQL 密码。数据库需要先执行数据结构同学的：

```text
D:\AIE4902\数据结构\library_schema_fixed.sql
```

Redis 需要本地启动，默认连接：

```text
localhost:6379
```

## 3. 放入测试图片

把图书馆座位测试图片放到：

```text
D:\AIE4902\图像算法\images
```

如果只有一个摄像头 `CAM-3A`，图片可以任意命名，例如 `test01.jpg`。如果以后有多个摄像头，建议图片名包含摄像头编号，例如 `CAM-3A_001.jpg`。

## 4. 运行

正常运行，直写 Redis 和 MySQL：

```powershell
..\.image_algo_venv\Scripts\python.exe main.py
```

只本地测试，不写 Redis/MySQL：

```powershell
..\.image_algo_venv\Scripts\python.exe main.py --dry-run --skip-mysql --skip-redis
```

只处理单张图片：

```powershell
..\.image_algo_venv\Scripts\python.exe main.py --image images\test01.jpg
```

公开图片样例测试，不写 Redis/MySQL：

```powershell
..\.image_algo_venv\Scripts\python.exe scripts\download_web_samples.py
..\.image_algo_venv\Scripts\python.exe main.py --config web_samples_config.yaml --dry-run --skip-mysql --skip-redis
```

样例输出位置：

```text
outputs\web_samples\latest_seat_status.csv
outputs\web_samples\latest_detections.json
outputs\web_samples\annotated
```

## 5. 输出字段

CSV 输出位置：

```text
outputs/latest_seat_status.csv
```

字段与 `seat_status_log` 对齐：

| 字段 | 说明 |
|---|---|
| `seat_id` | 座位编号 |
| `floor` | 楼层 |
| `zone` | 区域 |
| `detected_at` | 检测时间 |
| `has_person` | 是否有人，0/1 |
| `has_object` | 是否有物，0/1 |
| `status` | `free`, `occupied`, `suspected`, `unavailable` |
| `suspect_duration` | 疑似占座累计分钟 |

Redis 字段：

```json
{
  "status": "suspected",
  "has_person": "0",
  "has_object": "1",
  "suspect_min": "30",
  "floor": "3",
  "zone": "A",
  "updated_at": "2025-04-01 09:00:00"
}
```

## 6. 状态判断规则

- 有人：`occupied`，`suspect_duration = 0`。
- 无人有物：读取 Redis 上一次 `suspect_min`，加 30 分钟；累计达到 20 分钟后为 `suspected`。
- 无人无物：`free`，`suspect_duration = 0`。
- 座位未启用：`unavailable`。

## 7. 常见问题

- 缺少依赖：重新运行 `.\setup.ps1`。
- 缺少模型：运行 `..\.image_algo_venv\Scripts\python.exe main.py --download-model-only`。
- MySQL 连接失败：检查 `.env` 密码、数据库名和是否已执行建表 SQL。程序会退回到 `config.yaml` 里的 4 个演示座位，并继续生成本地 CSV。
- Redis 连接失败：程序会提示 warning，并继续生成本地 CSV；但疑似时长无法从 Redis 历史值累加。
- 图片目录为空：把 jpg/png 图片放进 `images/` 后重新运行。
- 公开图片样例仅用于 sanity check，不能替代学校真实图书馆数据的正式准确率评估。

## 8. GitHub 提交说明

建议提交代码、配置、说明文档和 `.gitkeep` 空目录占位文件；不要提交 `.env`、虚拟环境、模型权重、学校真实图片、第三方网页图片或 `outputs/` 生成结果。

模型权重由 `setup.ps1` 自动下载到 `models/yolov8n.pt`。公开网页样例可通过 `scripts/download_web_samples.py` 重新下载。学校真实图片如需复现，请在组内单独共享，并放到：

```text
images\school_test\SCHOOL-01_suspected_bag_bottle.jpg
```
