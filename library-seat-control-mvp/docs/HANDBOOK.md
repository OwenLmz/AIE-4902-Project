# 图书馆智能位控系统操作手册

本手册用于记录本地启动网站、检查服务、运行测试和准备演示的常用命令。当前项目是课程 MVP 原型，前端基于 Python / Streamlit，不迁移到 Java、SpringBoot 或 Vue。

## 1. 进入项目目录

```bash
cd "/Users/zzzzk/Desktop/AIE 智慧校园"
```

后续命令默认都在项目根目录下执行。

## 2. 安装依赖

如果是第一次运行，先安装 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

当前主要依赖包括：

- Streamlit
- pandas
- OpenCV
- Ultralytics YOLOv8

## 3. 准备 Dashboard 数据

Dashboard 默认读取：

- `output/seat_status.json`
- `output/crowd_status.json`

如果这两个文件已经存在，可以直接启动网站。

如需重新生成 mock 数据，可以运行：

```bash
python3 -m src.main --mock
```

注意：

- 该命令会修改 `output/*.json`。
- 状态机会根据规则累积无人有物持续时间。
- 测试不要依赖 `output/`，应使用 `tests/fixtures/` 或临时目录。
- 不要把真实监控图片、视频、真实闸机记录或个人数据放入 Git。

## 4. 启动网站

推荐使用以下命令启动 Streamlit：

```bash
python3 -m streamlit run src/dashboard/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

启动成功后，浏览器打开：

```text
http://localhost:8501
```

如果只是日常本地运行，也可以使用简写：

```bash
streamlit run src/dashboard/app.py
```

## 5. 检查网站是否可访问

```bash
curl -I http://localhost:8501
```

看到类似下面的结果，说明服务可访问：

```text
HTTP/1.1 200 OK
```

## 6. 重启网站

如果修改了前端样式但浏览器没有变化，通常需要重启 Streamlit。

先查找进程：

```bash
pgrep -fl "streamlit run src/dashboard/app.py|python3 -m streamlit"
```

停止对应进程：

```bash
kill <PID>
```

然后重新启动：

```bash
python3 -m streamlit run src/dashboard/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

如果不确定是否刷新了最新样式，可以浏览器强制刷新页面。

## 7. 前端页面结构

当前前端不是长下滑流式页面，而是：

- 右上角：学生模式 / 管理员模式切换
- 左侧：功能导航区
- 右侧：当前功能内容区

学生模式功能：

- 总览
- 区域推荐
- 座位地图
- 人流趋势

管理员模式功能：

- 管理概览
- 异常座位
- 异常定位

## 8. 每次修改后的必跑检查

运行单元测试：

```bash
python3 -m unittest discover
```

运行 Python 编译检查：

```bash
python3 -m py_compile src/dashboard/app.py src/dashboard/data_provider.py src/dashboard/components.py src/dashboard/styles.py src/dashboard/seat_layout.py
```

检查网站健康状态：

```bash
curl -I http://localhost:8501
```

检查是否误用了 Streamlit tabs：

```bash
grep -R "st.tabs" src/dashboard || true
```

检查是否误加管理员处理状态：

```bash
grep -R "processing_status\|action_result\|operator\|admin_note" src/dashboard tests || true
```

检查是否误加随机数据：

```bash
grep -R "random\|randint\|uniform" src/dashboard tests || true
```

## 9. 演示前检查清单

演示或截图前，确认：

- 页面顶部显示“模拟数据 · 原型验证中”。
- 右上角模式切换可用。
- 左侧功能导航可切换。
- 学生模式不展示 `has_person`、`has_object`、`unattended_minutes`。
- 管理员模式不出现处理按钮或假处理状态。
- 座位地图不展示原始摄像头图像。
- 座位地图不展示 polygon 原始坐标。
- 没有真实个人信息、学号、姓名、校园卡号。
- `forecast_30m` 缺失时显示“预测数据暂不可用”，不要伪造预测。

## 10. 常见问题

### 页面打不开

先检查 Streamlit 是否运行：

```bash
curl -I http://localhost:8501
```

如果不是 `200 OK`，重新启动网站。

### 修改了样式但页面没变化

先重启 Streamlit，再刷新浏览器：

```bash
pgrep -fl "streamlit run src/dashboard/app.py|python3 -m streamlit"
kill <PID>
python3 -m streamlit run src/dashboard/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

### 座位地图没有显示

检查：

- `output/seat_status.json` 是否存在；
- seat 数据是否包含 `seat_id`；
- seat 数据是否包含合法 `polygon`；
- 同一张图是否只使用同一个 `floor + zone + camera_id`；
- `src/data/seats.json` 是否能补齐缺失 polygon。

### 人流数据没有显示

检查：

- `output/crowd_status.json` 是否存在；
- `capacity` 是否大于 0；
- `current_people` 是否有效；
- `history` 是否为空。

### 测试失败

先不要继续改 UI。优先看失败用例名称，然后检查是否违反了：

- 不修改 `data_provider.py` 数据结构；
- 不修改 `output/` 和 `src/data/`；
- 不新增随机数据；
- 不伪造预测；
- 不新增管理员处理状态。

## 11. 不要做的事

- 不要为了展示效果手动改 `output/` 或 `src/data/`。
- 不要新增随机人数、随机座位状态或随机预测。
- 不要新增管理员处理状态字段。
- 不要展示原始摄像头图像或个人身份信息。
- 不要迁移到 Java、SpringBoot、Vue 或 React。
- 不要把真实视频、监控抽帧、闸机记录、密钥、模型权重提交到仓库。
