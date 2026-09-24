# PRD 05 · AI Provider 与策略

## 用户故事
- 配置 OpenAI / Qwen / Claude / Gemini / GLM / Kimi 任意 provider 的 api_key + model_name + base_url
- 创建多条"策略文本"，每条是一段自然语言指引（如"看到'高德'类的归到交通"）
- 在 Pipeline 中加入 `ai_classify` 步骤时绑定某条策略；由步骤的启用状态决定是否运行
- 调试时给一条样例输入，看 AI 返回什么类别

## 页面
- `/settings/ai/credentials`：provider/model_name/api_key/base_url/enabled
- `/settings/ai/strategies`：name + 多行 strategy_text + 绑定 credential
  - 右侧 "最终 prompt 预览"区域，展示 template + 已填策略文本拼接后的 prompt

## API
- `GET/POST/PATCH/DELETE /api/v1/ai/credentials[/:id]`
- `GET/POST/PATCH/DELETE /api/v1/ai/strategies[/:id]`
- `GET /api/v1/ai/providers` → `[{name, label, default_base_url, suggested_models}]`
- `POST /api/v1/ai/test` body `{credential_id, strategy_id, sample: {payee, item_name}}` → `{category, confidence, raw}`

## 数据模型
- `ai_credentials(id, user_id, provider, model_name, api_key_encrypted, base_url, enabled, ts)` — Fernet 加密
- `ai_strategies(id, user_id, name, strategy_text, credential_id, ts)`；现有 `active` 字段暂保留在数据库，但不参与分类判断

## 验收
- api_key 写入后从 DB 取出已加密；解密失败抛错而不裸露
- `POST /ai/test` 能复用 ai_classify 的实际调用路径
- Pipeline 中 `ai_classify` 步骤未绑定有效策略或凭据时给出明确错误
- OpenAI 兼容族（openai/qwen/glm/kimi）共用 adapter，仅 base_url + model 不同

## 不做
- 多模型负载均衡
- AI 结果缓存（先观察实际频率）
