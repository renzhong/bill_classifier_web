# PRD 04 · 类别 / Tag / 字典

## 用户故事
- 创建自己的业务分类（如 餐饮 / 交通 / 育儿），可改名、改颜色、删除、排序
- 维护一份/多份"关键词字典"，每个字典是 `key → category` 列表；支持 CSV 粘贴批量导入
- 维护 tag 标签，用于上传账单时附加额外标记（如归属人、用途）

## 页面
- `/settings/categories`：表格 CRUD + 拖拽排序
- `/settings/tags`：表格 CRUD
- `/settings/dicts`：左侧字典列表，右侧 entries 表格 + "粘贴 CSV"按钮

## API
- `GET/POST/PATCH/DELETE /api/v1/categories[/:id]`
- `GET/POST/DELETE /api/v1/tags[/:id]`
- `GET/POST/PATCH/DELETE /api/v1/dicts[/:id]`
- `POST /api/v1/dicts/:id/entries/bulk` body `{csv_text: "key,category_name\n..."}`

## 数据模型
- `categories(id, user_id, name UNIQUE per user, display_name, color, sort_order, ts)`
- `tags(id, user_id, name UNIQUE per user, color, ts)`
- `user_dicts(id, user_id, name UNIQUE per user, target_field {payee/item_name/any}, remark, ts)`
- `user_dict_entries(id, dict_id CASCADE, key_text, category_id)`

## 验收
- 删除类别时，若被字典 entry 或账单引用 → 提示并阻止
- CSV 粘贴中找不到 category_name → 整行报错并 rollback
- 同 user 下字典名/类别名/tag 名唯一

## 不做
- 类别层级（暂时单层）
- tag 自动建议
