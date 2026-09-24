# 数据模型

- `upload_tasks.tag_ids`：上传时选中的标签 ID 快照，验证归当前用户所有。
- `bills.upload_task_id`：关联创建它的上传任务；`owner` 保留归属文本。
- `bill_tags(bill_id, tag_id)`：最终逐笔标签，复合主键保证不重复；两端属于同一用户。

仅成功入库的新账单继承任务标签；重复行不改。历史补齐只增加缺少的关联。
