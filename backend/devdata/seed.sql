-- Data only: apply migrations first. Use an empty development database.
-- Synthetic account: demo@example.com / Demo-only-123456
-- Tests may set @fixture_user_id to attach metadata to their isolated user.
START TRANSACTION;
INSERT INTO users (email, password_hash, nickname, status, is_admin)
SELECT 'demo@example.com',
        '$argon2id$v=19$m=65536,t=3,p=4$ZUTrS6qvaPIGxd0v6pve5A$UOBJCcCjDlAZqnmpvxBvCMpyW4VjAuS2Yt7Gv/1yjcU',
        '合成数据测试账号', 'active', 0
WHERE @fixture_user_id IS NULL;
SET @fixture_user_id = COALESCE(@fixture_user_id, LAST_INSERT_ID());

INSERT INTO categories (user_id, name, display_name, color, sort_order)
VALUES (@fixture_user_id, '餐饮', '餐饮', '#e67e22', 1),
       (@fixture_user_id, '交通', '交通', '#3498db', 2),
       (@fixture_user_id, '购物', '购物', '#9b59b6', 3);

INSERT INTO ai_strategies (user_id, name, strategy_text, active)
VALUES (@fixture_user_id, '固定样本分类规则', CONCAT(
    '餐厅、早餐、咖啡归为餐饮。', CHAR(10),
    '地铁、公交归为交通。', CHAR(10),
    '文具、日用品归为购物。', CHAR(10),
    '无法判断或收入转账返回 UNKNOWN。'), 1);
SET @fixture_strategy_id = LAST_INSERT_ID();

-- Bind a real credential in the UI before enabling this step.
INSERT INTO pipeline_steps (user_id, strategy_type, display_name, params, sort_order, enabled)
VALUES (@fixture_user_id, 'ai_classify', '固定样本 AI 分类',
        JSON_OBJECT('strategy_id', @fixture_strategy_id, 'only_unclassified', TRUE, 'max_concurrency', 4),
        1, 0);
SET @fixture_step_id = LAST_INSERT_ID();
COMMIT;
