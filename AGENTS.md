# 项目入口

本仓库是账单分类 Web 项目 `renzhong/bill_classifier_web`。前端为 Vue 3，后端为 FastAPI 与 MySQL。先按需阅读 `CLAUDE.md`、`arch.md` 和相关 `docs/`，不要一次加载全部文档。

# 独立工作树

- 每个新的本机编码任务都使用本业务仓库的独立 Git worktree，无需用户重复提醒。若 Codex 已为当前任务创建本仓库的专属 worktree，直接使用，勿重复创建。
- 若任务从主检出启动，在修改仓库前检查 `git status`、分支与远端，核对最新 `origin/main`，自动在主检出的 `.worktrees/<唯一任务标识>/` 创建分离 HEAD 的 worktree；在该工作树内完成本次编码、测试与交付。提交时使用 `codex/` 前缀分支。只读分析无需创建。
- 不复制其他工作树未提交的改动、被忽略的密钥、真实账单或 SQL 快照。各工作树共用专用测试数据库时不要并发恢复快照。

# Spec Kit 试点

- 新 feature 的首次试点使用仓库内 `.agents/skills/` 的 Spec Kit 技能，按需依次执行 `$speckit-specify`、`$speckit-plan`、`$speckit-tasks`、`$speckit-implement`、`$speckit-converge`。现有 PRD 和模块文档是事实依据，`specs/` 只描述本次变化。
- `.specify/memory/constitution.md` 记录项目原则；`.specify/feature.json` 是每个工作树的本机状态，不提交。Git 分支和工作树由 Codex/Git 管理，不以 Spec Kit Git 扩展管理。
- Issue 按需创建；需要评审时，随实现一起在 PR 中展示规格、方案和任务。从远端仓库启动的 Codex Cloud 任务使用已推送版本，不把真实账单、密钥或 SQL 快照上传。

# 安全与环境

- 个人账单、本机 `environment.env` 和 SQL 快照不可提交、上传云端或贴进对话。测试数据操作按 `docs/test-data.md` 执行；恢复前备份并停止后端，不混用业务数据库与专用测试库。
- Python、Node 依赖仅装在本项目的虚拟环境、`node_modules` 或容器内。需新装依赖且尚无隔离环境时先请用户确认。
- Git 身份由 `~/.gitconfig` 的 `includeIf` 选择；不要手动配置全局或仓库级 `user.name/email`。提交信息遵守：主题不超过 50 字符、首字母大写、祈使语气、末尾无句号；空一行后正文按 72 字符折行，写 what 与 why。
- 项目尚未上线，除非用户要求，不新增确定性规则分类策略。
