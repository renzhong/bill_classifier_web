# 账单标签合同

- `POST /api/v1/bills/upload`：继续接受 `tag_ids`，每笔新账单继承全部有效标签；重复账单保持原标签。
- `GET /api/v1/bills`、`GET /api/v1/bills/{id}`：返回 `source`、`owner`、`tag_ids`。
- `PATCH /api/v1/bills/{id}`：`tag_ids` 表示完整标签集合；只接受当前用户的标签。只改标签不设置 `manual_overridden`。
- `GET /api/v1/bills?tag_id=...`：按当前关联过滤。
