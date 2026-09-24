# 账单分类项目的 Codex 开发环境方案

状态：Codex 与 Spec Kit 基础配置已落地，首个 feature 试点待进行 · 2026-09-24

业务仓库：`renzhong/bill_classifier_web`；本机独立仓库：`~/codex/bill_classifier_web`
调查基线：`origin/main` 的 `cc3e1ea`，已在配置前核对与本机 `main` 一致。

## 评审结论

1. **项目规则和文档入口使用 Codex 原生机制。** 仓库根 `AGENTS.md` 放简短、稳定的约束；模块需要特殊约束时使用就近 `AGENTS.md`；`.agents/skills/` 放按需加载的技能；架构、目录索引和业务合同仍是普通文档。不引入 rulesync 或多工具生成目录。[Codex 指令发现](https://developers.openai.com/codex/guides/agents-md)、[技能发现](https://developers.openai.com/codex/skills)。
2. **SDD 先试 GitHub Spec Kit 核心流程。** 使用它的 Codex 集成生成本次变更的规格、方案与任务；是否在 GitHub 建 Issue 或 PR 按实际协作需要决定。暂不安装 Spec Kit 的 Git 扩展，它管理 feature 分支，并不负责将规格和方案维护在 GitHub Issue/PR 中。OpenSpec 与 Matt Pocock 的 skills 作为备选，见第 4～5 节。
3. **编码任务优先使用 Codex 原生 Worktree。** 新业务检出已建立在 `~/codex/bill_classifier_web`，Codex 桌面应用已登记同名业务项目；旧 `stock` 项目仍指向外层目录。从业务项目新建编码任务时选择 Worktree，应用会为任务创建专属工作树。从 Local 主检出启动时，仓库 `AGENTS.md` 的手动创建规则仅作后备。只读问答与方案评审不创建空工作树。详见第 6 节。
4. **保留目录索引、就近模块设计和渐进披露。** 这些描述当前代码，不交给 SDD 工具重复维护。复杂变更的 spec 只描述本次要改变什么。

已在业务仓库初始化 Spec Kit 1.0.10 的 Codex 集成，并填写项目 constitution；CLI 安装在仓库自己的 `.venv`，虚拟环境不提交。当前没有生成真实 feature spec，也没有改动业务代码。本机主检出的配置文件仍需进入远端 `main`，新建 Worktree 或 Cloud 任务才能从该版本取得它们。Codex 应用已新增 `bill_classifier_web` 项目，旧 `stock` 项目仍保留。

## 1. 当前项目中要解决的问题

项目已有 Vue 3、FastAPI、MySQL、用户可配置的 AI 分类 Pipeline，以及 `CLAUDE.md`、`arch.md`、`prd/` 和专题文档。基线约 176 个 Git 跟踪文件。现有 CI 执行后端 Ruff、迁移与 pytest，并独立构建前端。

目前可以看到具体的文档漂移：

| 文档 | 当前代码 | 影响 |
|---|---|---|
| `arch.md` §7 写 Provider 的 `classify(prompt, ctx)` | [实际接口](../backend/app/ai/base.py)是 `chat(*, prompt, model, api_key, base_url)` | 新增 Provider 容易写错接口 |
| `arch.md` §6 描述先分类再持久化 | [上传任务](../backend/app/tasks/upload_runner.py)先插入并提交，再分类并回写 | 容易误判事务和失败后的账单状态 |
| `CLAUDE.md` §6 写早期测试总数 | [现有 CI](../.github/workflows/ci.yml)已经执行 MySQL 集成测试 | 容易漏掉验证 |

所以需要的不只是文档数量，而是“哪些文档描述当前事实、每次变化如何同步、AI 怎样找到它们”。本轮不按过时的文件数量或旧提交来推导当前状态。

## 2. Codex 原生的规则与文档布局

```text
bill_classifier_web/                    # 业务 Git 仓库根
├── AGENTS.md                          # 每次加载：项目身份、硬约束、阅读路径、验证原则
├── .agents/skills/                    # 按需加载：Spec Kit 的 Codex 技能
├── .specify/                          # Spec Kit 的模板、脚本与配置
├── specs/                             # 每个 feature 的 spec.md、plan.md、tasks.md
├── README.md                          # 人类入口
├── arch.md                            # 系统级架构与关键运行路径
├── prd/                               # 产品行为；标出已实现和待实现
├── docs/
│   ├── repo-map.md                    # 每个跟踪目录的职责、划分理由和设计文档
│   ├── testing.md                     # 复用已有测试说明
│   ├── api.md                         # 复用已有接口说明
│   ├── parser-spec.md                 # 复用已有解析合同
│   ├── strategy-types.md              # 复用已有扩展合同
│   └── adr/                            # 少量长期架构决策
├── backend/
│   ├── AGENTS.md                      # 后端专属的短约束
│   └── app/<独立模块>/.arch/module-design.md
└── frontend/
    ├── AGENTS.md                      # 前端专属的短约束
    └── src/<独立模块>/.arch/module-design.md
```

其中 `AGENTS.md`、`.agents/skills/` 和 `.specify/` 已建立；`specs/` 将由首个 feature 生成，目录索引与局部设计仍是后续文档整理工作。现有 `CLAUDE.md` 在整理完成前保留为迁移参考；与 `AGENTS.md` 重叠的约束应集中到新入口，避免今后两份规则相互矛盾。现有产品文档和测试说明不因采用 Codex 而搬进技能。插件作为能力来源，可以照常使用；仓库本地的事实和约束仍由仓库自身维护。[Codex Skills 与插件](https://developers.openai.com/codex/skills)。

### 2.1 入口保持短

仓库 `AGENTS.md` 建议只写项目事实、不可违反的边界、如何选择模块文档、测试和交付要求，目标不超过 80 行。个人账单、密钥、测试数据库恢复红线也写在这里。后端和前端的差异进入相应的子目录 `AGENTS.md`。

Codex 会按仓库根至当前工作目录查找指令；启动于仓库根时，不能假设它已经读取所有后代目录中的 `AGENTS.md`。因此根入口必须写明：**定位改动文件后，先读该目录对应的设计和局部规则**。技能只在任务适用时加载全文，适合 Spec Kit 这样的工作流；普通文档链接不会自动递归加载。[官方指令说明](https://developers.openai.com/codex/guides/agents-md)、[官方技能说明](https://developers.openai.com/codex/skills)。

### 2.2 每个目录如何找到设计

`docs/repo-map.md` 手工维护，每个 Git 跟踪目录至少有一行：**路径、职责、为什么这样划分、设计文档、相关测试**。普通子目录可以指向父模块设计的明确章节；新增独立职责时，再就近创建自己的设计。这样保证每个目录有设计归属，又避免给 `migrations/versions` 或 `api/v1` 制造一份空壳文档。

| 现有目录 | 应回答的设计问题 |
|---|---|
| `backend/app/parsers/` | 外部文件怎样转换为标准账单；坏行、编码、金额如何处理 |
| `backend/app/tasks/` | 上传、入库、分类、回写的状态与事务在哪里分界 |
| `backend/app/classify/` 与 `strategy_types/` | 执行顺序、终态、策略注册与参数合同 |
| `backend/app/ai/` 与 `providers/` | 凭证归属、解密时机、外部模型协议与错误 |
| `backend/app/bills/`、`pipeline/` | 账单操作与用户配置怎样影响分类 |
| `backend/app/models/`、`schemas/`、`migrations/` | 持久化字段、API 形状和数据库演进如何关联 |
| `backend/app/auth/`、`core/` | 身份、用户隔离、连接和通用响应由谁负责 |
| `backend/app/categories/`、`tags/`、`dicts/`、`assets/`、`incomes/`、`reports/` | 各自的业务边界、金额与查询口径 |
| `frontend/src/api/`、`stores/`、`router/` | 网络调用、跨页状态、导航与权限边界 |
| `frontend/src/views/`、`components/`、`styles/` | 页面编排、复用组件和样式归属 |
| `backend/tests/`、`devdata/`、`scripts/` | 验证分层、合成数据和本机测试工具 |
| `docker/`、`nginx/`、`.github/`、`docs/`、`prd/` | 部署、CI、文档治理与产品需求归属 |

索引会展开所有实际跟踪子目录；表里只概括主要模块。`backend/app/api/v1/`、`backend/migrations/versions/`、`nginx/sites/` 等也须有索引行。`.venv`、`node_modules`、缓存、生成产物和上传数据不纳入索引。

每个独立模块的设计文档采用短格式：职责与非职责、划分理由、输入输出及合同链接、允许的依赖、正常与失败路径、不变量、扩展位置、测试。详细字段和 API 合同链接已有专题文档，不复制整份。系统层仍以 `arch.md` 为准。

### 2.3 渐进式阅读

```text
AGENTS.md（每次）
  → repo-map.md（定位）
  → 本次涉及的模块设计、局部 AGENTS.md
  → 相关 PRD、接口、测试和 ADR
  → 需要复杂功能流程时读取 Spec Kit 技能
```

例如修改微信 XLSX 解析，先读 `parsers` 设计和解析合同；若影响持久化，再读 `tasks` 与 `models`。无需预读整个产品需求或所有 AI Provider。

## 3. 文档如何跟随迭代

| 改动 | 同次需要更新或核对 |
|---|---|
| 新增、移动、删除目录或改变职责 | `repo-map.md` 和对应设计 |
| API、数据字段、数据库约束改变 | 模块设计、合同/PRD、迁移与验证 |
| 状态、事务、错误语义改变 | 相关模块设计、行为验收与测试 |
| 跨模块依赖或重大架构选择改变 | 双方模块设计、`arch.md`，必要时 ADR |
| 环境、测试、部署、Codex 规则改变 | 对应操作文档、`AGENTS.md` 或技能 |
| 保持现有合同的内部修复 | 核对相关文档，交付说明写明“无需改文档”的理由 |

“每次迭代更新”是每次完成影响核对，存在实质变化时同步修改。不要为了让 Markdown 出现差异而重写无变化的设计。

初期只加轻量检查：用 Git 跟踪目录核对索引覆盖、检查链接存在、标出受影响模块；不自动推断“为什么这样划分”。结构可以由脚本或 CI 验证，行为正确性仍靠测试和评审。首期不需要为这套检查开发新框架。

## 4. 三个现成流程的比较

| 方案 | 当前形态 | 与本项目及 GitHub 协作的关系 |
|---|---|---|
| [GitHub Spec Kit](https://github.github.com/spec-kit/) | 官方 CLI + Codex 技能；specify → plan → tasks → implement → converge | 规格、方案和任务是仓库中的 Markdown，可通过 PR 评审；可选 `taskstoissues` 把任务转换成 GitHub Issues；推荐先试 |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md) | 当前规格与变更包分开；完成后归档和回填 | 适合长期维护行为规格，但会与现有 `prd/` 形成需要治理的双份事实 |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | 可组合的工程技能，如 `grill-with-docs`、`to-spec`、`to-tickets`、`implement` | 偏重需求澄清、术语和 issue tracker；若试点表明 Spec Kit 负担过高，再考虑选用其中的技能 |

**Spec Kit 的 Git 扩展不是 GitHub Issue/PR 集成。** 它提供 feature 分支创建、命名与校验，和本次想试的规格、方案、任务流程没有必需关系。本试点不安装它。Spec Kit 的 `taskstoissues` 只是可选的任务转 Issue 命令，不表示 `spec.md`、`plan.md` 与 GitHub Issue/PR 自动双向同步。[Git 扩展定义](https://github.com/github/spec-kit/blob/main/extensions/git/extension.yml)、[Spec Kit 命令说明](https://github.github.com/spec-kit/reference/agentic-sdd.html)。

Matt Pocock 仓库当前提供 Codex 技能安装方式，但其原生 Codex 插件仍在规划中；`setup-matt-pocock-skills` 会配置 issue tracker、术语文档与相关约定。[项目 README](https://github.com/mattpocock/skills)、[初始化技能](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md)。先完成 Spec Kit 试点，再决定是否需要补充其他技能。

## 5. Spec Kit 的建议试用方式

采用 [官方的既有项目指南](https://github.github.com/spec-kit/guides/existing-projects.html)。仓库级初始化已在本次主检出完成：`specify-cli==1.0.10` 安装于本项目 `.venv`，使用 `--integration codex` 生成 `.specify/` 与 `.agents/skills/`，并将项目约束写入 constitution；没有向系统 Python 安装。首个真实 feature 再从业务项目的独立 Worktree 运行核心流程，核对生成的 `specs/` 及实现改动。[Codex 集成](https://github.github.com/spec-kit/reference/integrations.html)。

先选一个范围明确、可以独立评审的需求，按官方技能顺序生成规格、技术方案、任务并完成收敛验证。`constitution` 从当前代码、测试和已确认约束提炼，不凭空增加“必须全面重构”之类规则。现有 PRD、模块设计是事实依据；新 spec 只写本次变化。[既有项目指南](https://github.github.com/spec-kit/guides/existing-projects.html)。

试点默认将 `specs/<feature>/spec.md`、`plan.md`、`tasks.md` 作为仓库内的变更文档，在需要分享或审查实现时随代码进入 PR。**不要求每个 feature 都有 Issue**；有跟踪需求时再建 Issue，并在 PR 中引用。若确实需要把 `tasks.md` 转成独立 Issues，再单独评估可选的 `taskstoissues` 命令及其 GitHub `origin`、GitHub MCP 前提；这不是规格与方案的同步机制。[Spec Kit 命令说明](https://github.github.com/spec-kit/reference/agentic-sdd.html)。

试点时验证四件事：

1. Codex 创建的业务 worktree 中可以完成 Spec Kit 核心流程；分支由 Codex/Git 管理，不让 Spec Kit 的 Git 扩展介入。
2. `spec.md`、`plan.md`、`tasks.md` 在 `specs/<feature>/` 中对应同一需求，方案和任务可供直接评审。
3. `.specify/feature.json` 是当前工作树的本机 feature 指针，切换 feature 时核对它所指向的目录；该指针由 Spec Kit 忽略，不作为跨工作树共享状态。[Spec Kit 核心参考](https://github.github.com/spec-kit/reference/core.html)。
4. 没有意外自动提交；工作树可以取得既有 Git 身份，不通过设置全局或仓库级身份来掩盖问题。

若核心流程不适合当前团队，再试 OpenSpec 或精选 Matt 技能。不要为了 Issue/PR 映射编写本项目专属 SDD 命令，也不要在试点前安装 Git 扩展。

试点的评价标准：生成的 spec 能否让用户直接 review、是否遵守现有代码边界、任务与验收能否追踪、额外询问是否过多、完成后是否易于回填现有产品与模块文档。保留结果，再决定长期采用哪套。

## 6. Codex、Work、远程与工作树

### 6.1 选择开发入口

**本项目使用 Codex。** 官方将 Codex 用于需要代码库上下文和开发工具的软件开发；ChatGPT Work 主要用于研究、分析和文档等交付。本文中的本机 Git 仓库、终端、代码差异、分支与 worktree 都按 Codex 本地项目来设计。Work 可用于独立的调研或文档任务，但不承担本项目的编码入口。[官方快速入门](https://learn.chatgpt.com/docs/quickstart)。

“远程”需要区分三种方式：**手机 Remote** 操作已连接的电脑，代码和工作树仍在该电脑；**SSH 开发机**让项目文件与命令运行在自己的远程主机；**Codex Cloud** 则在云端容器检出仓库并运行任务。前两种可以继续使用相应主机上的 Codex 项目和工作树；手机控制要求主机保持在线，SSH 开发机需要先配置主机、项目与远端 Codex。这些方式都不是 ChatGPT Work；真实账单与本机密钥不应为试点上传。[Codex Remote](https://learn.chatgpt.com/docs/remote)、[远程连接与 SSH](https://learn.chatgpt.com/docs/remote-connections)、[Codex Cloud](https://learn.chatgpt.com/docs/environments/cloud-environment)。

**Worktree 与 Cloud 是新任务的两种运行位置，不能在同一个新任务里同时选择。** 下次在本机开发新 feature 时，选业务项目和 Worktree；需要云端执行时，选 Cloud 与该 GitHub 仓库对应的云端环境。云端任务检出远端分支或提交，不能依赖本机 `.venv`、未提交文件或个人数据。先将本仓库的 Spec Kit 配置提交并推送，再在 [Codex 云端环境设置](https://chatgpt.com/codex/settings/environments) 中连接 `renzhong/bill_classifier_web`，按需配置项目级隔离依赖和测试服务；首次云端任务以读取 constitution、生成一个合成数据 feature 规格为轻量验收。[运行位置](https://learn.chatgpt.com/docs/environments/modes)、[云端环境](https://learn.chatgpt.com/docs/environments/cloud-environment)。

### 6.2 每个编码任务的工作树

Codex 桌面应用已新增 `bill_classifier_web` 项目，路径为 `/Users/zhangrenzhong/codex/bill_classifier_web`。旧 `stock` 项目指向 `/Users/zhangrenzhong/codex/stock`，它本身是另一 Git 仓库；从旧项目创建 Worktree 会针对旧仓库。新任务先选正确的业务项目。

从业务项目新建编码任务时，在输入框下选择 **Worktree** 和起点分支；Codex 会为该任务创建托管工作树，默认以分离 HEAD 开始，同一任务继续使用自己的工作树。侧栏项目菜单还可创建**永久工作树**，它会成为单独的项目，允许多个任务共用；这种方式适合固定开发环境，不提供“一任务一工作树”的隔离。官方文档没有给出项目级“所有新任务自动选 Worktree”的配置，因此方案不能承诺项目设置会完成这一步。[Codex Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)、[环境选择](https://learn.chatgpt.com/docs/environments/modes)。

若编码任务从业务主检出的 **Local** 模式启动，仓库根 `AGENTS.md` 当前要求代理核对状态和远端，在 `.worktrees/<任务标识>/` 手动创建一份标准 Git worktree。它仅是后备路径；这类工作树不由 Codex App 托管，任务结束后需自行核对并清理。已经在专属工作树中的任务不重复创建。只读问答和方案评审不创建工作树。

`AGENTS.md` 与 Spec Kit 配置需提交并推送后，才能由远端 `main` 新建的工作树和云端任务取得。被 Git 忽略的本机配置、虚拟环境、Node 依赖和测试快照通常不随工作树出现；新工作树只在项目隔离环境内安装依赖，不复制真实账单、密钥或 SQL 快照。`.worktreeinclude` 可用于托管工作树复制指定忽略文件，但本项目不将敏感配置列入其中。[Codex Worktrees：ignored files](https://learn.chatgpt.com/docs/environments/git-worktrees)。

工作树隔离代码，不隔离共享服务。多个任务不能并发恢复同一个持久化 MySQL 测试库；数据库、端口和依赖冲突在试点时验证。

### 6.3 验收

- 从 `bill_classifier_web` 项目分别以 Worktree 模式新开两个编码任务：产生不同的业务工作树，任务之间的代码修改互不覆盖，代理不重复创建工作树。
- 从业务主检出的 Local 模式启动编码任务时，后备规则只创建一份标准 Git worktree；只读任务不留下空工作树。
- 从手机连接这台电脑、或连接已配置的 SSH 项目后，核对任务实际运行的仓库和工作树路径，再进行编码。
- 在工作树中测试 Git 提交身份；不设置全局或仓库级 `user.name/email`。
- 后续试点实测数据库、端口和依赖隔离。

## 7. 落地顺序

| 步骤 | 具体工作 | 可核对结果 |
|---|---|---|
| 0 | 保留已登记的业务项目；编码任务选择 Codex 原生 Worktree，Local 启动时使用仓库后备规则 | 工作树来自业务仓库；原生任务不重复创建；不把后备规则误认为项目级自动开关 |
| 1 | 在业务仓库建立短 `AGENTS.md`、目录索引、核心模块设计；修正已发现的文档漂移 | 从仓库根启动能找到正确模块；每个跟踪目录有设计归属 |
| 2 | 已在业务仓库的隔离虚拟环境安装 Spec Kit 1.0.10 并初始化 Codex 集成；首个 feature 再在独立 Worktree 试用核心流程 | `.specify/`、`.agents/skills/` 已就位；首个 `specs/`、feature 状态与提交行为待试点验证 |
| 3 | 用一个真实的、有边界的变更完成 Spec Kit 全流程，并同步当前文档 | spec、实现、测试和模块文档一致；用户能评估流程负担 |
| 4 | 将目录覆盖、断链与必要的依赖边界检查接入现有 CI | 故意遗漏索引或改坏链接时检查准确失败 |

当前执行选择是：**使用 Codex 开发、本机编码任务优先选原生 Worktree、先试 Spec Kit 核心流程，并保留 Cloud 作为可选择的独立运行位置**。GitHub Issue 按跟踪需要使用，PR 可评审规格、方案、任务与实现；Spec Kit Git 扩展不在首轮试点范围。Codex 项目与 Spec Kit 基础配置已建立；首个 feature 的完整流程、云端环境以及目录文档体系仍待验证与实施。
