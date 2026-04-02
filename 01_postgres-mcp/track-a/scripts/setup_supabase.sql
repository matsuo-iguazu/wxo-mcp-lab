-- =============================================================================
-- setup_supabase.sql  —  検証用サンプルデータ
-- Supabase SQL Editor で実行する
-- =============================================================================

DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    price    INTEGER      NOT NULL,
    category VARCHAR(50),
    stock    INTEGER DEFAULT 0
);

INSERT INTO products (name, price, category, stock) VALUES
  ('ノートPC',              98000,  'PC',          15),
  ('デスクトップPC',        120000,  'PC',           5),
  ('マウス',                  2500,  'peripheral',  50),
  ('ワイヤレスマウス',         4800,  'peripheral',  30),
  ('モニター 24インチ',       45000,  'display',      8),
  ('モニター 27インチ',       68000,  'display',      3),
  ('メカニカルキーボード',    12000,  'peripheral',  20),
  ('メンブレンキーボード',     4500,  'peripheral',  40),
  ('USB ハブ 4ポート',         3200,  'accessory',   25),
  ('USB ハブ 7ポート',         5800,  'accessory',   12),
  ('ウェブカメラ HD',          8900,  'accessory',    6),
  ('ヘッドセット',            15000,  'audio',       18);

-- 確認
SELECT * FROM products ORDER BY category, price;
