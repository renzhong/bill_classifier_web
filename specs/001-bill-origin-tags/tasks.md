# Tasks: 账单归属标签

**Input**: [spec.md](spec.md)、[plan.md](plan.md)、[data-model.md](data-model.md)、[contracts/bill-tags.md](contracts/bill-tags.md)

## Phase 1: 上传后保留标签（US1，P1）

- [x] T001 [US1] 在 `backend/app/tasks/upload_runner.py` 给成功插入的账单关联任务标签，保持重复账单不变（FR-001、FR-005）
- [x] T002 [US1] 在 `backend/migrations/versions/` 添加幂等迁移，按用户边界补齐历史账单的任务标签（FR-006、FR-007）
- [x] T003 [US1] 用合成数据验证多标签上传、重复上传和历史补齐（SC-001、SC-004）

## Phase 2: 明细中查看和编辑（US2，P2）

- [x] T004 [US2] 在 `backend/app/bills/service.py` 校验账单标签归属用户（FR-007）
- [x] T005 [US2] 在 `frontend/src/views/BillsDetail.vue` 展示来源、归属人、标签并提供逐笔编辑（FR-002、FR-003）
- [x] T006 [US2] 在 `frontend/src/views/BillUpload.vue` 说明上传标签会附着到新账单（FR-001）
- [x] T007 [US2] 验证编辑后持久化、标签过滤和非法标签拒绝（SC-002、SC-003）

## Phase 3: 文档和收敛

- [x] T008 更新 `docs/api.md` 的当前标签行为，保持 PRD 作为规划文档
- [x] T009 检查 [spec.md](spec.md) 的要求与实现、验证结果；有缺口时追加收敛任务
