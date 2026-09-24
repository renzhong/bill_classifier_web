# 决策记录

## 归属表达

**Decision**: 保留 `owner` 和平台 `source`，用多标签作为可编辑归属标记。
**Rationale**: 旧项目 `zrz/cwx` 作为每笔账单的 `owner`；新项目已有同类字段和标签关联表。
**Alternatives considered**: 文件名不适合长期归属筛选；单个自由文本不方便扩展。

## 重复与历史账单

**Decision**: 重复上传保留原标签；用幂等迁移补齐历史任务标签而不删除已有标签。
**Rationale**: 避免覆盖用户手工修正，同时补齐已有上传记录。
