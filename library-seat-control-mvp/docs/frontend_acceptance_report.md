# 前端验收报告

验收日期：2026-06-26

## 1. 当前前端页面结构

当前 Streamlit 前端入口为 `src/dashboard/app.py`。

- 页面标题：图书馆智能位控系统
- 数据来源提示：模拟数据，仅用于原型验证
- 侧边栏：5 秒自动刷新开关
- 页面标签页：
  - 学生视图
  - 管理员视图

页面数据统一由 `src/dashboard.data_provider.load_dashboard_data()` 读取和标准化，`app.py` 只负责页面组装。

## 2. 学生视图已实现功能

学生视图由 `src/dashboard/components.py` 中的 `render_student_view()` 组织，已包含：

- 数据来源状态：显示“模拟数据，仅用于原型验证”。
- 座位数据更新时间、人流数据更新时间、自动刷新状态。
- 核心指标：
  - 当前馆内人数 / 图书馆总容量；
  - 当前空闲座位数；
  - 当前拥挤等级；
  - 未来 30 分钟趋势，缺失时显示“预测数据暂不可用”。
- 楼层与区域概览：
  - 按 `floor + zone` 聚合；
  - 展示空闲、使用中、暂不可用、疑似占座、不可用数量；
  - 可用率计算排除 `UNAVAILABLE`；
  - 无有效容量时显示明确空状态，不除以 0。
- 楼层 / 区域筛选入口：
  - 只使用已有座位数据中的楼层和区域；
  - 楼层变化后区域选项动态更新。
- Polygon 座位布局图：
  - 按 `floor + zone + camera_id` 分组；
  - 不混合不同摄像头坐标系；
  - 显示 `seat_id` 和状态中文名；
  - 显示状态图例；
  - 不展示原始摄像头图像；
  - 不展示 polygon 原始坐标。
- 人流趋势：
  - 标题为“图书馆人流趋势”；
  - 显示时间轴说明、人数单位、图例和数据时间范围；
  - 不生成随机预测线；
  - 没有 `forecast_30m` 时显示“未来 30 分钟预测数据暂不可用”。
- 简单座位列表预览：
  - 仅展示学生端可见字段；
  - 不展示 `has_person`、`has_object`、`unattended_minutes`、模型置信度或 polygon 坐标。

## 3. 管理员视图已实现功能

管理员视图由 `src/dashboard/components.py` 中的 `render_admin_view()` 组织，当前是“查看与定位”基础版，已包含：

- 页面状态区：
  - 标题：图书馆座位管理视图；
  - 数据来源：模拟数据，仅用于原型验证；
  - 座位数据更新时间或“暂无座位数据”；
  - 自动刷新状态。
- 管理概览：
  - 暂不可用数量；
  - 疑似占座数量；
  - 当前实际座位使用率；
  - 异常最多区域。
- 异常座位列表：
  - 只包含 `POSSIBLY_OCCUPIED` 和 `SUSPICIOUS`；
  - 字段包括座位编号、楼层、区域、摄像头视角、当前状态、是否检测到人、是否检测到物品、无人有物持续时间、最后更新时间；
  - 无异常时显示“暂无异常座位”。
- 异常座位选择器：
  - 管理员可选择异常座位。
- Polygon 定位图：
  - 按选中座位的 `floor + zone + camera_id` 过滤；
  - 复用 `src/dashboard/seat_layout.py`；
  - 高亮选中座位；
  - 不展示原始摄像头图像或 polygon 坐标。
- 异常座位详情：
  - 座位编号；
  - 楼层；
  - 区域；
  - 摄像头视角；
  - 当前状态；
  - 是否检测到人；
  - 是否检测到物品；
  - 无人有物持续时间；
  - 最后更新时间。

## 4. 明确未实现功能

本阶段不实现以下内容：

- 管理员确认占座按钮；
- 标记误判按钮；
- 暂不处理按钮；
- 管理员处理状态；
- 操作日志；
- 真实 API 接入；
- 真实摄像头画面展示；
- 个人身份识别；
- 生产级权限系统；
- 数据库结构改造。

## 5. 数据来源说明

当前 Dashboard 使用本地 JSON / CSV 模拟数据：

- 座位状态：`output/seat_status.json`
- 人流状态：`output/crowd_status.json`
- 座位 polygon 与补充布局：`src/data/seats.json`
- 模拟闸机数据：`src/data/gate_flow.csv`

页面通过 `data_provider.py` 统一字段模型后展示，不在 UI 层重复处理旧字段兼容逻辑。

## 6. Mock 数据说明

当前项目以 mock 数据验证端到端链路：

图像检测结果 -> 座位映射 -> 状态机 -> 人流统计 -> Streamlit Dashboard。

Mock 数据仅用于原型验证，不代表真实图书馆数据，不包含真实人员身份信息。

## 7. 隐私保护说明

当前前端已遵守以下隐私边界：

- 不展示原始摄像头图像；
- 不展示真实监控截图；
- 不展示姓名、学号、校园卡号等个人身份信息；
- 不展示模型置信度；
- 不上传或要求访问真实视频；
- 不接入真实闸机记录；
- 不读取密钥或 `.env` 文件。

## 8. 禁止项检查结果

对 `src/dashboard` 执行风险词搜索，未发现以下 UI 功能或字段：

- `Math.random`
- `random`
- `randint`
- `uniform`
- `processing_status`
- `action_result`
- `action_time`
- `operator`
- `admin_note`
- 确认占座
- 标记误判
- 暂不处理
- 原始图像
- 摄像头原图
- 姓名
- 学号
- 校园卡号
- AI Score
- System Performance
- Active Users
- Server Status

部分风险词只出现在历史审计文档、重构计划文档或测试负向断言中，不属于 UI 功能。

## 9. 测试运行结果

运行命令：

```bash
python3 -m unittest discover
```

结果：

```text
Ran 50 tests in 0.005s
OK
```

## 10. 编译检查结果

运行命令：

```bash
python3 -m py_compile src/dashboard/app.py src/dashboard/data_provider.py src/dashboard/components.py src/dashboard/styles.py src/dashboard/seat_layout.py
```

结果：通过，无编译错误。

## 11. Streamlit 服务检查结果

服务检查命令：

```bash
curl -I http://localhost:8501
```

结果：

```text
HTTP/1.1 200 OK
```

## 12. 当前限制

- 当前数据仍为 mock 数据，未接入真实摄像头、真实闸机和真实后端 API。
- 当前管理员视图仅支持查看和定位，不支持处理闭环。
- 当前 dashboard 不做用户登录、权限控制和审计日志。
- 当前 `forecast_30m` 缺失时只显示不可用提示，不伪造预测。
- 当前不保证生产环境的高并发、稳定性和部署安全。

## 13. 后续建议

- Final delivery 前补充一组人工截图和录屏。
- 若确需管理员处理闭环，应先定义后端持久化字段，再实现按钮。
- 与图像算法同学确认 `camera_id`、`seat_id`、polygon 坐标系一致性。
- 与数据建设同学确认 mock 数据与后续数据仓库字段映射关系。
