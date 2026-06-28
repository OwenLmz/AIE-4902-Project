# 图书馆智能位控系统前端重构计划

生成日期：2026-06-25  
依据文档：`ui-audit.md` 与本阶段已确认的产品/技术决策。  
执行边界：本文件只制定计划，不修改代码。

## 0. 已确认补充要求

- 统一 Seat 字段模型增加 `camera_id`。
- polygon 坐标按 `floor + zone + camera_id` 分组绘制；同一座位图不得混合多个摄像头坐标系。
- 若同一区域存在多个 `camera_id`，前端提供 `camera_id` 选择器，或按摄像头分别展示多个座位图。
- 本轮先创建并审核 `.gitignore`，不得直接执行 `git add .`。
- Step 1 增加轻量自动测试，使用 Python 标准库 `unittest`，不新增大型依赖。
- 测试使用 `tests/fixtures` 或临时目录，不依赖也不修改正在使用的 `output/*.json`。
- SVG/HTML 输出必须转义文本、校验 polygon，并使用 `viewBox` 自动缩放坐标。
- 数据适配层区分 `errors` 与 `warnings`。

## 1. 重构目标

将当前单页 Streamlit Dashboard 重构为一个清晰、可解释、可追溯数据来源的 MVP 前端：

- 继续使用 Streamlit，不改变启动方式：`streamlit run src/dashboard/app.py`。
- 使用 `st.tabs` 分为“学生视图”和“管理员视图”。
- 所有页面指标可追溯到 `output/seat_status.json`、`output/crowd_status.json`、`src/data/seats.json`。
- 明确显示“模拟数据，仅用于原型验证”。
- 不使用随机数据，不伪造预测数据，不默认展示误导性数字。
- 使用 `src/data/seats.json` 中的 polygon 绘制座位布局图。
- 使用 `floor + zone + camera_id` 作为座位布局分组边界。
- 本轮不接入真实 API，不新增数据库，不修改 AI 状态机。

本轮不需要新增第三方依赖。现有 Streamlit、pandas 和 Python 标准库足够完成 tabs、表格、折线图、HTML/SVG polygon 布局与 JSON 适配；不为了点击 polygon 引入大型依赖。

## 2. 页面信息架构

当前页面：

- `图书馆智能位控 Dashboard`

重构后页面仍由 `src/dashboard/app.py` 启动，但页面内分为：

1. 学生视图
2. 管理员视图

建议结构：

```text
图书馆智能位控系统
数据状态区：模拟数据，仅用于原型验证 / 座位更新时间 / 人流更新时间 / 自动刷新

[学生视图]
  核心指标
  楼层与区域概览
  座位布局图
  座位详情
  人流趋势

[管理员视图]
  管理概览
  异常座位列表
  异常座位定位图
  异常详情
```

## 3. 学生视图组件清单

| 区域 | 组件 | 数据字段 | 展示规则 | 空数据处理 |
|---|---|---|---|---|
| 页面状态区 | 页面标题 | 硬编码标题 | `图书馆座位状态` | 不适用 |
| 页面状态区 | 数据来源状态 | `data_source` | 固定显示“模拟数据，仅用于原型验证” | 不适用 |
| 页面状态区 | 座位数据更新时间 | `seat_updated_at` | 来自座位状态文件 | 缺失显示“暂无座位数据” |
| 页面状态区 | 人流数据更新时间 | `crowd_updated_at` | 来自人流状态文件 | 缺失显示“暂无人流数据” |
| 页面状态区 | 自动刷新开关 | UI 控件 | 保留 5 秒刷新 | 不适用 |
| 核心指标区 | 当前馆内人数 / 总容量 | `current_people`、`capacity` | 显示 `current_people / capacity 人` | 缺失显示“暂无人流数据”或“容量数据缺失” |
| 核心指标区 | 当前空闲座位数 | seat `status == FREE` | 单位为“座” | seat 列表为空显示“暂无座位数据” |
| 核心指标区 | 当前拥挤等级 | `crowd_level`、`crowd_ratio` | 中文显示：低 / 中等 / 拥挤 / 接近满载 | capacity 无效时显示“容量数据缺失” |
| 核心指标区 | 未来 30 分钟趋势 | `forecast_30m` | 当前不存在则显示“预测数据暂不可用” | 不生成假预测 |
| 楼层与区域概览 | 区域列表/卡片 | `floor`、`zone`、status 汇总 | 动态按现有 seat 数据分组 | 无 seat 显示“暂无座位数据” |
| 座位布局图 | Polygon 座位图 | `polygon`、`seat_id`、`status` | 中性空白画布绘制 polygon，不显示监控图像 | 无 polygon 显示“暂无座位布局数据” |
| 座位布局图 | 楼层/区域筛选 | `floor`、`zone` | 只使用现有数据生成选项 | 无数据禁用或显示空状态 |
| 座位详情 | 选中座位信息 | `seat_id`、`floor`、`zone`、`status`、`updated_at` | 不展示 has_person / has_object / unattended_minutes | 未选择显示“请选择座位” |
| 人流趋势 | 历史人数折线图 | `history[].recorded_at`、`history[].total_in_library` | 标题、横轴时间、纵轴人数、图例、时间范围 | history 为空显示“暂无人流数据” |

学生端状态中文名：

| 后端状态 | 学生端显示 |
|---|---|
| `FREE` | 空闲 |
| `OCCUPIED` | 使用中 |
| `POSSIBLY_OCCUPIED` | 暂不可用 |
| `SUSPICIOUS` | 疑似占座（待确认） |
| `UNAVAILABLE` | 不可用 |

学生视图不得展示：

- `has_person`
- `has_object`
- `object_unattended_minutes`
- `unattended_minutes`
- 模型置信度
- 原始图像
- 管理员处理信息

## 4. 管理员视图组件清单

| 区域 | 组件 | 数据字段 | 展示规则 | 空数据处理 |
|---|---|---|---|---|
| 管理概览 | 暂不可用数量 | `status == POSSIBLY_OCCUPIED` | 单位为“座” | 无 seat 显示“暂无数据” |
| 管理概览 | 疑似占座数量 | `status == SUSPICIOUS` | 单位为“座” | 无 seat 显示“暂无数据” |
| 管理概览 | 当前实际座位使用率 | `OCCUPIED / (total_seats - UNAVAILABLE)` | 百分比；POSSIBLY_OCCUPIED 和 SUSPICIOUS 不计入分子 | 分母无效显示“暂无数据” |
| 管理概览 | 异常最多区域 | 按 `floor + zone` 聚合异常数 | 显示楼层、区域、异常数 | 无异常显示“暂无异常区域” |
| 异常座位列表 | 可排序表格 | `seat_id`、`floor`、`zone`、`status`、`has_person`、`has_object`、`unattended_minutes`、`updated_at` | 只列 `POSSIBLY_OCCUPIED` 和 `SUSPICIOUS` | 无异常显示“暂无异常座位” |
| 异常座位列表 | 排序逻辑 | `status`、`unattended_minutes`、`updated_at` | SUSPICIOUS 优先，其次持续时间更长，其次更新时间更近 | 不适用 |
| 异常座位定位 | Polygon 布局图 | `polygon`、`seat_id`、`status` | 选中异常 seat_id 高亮 | 无 polygon 显示“暂无座位布局数据” |
| 异常详情 | 判断依据 | `has_person`、`has_object`、`unattended_minutes` | 管理员可见 | 缺字段显示“暂无数据” |

本轮不实现管理员操作按钮：

- 确认占座
- 标记误判
- 暂不处理
- 操作日志

原因：当前后端和数据文件没有 `processing_status`、`operator`、`action_time`、`action_result`、`admin_note` 等可持久化字段。不得使用仅存在于前端 session 的假处理状态伪装成真实结果。

## 5. 保留、修改、删除的现有组件

| 现有组件 | 当前位置 | 处理 | 说明 |
|---|---|---|---|
| 页面标题 `图书馆智能位控 Dashboard` | `app.py` | 修改 | 改为系统标题 + tabs 内视图标题 |
| `5 秒自动刷新` toggle | `app.py` sidebar | 保留并调整 | 移入页面状态区或保留 sidebar，但必须显示刷新含义 |
| `座位状态更新时间` caption | `app.py` | 修改 | 同时展示座位更新时间和人流更新时间 |
| 空闲 metric | `app.py` | 保留并修改 | 学生视图展示“当前空闲座位数” |
| 使用中 metric | `app.py` | 修改 | 管理员用于使用率计算；学生端可不单独展示使用中数量 |
| 有物无人 metric | `app.py` | 修改 | 学生端改为“暂不可用”语义；管理员端展示 POSSIBLY_OCCUPIED 数量 |
| 疑似占座 metric | `app.py` | 修改 | 管理员视图重点展示；学生端只通过座位状态看到 |
| 楼层 selectbox | `app.py` | 修改 | 增加区域筛选，选项由现有数据动态生成 |
| 四列座位卡片 | `render_seat_grid` | 删除并替换 | 替换为 polygon 座位布局图 |
| 人/物检测文本 | `render_seat_grid` | 移至管理员视图 | 学生端不得展示 |
| 无人有物累计文本 | `render_seat_grid` | 移至管理员视图 | 学生端不得展示 |
| 人流拥挤程度 metrics | `render_crowding` | 修改 | 更名、补单位、补数据缺失状态 |
| Streamlit 默认 line chart | `render_crowding` | 修改 | 保留一张清晰折线图，补标题、图例、时间范围和预测不可用提示 |
| 开发命令空状态 | `render_seat_grid` | 删除 | 不向真实用户展示 `python3 -m src.main --mock` |

## 6. 拟修改的文件

| 文件 | 操作 | 具体内容 |
|---|---|---|
| `.gitignore` | 新增 | 排除虚拟环境、缓存、密钥、模型、视频、图片、私有数据和 `output/` |
| `src/dashboard/app.py` | 修改 | 改为页面组装层：加载适配层数据，渲染 `st.tabs`，调用学生/管理员渲染函数 |
| `src/dashboard/data_provider.py` | 新增 | 读取本地 JSON，处理缺失/损坏/字段兼容，返回统一字段模型和数据来源元信息 |
| `src/dashboard/components.py` | 新增 | 放置状态标签、核心指标、区域概览、异常表格、人流图等 Streamlit 组件 |
| `src/dashboard/seat_layout.py` | 新增 | 根据 `src/data/seats.json` polygon 生成中性 SVG/HTML 座位布局图 |
| `src/dashboard/styles.py` | 新增 | 集中管理状态中文名、颜色、拥挤等级阈值、图例样式 |
| `tests/test_dashboard_data_provider.py` | 新增 | 使用 `unittest` 覆盖字段兼容、拥挤等级、错误状态、polygon 分组、异常排序、未知状态 |
| `tests/fixtures/*` | 新增 | 独立测试 JSON，不修改 `src/data` 和 `output` |
| `docs/TECH.md` | 可选修改 | 仅在代码完成后补充前端数据适配层说明；本轮计划阶段不改 |

不修改：

- `src/state_machine/rules.py`
- `src/detection/*`
- `src/seat_mapping/*`
- `library_schema_fixed.sql`
- `seat_status_simulation.csv`
- 真实或模拟数据文件内容

Git 保护要求：

- 当前项目不是 Git 仓库。
- 已先准备 `.gitignore`，至少排除 `.venv/`、`venv/`、`__pycache__/`、`*.pyc`、`.env`、`.env.*`、`*.pt`、`*.onnx`、视频文件、图片文件、`data/raw/`、`data/private/`、`output/`、`.streamlit/secrets.toml`。
- 不提交图书馆原始视频、监控抽帧、真实闸机记录、个人数据、密钥或模型大文件。
- 创建 `.gitignore` 后应先输出拟纳入 Git 的文件清单；等待确认后才可执行 `git add` 和 commit。
- 本轮不初始化 Git，不执行 `git add .`。

## 7. 每个文件的具体修改内容

### `src/dashboard/app.py`

- 保留原启动入口。
- 删除直接字段兼容逻辑，例如 `capacity = crowd_status.get("capacity", 1)`。
- 改为调用 `data_provider.load_dashboard_data()`。
- 添加 `st.tabs(["学生视图", "管理员视图"])`。
- 根据适配层返回的状态显示数据来源、更新时间、错误提示。
- 保留自动刷新逻辑，但不在数据缺失时展示旧的默认数字。

### `src/dashboard/data_provider.py`

职责：

- 读取 `output/seat_status.json`。
- 读取 `output/crowd_status.json`。
- 读取 `src/data/seats.json`。
- 处理文件不存在和 JSON 损坏。
- 将多来源字段统一为前端字段。
- 合并 seat status 与 polygon。
- 返回数据和错误状态，不在 UI 组件里散落字段兼容判断。
- 标注 `data_source = "mock"`，用于页面显示“模拟数据，仅用于原型验证”。
- 为未来替换 API provider 保留同名返回结构，但不引入复杂抽象。
- 优先读取 `output/seat_status.json.seats[].camera_id`，缺失时按 `seat_id` 从 `src/data/seats.json` 补齐。
- 检查 `seat_id` 是否重复。
- 将 `floor` 统一转换为字符串。
- 校验 `status` 是否属于已知枚举，未知状态保留原值并返回 warning，不默认为 `FREE`。
- 校验 `current_people >= 0`。
- 校验 `capacity > 0`，否则返回 `invalid_capacity`。
- `current_people > capacity` 时允许展示，但返回数据质量 warning。
- 时间戳无法解析时保留原值，同时返回 warning。
- 缺少 `zone` 时保持为空，不伪造不存在的区域名。

### `src/dashboard/components.py`

职责：

- 渲染学生状态区、核心指标、区域概览、座位详情、人流趋势。
- 渲染管理员概览、异常列表、异常详情。
- 只消费统一字段模型，不直接读文件。
- 所有缺失数据通过统一文案显示。

### `src/dashboard/seat_layout.py`

职责：

- 读取已合并到 seat 对象中的 `polygon`。
- 计算所有 polygon 的画布边界。
- 使用 SVG `<polygon>` 绘制座位。
- 每个 polygon 显示 `seat_id`。
- 根据 `status` 设置颜色、描边和图例。
- 支持选中 seat_id 的高亮样式。
- 不展示原始摄像头图像，不依赖真实监控背景。
- 按 `floor + zone + camera_id` 分组接收座位，不混合不同摄像头坐标系。

交互替代方案：

- MVP 先使用 `st.selectbox` 选择座位或异常座位。
- SVG 负责空间定位与高亮。
- 不为点击 polygon 引入大型依赖。

### `src/dashboard/styles.py`

职责：

- 集中定义状态中文名。
- 集中定义状态颜色。
- 集中定义拥挤等级阈值。
- 集中定义拥挤等级中文名。
- 避免阈值和颜色散落在多个组件中。

## 8. 数据适配层设计

建议返回结构：

```python
{
    "data_source": "mock",
    "seat_updated_at": "...",
    "crowd_updated_at": "...",
    "seats": [...],
    "crowd": {...},
    "errors": {
        "seat": None,
        "crowd": None,
        "layout": None
    },
    "warnings": []
}
```

错误状态建议：

| 错误码 | 页面文案 |
|---|---|
| `missing_file` | 数据读取失败 |
| `invalid_json` | 数据读取失败 |
| `missing_field` | 暂无座位数据 / 暂无人流数据 |
| `empty_seats` | 暂无座位数据 |
| `invalid_capacity` | 容量数据缺失 |
| `empty_history` | 暂无人流数据 |
| `missing_forecast` | 预测数据暂不可用 |
| `duplicate_seat_id` | 数据读取失败 |
| `missing_polygon` | 暂无座位布局数据 |
| `invalid_polygon` | 暂无座位布局数据 |

适配层原则：

- 不使用误导性默认值。
- 不将缺失的 `capacity` 默认成 1。
- 不将缺失的 `current_people` 默认成 0。
- 不将缺失的 `crowd_level` 默认成 low。
- 不在真实页面显示开发命令。
- warning 不阻断页面渲染，error 才阻断对应组件。

## 9. 统一字段模型

### Seat

| 字段 | 类型 | 说明 |
|---|---|---|
| `seat_id` | string | 座位唯一编号 |
| `floor` | int/string | 楼层 |
| `zone` | string | 区域 |
| `camera_id` | string/null | 摄像头编号，同一布局图的坐标系边界 |
| `status` | string | `FREE/OCCUPIED/POSSIBLY_OCCUPIED/SUSPICIOUS/UNAVAILABLE` |
| `has_person` | bool/null | 是否检测到人，管理员可见 |
| `has_object` | bool/null | 是否检测到物品，管理员可见 |
| `unattended_minutes` | int/null | 无人有物持续时间，管理员可见 |
| `updated_at` | string/null | 最后更新时间 |
| `polygon` | list[list[number]]/null | 座位布局坐标 |

### Crowd

| 字段 | 类型 | 说明 |
|---|---|---|
| `current_people` | int/null | 当前馆内人数 |
| `capacity` | int/null | 图书馆总容量 |
| `crowd_ratio` | float/null | `current_people / capacity` |
| `crowd_level` | string/null | `LOW/MEDIUM/HIGH/FULL` |
| `recorded_at` | string/null | 人流数据记录时间 |
| `history` | list | 历史馆内人数 |
| `forecast_30m` | dict/null | 未来 30 分钟预测；当前为空 |
| `data_source` | string | `mock` 或未来 `api` |

## 10. 现有字段映射表

### Seat 字段映射

| 统一字段 | 当前来源字段 | 说明 |
|---|---|---|
| `seat_id` | `output/seat_status.json.seats[].seat_id` | 直接映射 |
| `floor` | `output/seat_status.json.seats[].floor`，缺失时可由 `src/data/seats.json` 补齐 | 不伪造不存在楼层 |
| `zone` | `output/seat_status.json.seats[].zone`，缺失时可由 `src/data/seats.json` 补齐 | 不伪造不存在区域 |
| `camera_id` | 优先 `output/seat_status.json.seats[].camera_id`，缺失时由 `src/data/seats.json[].camera_id` 补齐 | 用于按坐标系分组绘图 |
| `status` | `output/seat_status.json.seats[].status` | 增加前端对 `UNAVAILABLE` 的支持 |
| `has_person` | `output/seat_status.json.seats[].has_person` | 管理员可见 |
| `has_object` | `output/seat_status.json.seats[].has_object` | 管理员可见 |
| `unattended_minutes` | `object_unattended_minutes` 或 `suspect_duration` | 同义字段在适配层统一 |
| `updated_at` | seat 级字段缺失时使用 `output/seat_status.json.updated_at` | 当前 seat 级无独立更新时间 |
| `polygon` | `src/data/seats.json[].polygon` | 按 `seat_id` 合并 |

### Crowd 字段映射

| 统一字段 | 当前来源字段 | 说明 |
|---|---|---|
| `current_people` | `output/crowd_status.json.latest.total_in_library` | 兼容未来 API `current_num` |
| `capacity` | `output/crowd_status.json.capacity` | 缺失或 <=0 时不计算 |
| `crowd_ratio` | `current_people / capacity` | capacity 有效时计算 |
| `crowd_level` | 按统一阈值由 `crowd_ratio` 计算 | 不继续依赖旧 `low/medium/high` 默认值 |
| `recorded_at` | `output/crowd_status.json.latest.recorded_at` | 人流最新记录时间 |
| `history` | `output/crowd_status.json.history[]` | 保留历史人数折线 |
| `forecast_30m` | 当前无字段 | 显示“预测数据暂不可用” |
| `data_source` | 适配层固定 `mock` | 页面显示模拟数据标签 |

## 11. Polygon 座位图实现方案

实现方式：

- 使用 Python 字符串生成 SVG。
- 通过 `st.markdown(svg_html, unsafe_allow_html=True)` 渲染。
- 如 `st.markdown` 对 SVG 渲染不稳定，可使用 `streamlit.components.v1.html`，它属于 Streamlit 内置模块，不视为新增第三方依赖。
- 画布尺寸由所有 polygon 坐标自动计算，增加 padding。
- 每个 seat 生成：
  - `<polygon points="...">`
  - `<text>` 显示 `seat_id`
- 状态颜色来自 `styles.py`。
- 选中座位使用更粗描边或外框高亮。
- 下方提供图例，文字和颜色同时表达状态。
- 对 `seat_id`、`floor`、`zone`、`camera_id` 等文本使用 `html.escape`。
- 校验 polygon 至少包含 3 个有效坐标点。
- 忽略非法坐标并返回明确错误状态。
- 使用 SVG `viewBox` 自动缩放原始图像坐标。
- 不拼接未经转义的外部字符串。
- 同一 SVG 只绘制同一个 `floor + zone + camera_id` 分组内的 polygon。

状态视觉建议：

| 状态 | 中文 | 用途 | 颜色建议 |
|---|---|---|---|
| `FREE` | 空闲 | 可用座位 | 绿色 |
| `OCCUPIED` | 使用中 | 正常占用 | 蓝色 |
| `POSSIBLY_OCCUPIED` | 暂不可用 | 学生端避免误用；管理员端异常观察 | 橙色 |
| `SUSPICIOUS` | 疑似占座（待确认） | 管理员重点关注 | 红色 |
| `UNAVAILABLE` | 不可用 | 维修/封闭 | 灰色 |

不做：

- 不显示原始监控画面。
- 不接摄像头背景图。
- 不引入大型可视化依赖。
- 不为了展示效果伪造 `UNAVAILABLE` 座位。

## 11.1 自动测试计划

Step 1 使用 Python 标准库 `unittest`，不新增 pytest 等依赖。

| 测试主题 | 覆盖内容 |
|---|---|
| seat 字段兼容 | `object_unattended_minutes`、`suspect_duration`、`unattended_minutes` 均映射为 `unattended_minutes` |
| crowd 字段兼容 | `latest.total_in_library`、未来 API `current_num` 均映射为 `current_people` |
| 拥挤等级边界 | `0.49 -> LOW`、`0.50 -> MEDIUM`、`0.74 -> MEDIUM`、`0.75 -> HIGH`、`0.89 -> HIGH`、`0.90 -> FULL` |
| 无效容量 | capacity 缺失、0、小于 0 |
| 数据错误 | 文件不存在、JSON 损坏、seats 为空、history 为空 |
| Polygon 合并 | 按 seat_id 合并；缺 polygon 返回明确状态；不同 camera_id 不合并到同一布局分组 |
| 异常座位排序 | `SUSPICIOUS` 优先、`unattended_minutes` 更长优先、`updated_at` 更新优先 |
| 状态异常 | 未知状态不崩溃，显示“未知状态”，不默认为 `FREE` |

测试数据约束：

- 测试使用 `tests/fixtures` 或临时目录。
- 不直接依赖当前 `output/*.json`。
- 不修改 `src/data` 与 `output` 中的现有数据。
- 重复运行测试结果必须稳定。

## 12. 空数据和错误状态方案

| 场景 | 学生视图 | 管理员视图 |
|---|---|---|
| seat 文件不存在 | 显示“数据读取失败” | 显示“数据读取失败” |
| seat JSON 损坏 | 显示“数据读取失败” | 显示“数据读取失败” |
| seat 列表为空 | 显示“暂无座位数据” | 显示“暂无座位数据” |
| layout 文件不存在或 polygon 缺失 | 显示“暂无座位布局数据” | 显示“暂无座位布局数据” |
| crowd 文件不存在 | 显示“暂无人流数据” | 不显示人流相关默认值 |
| crowd JSON 损坏 | 显示“数据读取失败” | 显示“数据读取失败” |
| capacity 缺失或 <=0 | 显示“容量数据缺失” | 使用率显示“暂无数据” |
| history 为空 | 显示“暂无人流数据” | 不影响异常列表 |
| forecast 不存在 | 显示“预测数据暂不可用” | 不展示预测 |

## 13. 当前仍缺失的后端字段

本轮不能伪造以下字段，只能记录为后续缺口：

| 缺失字段 | 用途 | 影响 |
|---|---|---|
| `forecast_30m` | 学生端未来 30 分钟人数/趋势 | 当前只能显示“预测数据暂不可用” |
| `processing_status` | 管理员处理状态 | 本轮不实现操作按钮 |
| `operator` / `admin_id` | 记录处理人 | 本轮不实现操作日志 |
| `action_time` | 记录处理时间 | 本轮不实现操作日志 |
| `action_result` | 记录处理结果 | 本轮不实现处理闭环 |
| `admin_note` | 管理备注 | 本轮不实现备注 |
| seat 级 `updated_at` | 每个座位独立更新时间 | 当前使用全局 `seat_updated_at` |
| `UNAVAILABLE` 来源字段 | 不可用座位来源 | 前端支持，但不伪造数据 |

## 14. 明确不在本轮实现的功能

- 不接入真实 API。
- 不引入 Vue、React、Java、FastAPI 或新前端框架。
- 不新增数据库表。
- 不修改数据库结构。
- 不修改 AI 状态机。
- 不修改检测、映射、状态机业务逻辑。
- 不修改真实数据文件或模拟数据文件内容。
- 不生成随机预测。
- 不显示原始摄像头图像。
- 不实现管理员确认占座、标记误判、暂不处理、操作日志。
- 不为了点击 polygon 引入大型依赖。

## 15. 分步骤实施顺序

### Step 0：更新计划与 Git 忽略规则

修改文件：

- 修改 `ui-refactor-plan.md`
- 新增 `.gitignore`

工作内容：

- 将 `camera_id` 坐标系边界、Git 敏感数据保护、自动测试、SVG 安全、数据校验写入计划。
- 输出拟纳入 Git 的文件清单。
- 不初始化 Git，不执行 `git add`。

验收标准：

- `.gitignore` 覆盖敏感和大文件类型。
- 计划中明确本轮不修改数据库、状态机、真实数据文件。

### Step 1：新增配置、数据适配层和自动测试

修改文件：

- 新增 `src/dashboard/styles.py`
- 新增 `src/dashboard/data_provider.py`
- 新增 `tests/test_dashboard_data_provider.py`
- 新增 `tests/fixtures/*`

工作内容：

- 定义状态中文名、颜色、拥挤等级阈值。
- 读取三个本地数据文件。
- 统一 seat 和 crowd 字段。
- 按 seat_id 合并 polygon 和 camera_id。
- 按 `floor + zone + camera_id` 生成 layout 分组。
- 删除误导性默认值策略。
- 增加 unittest 自动测试。

验收标准：

- 文件缺失、JSON 损坏、字段缺失均返回明确错误状态。
- `capacity <= 0` 不计算拥挤等级。
- 不出现 `capacity=1`、`current_people=0`、`crowd_level=low` 这类误导性默认值。
- 未知状态不崩溃，不默认为 `FREE`。
- 不同 `camera_id` 的 polygon 不合并到同一布局分组。
- 自动测试通过。

### Step 2：实现学生视图

修改文件：

- 修改 `src/dashboard/app.py`
- 新增/修改 `src/dashboard/components.py`
- 新增 `src/dashboard/seat_layout.py`

工作内容：

- 增加 `st.tabs`。
- 学生 tab 展示状态区、核心指标、区域概览、座位布局、座位详情、人流趋势。
- 学生端隐藏检测细节。
- 预测缺失显示“预测数据暂不可用”。

验收标准：

- 页面明确显示“模拟数据，仅用于原型验证”。
- 学生端不展示 `has_person`、`has_object`、`unattended_minutes`。
- 座位图使用 polygon，而不是固定四列卡片。
- 图表有标题、单位、图例、时间范围。

### Step 3：实现管理员视图

修改文件：

- 修改 `src/dashboard/app.py`
- 修改 `src/dashboard/components.py`
- 修改 `src/dashboard/seat_layout.py`

工作内容：

- 管理员 tab 展示管理概览。
- 展示异常座位列表。
- 根据排序规则排序异常座位。
- 选择异常座位后高亮座位图。
- 展示管理员可见判断依据。

验收标准：

- 异常列表只包含 `POSSIBLY_OCCUPIED` 和 `SUSPICIOUS`。
- 排序符合 SUSPICIOUS 优先、持续时间优先、更新时间优先。
- 无处理按钮和假处理状态。
- 不展示原始图像或个人身份信息。

### Step 4：空数据和错误状态检查

修改文件：

- 修改 `src/dashboard/components.py`
- 修改 `src/dashboard/data_provider.py`

工作内容：

- 覆盖文件不存在、JSON 损坏、字段缺失、空列表、无效容量、空 history、无 forecast。
- 删除面向用户的开发命令提示。

验收标准：

- 缺座位时显示“暂无座位数据”。
- 缺人流时显示“暂无人流数据”。
- 读取失败显示“数据读取失败”。
- 容量无效显示“容量数据缺失”。
- 无预测显示“预测数据暂不可用”。

### Step 5：运行验证

验证命令：

```bash
python3 -m src.main --mock
python3 -m py_compile src/dashboard/app.py src/dashboard/data_provider.py src/dashboard/components.py src/dashboard/seat_layout.py src/dashboard/styles.py
streamlit run src/dashboard/app.py
```

验收标准：

- Streamlit 页面可正常打开。
- 页面无随机业务数据。
- 页面无意义不明指标。
- 学生/管理员信息分离。
- 桌面宽度不横向溢出。
- 当前数据来源均可追溯到本地 JSON。

## 16. 每一步的验收标准汇总

| 步骤 | 验收点 |
|---|---|
| Step 0 | 计划已更新，`.gitignore` 已创建，未执行 Git 初始化或提交 |
| Step 1 | 数据适配层可返回统一字段；错误状态明确；无误导默认值 |
| Step 2 | 学生视图能回答拥挤、空座、区域、座位可用性、预测是否可用 |
| Step 3 | 管理员视图能查看异常座位、持续时间、判断依据和空间位置 |
| Step 4 | 所有空数据、错误和缺失字段都有明确用户文案 |
| Step 5 | 项目保持原启动方式，页面可运行，未扩大范围 |

## 17. 回滚方案

当前项目不是 Git 仓库。建议在正式改代码前初始化 Git 或至少复制备份相关文件。

本轮重构实施后的手动回滚路径：

- 恢复 `src/dashboard/app.py` 到修改前版本。
- 删除新增文件：
  - `src/dashboard/data_provider.py`
  - `src/dashboard/components.py`
  - `src/dashboard/seat_layout.py`
  - `src/dashboard/styles.py`
- 保留或删除本计划文档按需要决定。

若用户批准初始化 Git，建议在重构前创建一次 checkpoint：

```bash
git init
git add .
git commit -m "checkpoint before dashboard refactor"
```

本计划阶段不执行以上命令。
