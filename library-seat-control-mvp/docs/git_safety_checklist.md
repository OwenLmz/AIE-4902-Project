# GitHub 提交安全检查清单

本目录是整理后的 GitHub 提交副本，仅包含课程 MVP 项目运行、测试、文档和演示所需文件。

## 已排除内容

- 本地缓存：`__pycache__/`、`*.pyc`、`.DS_Store`
- 本地环境：`.venv/`、`venv/`
- 密钥配置：`.env`、`.env.*`、`.streamlit/secrets.toml`
- 模型与大文件：`*.pt`、`*.onnx`、视频文件、图片文件
- 原始/私有数据：`data/raw/`、`data/private/`、`src/data/raw/`、`src/data/private/`
- 本地编辑器和开发代理留档目录

## 当前保留内容

- `src/`：项目源码
- `tests/`：单元测试和测试夹具
- `docs/`：PRD、技术说明、操作手册、中期报告材料
- `midterm_report_latex/`：中期报告 LaTeX 框架
- `output/*.json`：无敏感信息的 mock 演示输出，用于保证 Dashboard 开箱可运行
- `src/data/`：示例座位布局和模拟闸机 CSV
- `README.md`、`requirements.txt`

## 提交前人工确认

1. 确认 `output/*.json` 仅为 mock 演示数据。
2. 确认 `src/data/seats.json` 的 polygon 与 `camera_id` 不包含真实敏感摄像头信息。
3. 确认 `src/data/gate_flow.csv` 和 `seat_status_simulation.csv` 不含真实人员记录。
4. 确认没有加入真实视频、监控抽帧、真实闸机记录、个人信息、密钥或模型权重。
5. 使用 `git status --ignored` 查看将提交和被忽略的文件。

## 建议提交方式

进入本提交副本目录后再初始化 Git：

```bash
cd github_submission/library-seat-control-mvp
git init
git status --ignored
git add README.md requirements.txt src tests docs midterm_report_latex output generate_sim_data.py import_simulation.sql library_schema_fixed.sql seat_status_simulation.csv ui-audit.md ui-refactor-plan.md 模块对接说明.md .gitignore
git status
```

确认文件清单无误后再 commit 和 push。
