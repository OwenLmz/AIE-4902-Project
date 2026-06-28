# Final Midterm Check

日期：2026-06-26

本检查用于冻结中期提交前的运行状态。本阶段未开发新功能，未修改业务代码，未修改 `output/`、`src/data/`、AI 状态机或数据库结构。

## 1. 单元测试

运行命令：

```bash
python3 -m unittest discover
```

结果：

```text
Ran 50 tests in 0.004s
OK
```

结论：通过。

## 2. 编译检查

运行命令：

```bash
python3 -m py_compile src/dashboard/app.py src/dashboard/data_provider.py src/dashboard/components.py src/dashboard/styles.py src/dashboard/seat_layout.py
```

结果：无错误输出。

结论：通过。

## 3. Streamlit 健康检查

运行命令：

```bash
curl -I http://localhost:8501
```

结果摘要：

```text
HTTP/1.1 200 OK
server: uvicorn
content-type: text/html; charset=utf-8
```

结论：当前本地 Streamlit 服务可访问。

## 4. 截图与录屏状态

当前未自动生成截图或录屏，也未伪造截图。

待人工补充：

- `docs/evidence/screenshots/student_summary.png`
- `docs/evidence/screenshots/student_area_overview.png`
- `docs/evidence/screenshots/student_seat_layout.png`
- `docs/evidence/screenshots/student_crowd_trend.png`
- `docs/evidence/screenshots/admin_summary.png`
- `docs/evidence/screenshots/admin_anomaly_table.png`
- `docs/evidence/screenshots/admin_seat_highlight.png`
- `docs/evidence/screenshots/admin_anomaly_detail.png`
- `docs/evidence/dashboard_walkthrough.mp4`

操作清单见：

- `docs/evidence/manual_capture_checklist.md`

## 5. 提交前提醒

- 不要提交 `output/`。
- 不要提交原始视频、真实摄像头图像、真实闸机记录、个人数据、密钥或模型权重。
- 不要执行 `git add .`。
- 贡献表需要团队人工确认后再进入正式报告。
- 当前 Dashboard 使用 mock / 示例数据，不应描述为已接入学校真实系统。
