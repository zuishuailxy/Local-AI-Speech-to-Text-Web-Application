# 阶段二：功能开发与集成

> 状态：进行中（P1 脚手架/配置/健康检查/错误处理/测试隔离已完成）。
> 本文是 OpenCode 实现阶段的关键步骤记录，不是完整对话；会随 P2/P3/P4 继续补充。
> 会话：`ses_e838f4101ffet1mEwSYEGuuSMK`（OpenCode Desktop，`deepseek-flash` high）
> 日期：2026-10-27

## 1. 阶段范围

本阶段从“只有计划和任务清单”推进到可启动的 FastAPI 骨架：

- Python 3.12 虚拟环境与依赖锁定；
- 目录骨架与 `.gitignore`；
- 配置模块；
- 应用工厂、`GET /health`、`GET /`、静态资源挂载；
- 统一错误模型与异常处理器；
- pytest 标记、FakeTranscriber、WAV fixture、测试隔离；
- GitHub Actions `windows-latest` CI 骨架。

## 2. 关键用户指令

> 你只需要提交，我手动来 push。现在开始实施 T0.5，T0.6

> 已经 push，验证 T1.8。先做配置模块

> Windows job 为绿色了，继续开发 T1.4 。注意完成一个核心模块之后都要写单测

> 没问题 继续推进 T1.5 和 1.6

> 我现在把仓库修改为 public 了。你能读取到结果吗？

这些指令确定了三个工作方式：

1. 每个核心模块必须同时提交单测；
2. Windows 实机不可用，以 GitHub Actions 作为兼容性验证；
3. 代理可以提交和推送，但默认尊重“先本地验证、再推送”的节奏。

## 3. 实施步骤与结果

### 3.1 T1.1 目录骨架

- 创建 `app/`、`static/`、`scripts/`、`tests/`、`samples/`、`docs/evidence/`、`.github/workflows/`。
- 添加 `app/__init__.py`、`app/api/__init__.py`、`app/services/__init__.py`。
- `.gitignore` 排除 `.venv/`、`models/`、`.wheelhouse-check/`、缓存、日志、`.DS_Store`。
- 添加 `.python-version` = 3.12。

### 3.2 T1.2 Python 3.12 与依赖锁定

问题：本机系统 `python3` 是 3.9，Homebrew 当前不可用；直接用系统 Python 会偏离题目要求。

处理：

- 使用 uv 管理的 CPython 3.12.13 创建 `.venv`；
- 安装并冻结 41 个精确版本到 `requirements.txt`；
- `pip download --platform win_amd64 --python-version 3.12 --abi cp312 --only-binary=:all:` 成功下载 41 个 Windows wheel；
- 在全新临时 venv 中按 requirements 复装并导入关键模块；
- `pip check` 无冲突。

关键版本：

```text
fastapi 0.162.0
uvicorn 0.54.0
faster-whisper 1.2.1
ctranslate2 4.8.4
av 19.0.2
onnxruntime 1.31.1
websockets 17.3
pytest 9.1.1
httpx 0.28.1
```

证据：`docs/evidence/t1.2-environment.txt`、`windows-wheels.txt`。

### 3.3 T1.3 配置模块

- 新增 `app/config.py`，frozen dataclass `Settings`。
- 路径解析基于项目根，兼容 Windows/POSIX。
- 校验布尔值和正整数，非法值 fail fast 并指出环境变量名。
- 支持 `environ`/`project_root` 注入，测试不污染真实环境。
- 新增 `tests/test_config.py`：21 个测试。

### 3.4 T1.4 应用工厂与健康检查

- `app/main.py` 提供 `create_app(transcriber=None)`。
- `app.state.transcriber` 注入，导入时不加载模型。
- `GET /health` 精确返回 `{"status":"ok"}`。
- `GET /` 返回 `static/index.html`，`/static` 挂载。
- 新增 `tests/test_health.py`、`tests/test_app_factory.py`；实际 uvicorn 启动验证 `/health` 与 `/` 均为 200。
- 新增 `static/index.html` 占位页。

### 3.5 T1.5 统一错误模型

- `app/errors.py`：
  - `ApiError`；
  - `ModelUnavailableError` (503)；
  - `TranscriptionFailedError` (500)；
  - `InvalidAudioError` (400)。
- 统一 JSON：`{"detail": "...", "code": "..."}`。
- 处理 400/404/405/413/415/422/500/503。
- 未捕获异常返回通用 `internal_error`，不泄漏堆栈或请求内容。
- `tests/test_errors.py`：10 个测试。

### 3.6 T1.6 pytest 与测试隔离

- `pytest.ini` 注册 `real_model`、`e2e`，默认排除。
- `tests/conftest.py` 提供：
  - `FakeTranscriber` / `failing_transcriber`；
  - 1 秒 16 kHz WAV、静音 WAV、损坏音频；
  - `TestClient` 与 app fixture。
- `tests/test_fixtures.py` 验证 fixture 与隔离。
- 临时 probe 验证：
  - 默认 `pytest -q`：47 passed，probe deselected；
  - `pytest -q -m real_model`：probe 单独运行。
- 未加载模型、未下载权重、未访问麦克风。

### 3.7 T1.8 Windows CI

- `.github/workflows/windows.yml`：`windows-latest` + Python 3.12；安装依赖、`pip check`、导入检查、`pytest -q`。
- 初次 green run（用户确认）；公开仓库后 API 复核 run `40483713787`：
  - commit `fc8e7f9`；
  - 所有 step success；
  - run URL 记录在 `docs/evidence/t1.8-windows-ci.txt`。
- CI 只证明 Windows Server 上的安装/测试，不代表 Windows 11 实机麦克风已通过；该限制继续保留。

## 4. 测试矩阵（P1）

| 模块 | 文件 | 测试数 |
| --- | --- | --- |
| 配置 | `tests/test_config.py` | 21 |
| 错误处理 | `tests/test_errors.py` | 10 |
| fixture/隔离 | `tests/test_fixtures.py` | 8 |
| 健康检查/静态页 | `tests/test_health.py` | 4 |
| 应用工厂 | `tests/test_app_factory.py` | 4 |
| 合计 | | **47** |

命令：

```bash
python -m pytest -q
```

结果：`47 passed`。

## 5. 遇到的问题与处理

1. **默认 Python 3.9**：改用 uv 管理的 CPython 3.12，避免依赖/类型差异。
2. **PyPI 下载超时**：pip 多次 retry 后成功；requirements 已完整锁定，后续可复用缓存。
3. **Windows 实机缺失**：用 GitHub Actions 替代安装/测试验证，并明确记录“非 Windows 11 实机”。
4. **pytest marker 验证**：临时 probe 首次因文件名不符合 `test_*.py` 未被收集；改名后验证默认排除与 `-m real_model` 覆盖均正常。
5. **GitHub 网络间歇性超时**：push/fetch 偶发 `Empty reply from server`；已成功推送的 commit 以 `origin/main` 与 run 记录为准，不把失败的网络请求当成代码失败。

## 6. 待补充

- P2 音频校验/解码/时长/10 MB 限制；
- `/api/transcribe` 与 FakeTranscriber 契约；
- P3 真实模型、P4 前端、P6 手动/离线验证；
- 阶段三测试报告与修复记录。

## 7. 备注

- 本阶段没有下载 ASR 模型权重，`models/` 为空。
- `app.main` 导入不加载模型，`/health` 与默认测试可离线运行。
- 下一步以 `todo.md` 的 T1.7/P2 任务为准。
