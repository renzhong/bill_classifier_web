-- 初始化 MySQL 字符集与时区，schema 由 alembic 管理
SET GLOBAL time_zone = '+08:00';
ALTER DATABASE bill_classifier_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
