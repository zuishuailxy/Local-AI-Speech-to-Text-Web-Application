# OpenCode 开发过程记录

本目录保存 OpenCode 关键开发会话的脱敏导出，用于满足题目第 7.3 节“关键开发过程证据”要求。

## 索引

| 阶段 | 文件 | 状态 | 主要内容 |
| --- | --- | --- | --- |
| 阶段一：需求理解与技术设计 | [`01-requirements-and-design.md`](./01-requirements-and-design.md) | 已完成 | 读取题目、需求拆解、ASR 选型、实施计划、D1–D7 决策 |
| 阶段二：功能开发与集成 | [`02-implementation.md`](./02-implementation.md) | 进行中（P1 已记录） | 脚手架、配置、健康检查、错误处理、测试隔离、Windows CI |
| 阶段三：测试与问题修复 | `03-testing-and-fixes.md` | 待生成 | 测试失败、定位、修复与复测记录 |

## 导出原则

- 只保留与需求理解、技术决策、实现和修复相关的关键消息；不提交完整历史对话。
- 不包含模型内部推理过程、工具原始输出、密钥、token、个人路径或无关个人信息。
- 仓库绝对路径统一替换为 `<repo>`。
- 关键结论同时写入 `plan.md`、`todo.md` 和 `docs/ai-development.md`，避免只依赖会话记录。
- 若会话内容与最终代码/文档冲突，以最终代码、测试结果和 `docs/design.md` 为准。

## 会话来源

- 工具：OpenCode Desktop
- 会话 ID：`ses_e838f4101ffet1mEwSYEGuuSMK`
- 会话标题：面试考核题需求分析与规划
- 模型：`deepseek-flash`（variant: high）
- 日期：2026-10-27
- 项目目录：`<repo>`

## 隐私与脱敏

导出前已检查：

- 不包含 GitHub token、API key、账号凭据。
- 不包含用户主目录绝对路径。
- 不包含测试音频中的个人信息（当前阶段尚未录制）。
- 终端命令中的本地路径已替换为 `<repo>`。

如后续提交到公开仓库，仍需在 push 前再次人工检查 `docs/opencode/` 与 `docs/evidence/`。
