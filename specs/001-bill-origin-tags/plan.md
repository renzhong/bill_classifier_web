# Implementation Plan: 账单归属标签

**Feature ID**: `001-bill-origin-tags` | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

## Summary

复用现有上传任务、账单和标签关联：新账单入库时关联所选标签；历史任务补齐关联；明细页展示并编辑标签。

## Technical Context

**Language/Version**: Python 3.11；TypeScript 5、Vue 3
**Primary Dependencies**: FastAPI、SQLAlchemy 2、Naive UI
**Storage**: MySQL 8；`upload_tasks`、`bills`、`tags`、`bill_tags`
**Testing**: pytest、MySQL 集成测试、前端构建
**Target Platform**: 浏览器与后端容器
**Project Type**: Web 应用
**Performance Goals**: 不为每笔账单额外发起数据库往返
**Constraints**: 用户隔离；不读取真实账单；重复行不改原标签
**Scale/Scope**: 单文件上传和明细页，不增加标签类型

## Constitution Check

- 不内置个人姓名或规则：通过。
- 标签关联及历史补齐按用户边界过滤：通过。
- 复用现有 API 与表，保持已有合同：通过。
- 用合成数据验证：通过。

设计后复核：仍满足以上原则，无例外。

## Project Structure

### Documentation (this feature)

```text
specs/001-bill-origin-tags/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/bill-tags.md
├── quickstart.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/app/tasks/upload_runner.py
backend/app/bills/service.py
backend/migrations/versions/
backend/tests/tasks/
frontend/src/views/BillUpload.vue
frontend/src/views/BillsDetail.vue
docs/api.md
```

**Structure Decision**: 延续现有模块和关联表，不新增服务层。
