# Bill Classifier Web Constitution

## Core Principles

### I. 用户配置决定分类行为

系统提供可扩展的分类能力，具体 Pipeline 与策略参数由用户配置。新增分类策略类型必须有明确需求；当前项目尚未上线，不为方便实现而添加确定性规则策略。

### II. 保护账单与用户边界

所有用户级数据按用户隔离；凭证与密钥按现有加密和环境变量约定处理。规格、示例、测试与提交只使用合成数据，不包含个人账单、本机 `environment.env` 或 SQL 快照。

### III. 尊重现有模块合同

新功能沿用 Vue 3、FastAPI、MySQL 与用户可配置 Pipeline 的现有边界。先按 `AGENTS.md` 找到相关模块设计、API 和测试，再提出接口、状态或数据结构变化；变更这些合同时同次更新对应文档。

### IV. 验证与影响相称

按改动风险运行相关测试、类型检查或构建；涉及数据库的验证遵守 `docs/test-data.md`，不得混用业务数据库与专用测试库。纯文档或保持合同的内部修复不强制增加形式化测试。

### V. 规格只描述本次变化

每个需要 Spec Kit 的新 feature 在 `specs/<feature>/` 保留规格、方案与任务，按需参考 PRD，并引用当前架构和模块文档。PRD 是规划，不作为已实现行为的依据；完成后同步受到实际影响的持久文档。

## Development Workflow

- 编码任务使用业务仓库的独立 worktree；Codex 已提供专属工作树时直接使用。
- Spec Kit 负责 specify、plan、tasks、implement、converge；Git 分支和工作树由 Codex/Git 管理，不安装 Spec Kit Git 扩展作为前提。
- GitHub Issue 按跟踪需要使用；需要评审或分享变更时，用 PR 展示规格、方案、任务和实现。
- Python、Node 依赖仅装在项目隔离环境或容器中；不改系统级包环境。

## Governance

本文件为 Spec Kit 生成规格与方案提供项目原则。具体操作约束以仓库 `AGENTS.md`、相关模块文档和当前代码为依据；发现冲突时先核对事实并修正文档。新增原则须说明原因和影响，不因模板示例引入无关流程。

**Version**: 0.1.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
