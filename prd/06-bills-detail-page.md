# PRD 06 · 账单明细页

## 用户故事
- 按月/分类/source/tag/关键词过滤账单
- 列表展示金额/payee/item_name/类别/命中策略类型/tag/操作列
- 手工改类别、改 tag；单条重分类；批量改类/删除

## 页面
- `/bills/detail`：
  - 顶部过滤区：month picker、category 多选、source 多选、tag 多选、关键词输入
  - 表格用 Naive UI `n-data-table-v2` 虚拟滚动
  - 列：金额 / 类别 / payee / item_name / 时间 / source / owner / 命中策略 / 标签 / 操作
  - 选中多条 → 批量操作菜单

## API
- `GET /api/v1/bills?month=&category_id=&source=&tag_id=&keyword=&page=&page_size=`
- `GET /api/v1/bills/:id`
- `PATCH /api/v1/bills/:id` body `{category_id?, tag_ids?}`
- `POST /api/v1/bills/:id/reclassify`
- `POST /api/v1/bills/batch` body `{ids:[], action: 'set_category'|'add_tag'|'delete', payload}`

## 验收
- 手动改类 → `manual_overridden=1`，后续 Pipeline 重跑保留
- 单条重分类 → 重走 user 的 Pipeline，结果更新
- 列表分页 + 排序（默认 bill_time desc）
- 选中后批量改类成功；批量删除有二次确认

## 不做
- 导出 CSV（后续 milestone）
- 富文本备注（先不加）
