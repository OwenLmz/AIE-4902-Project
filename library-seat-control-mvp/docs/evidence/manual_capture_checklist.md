# 人工截图与录屏操作清单

日期：2026-06-26

当前环境未生成自动截图。请在本地浏览器人工截图和录屏，不要伪造截图。

## 1. 截图前准备

1. 启动 Streamlit：

```bash
streamlit run src/dashboard/app.py
```

2. 确认页面显示：

```text
模拟数据，仅用于原型验证
```

3. 确认页面没有显示：

- 原始摄像头图像；
- 真实监控截图；
- 姓名；
- 学号；
- 校园卡号；
- 个人身份信息；
- 管理员确认占座 / 标记误判 / 暂不处理按钮；
- `processing_status`、`action_result`、`operator`、`admin_note` 等假处理字段。

## 2. 截图清单

截图保存目录：

```text
docs/evidence/screenshots/
```

### 学生端

1. `student_summary.png`：核心指标区，包括数据来源、当前人数 / 容量、空闲座位、拥挤等级、未来趋势提示。
2. `student_area_overview.png`：楼层与区域概览。
3. `student_seat_layout.png`：Polygon 座位布局。
4. `student_seat_detail.png`：座位详情。
5. `student_crowd_trend.png`：人流趋势图。

### 管理员端

1. `admin_summary.png`：管理概览。
2. `admin_anomaly_table.png`：异常座位列表。
3. `admin_seat_highlight.png`：异常座位高亮定位。
4. `admin_anomaly_detail.png`：异常座位详情。

## 3. 录屏脚本

建议录屏文件名：

```text
docs/evidence/dashboard_walkthrough.mp4
```

录屏流程：

1. 打开 Dashboard。
2. 展示学生视图。
3. 说明当前是模拟数据。
4. 展示核心指标。
5. 展示区域概览。
6. 选择楼层 / 区域。
7. 展示 Polygon 座位图。
8. 选择座位查看详情。
9. 展示人流趋势。
10. 切换管理员视图。
11. 展示异常概览。
12. 选择异常座位。
13. 展示异常座位高亮定位。
14. 展示异常详情。
15. 说明当前不展示原始图像、不识别个人身份、不做管理员处理按钮。

## 4. 录屏口播提示

可以用以下表述：

```text
当前系统是课程 MVP 原型，Dashboard 使用模拟数据进行验证。系统展示的是座位状态和人流趋势，不展示摄像头原图，也不识别姓名、学号或校园卡号。管理员视图当前只支持异常查看和定位，不提供确认占座或误判处理按钮。
```
