# Track A — @modelcontextprotocol/server-postgres (npx / STDIO)

公式 archived MCP サーバーを使って wxO エージェントから PostgreSQL を参照します。

---

## 前提条件

- IBM watsonx Orchestrate（SaaS または Developer Edition）
- `orchestrate` CLI（[ADK](https://github.com/IBM/ibm-watsonx-orchestrate-adk) に同梱）
- `orchestrate env activate <env>` で環境をアクティブにしておくこと
- Supabase アカウント（無料プランで可）

---

## ファイル構成

```
track-a/
├── connections/
│   └── m-postgres-conn.yaml     # wxO Connection 定義
├── toolkits/
│   └── m-postgres-toolkit.yaml  # MCP Toolkit 定義
├── agents/
│   └── M-postgres-agent.yaml    # エージェント定義
├── scripts/
│   └── setup_supabase.sql       # サンプルテーブル + データ
└── import-all.sh                # 一括インポートスクリプト
```

---

## 手順

### 1. Supabase にサンプルテーブルを作成（scripts/setup_supabase.sql）

Supabase ダッシュボードの **SQL Editor** で `scripts/setup_supabase.sql` を実行します。

```sql
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    price    INTEGER      NOT NULL,
    category VARCHAR(50),
    stock    INTEGER DEFAULT 0
);

INSERT INTO products (name, price, category, stock) VALUES
  ('ノートPC',              98000, 'PC',         15),
  ('デスクトップPC',        120000, 'PC',          5),
  ('マウス',                  2500, 'peripheral',  50),
  ('ワイヤレスマウス',        4800, 'peripheral',  30),
  ('モニター 24インチ',      45000, 'display',      8),
  ('モニター 27インチ',      68000, 'display',      3),
  ('メカニカルキーボード',   12000, 'peripheral',  20),
  ('メンブレンキーボード',    4500, 'peripheral',  40),
  ('USB ハブ 4ポート',        3200, 'accessory',   25),
  ('USB ハブ 7ポート',        5800, 'accessory',   12),
  ('ウェブカメラ HD',         8900, 'accessory',    6),
  ('ヘッドセット',           15000, 'audio',       18);
```

### 2. Supabase の接続文字列を取得

Supabase ダッシュボード → **Connect** → **Session pooler** タブから接続文字列を取得します。

```
postgresql://postgres.{project-ref}:{password}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
```

> **注意**: Direct connection（IPv6）は wxO クラウドから到達できないことがあります。必ず **Session pooler**（IPv4）を使ってください。

### 3. インポート（import-all.sh）

```bash
cd track-a
chmod +x import-all.sh
DATABASE_URL="postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres" \
  ./import-all.sh
```

スクリプトは以下の順序で実行します：

| ステップ | コマンド | 説明 |
|---|---|---|
| 1 | `connections import` | Connection 定義をインポート |
| 2 | `connections configure` + `set-credentials` | DATABASE_URL を draft/live に登録 |
| 3 | `toolkits import` | MCP サーバーを起動してツール一覧を取得 |
| 4 | `agents import` | エージェントをインポート |

> **注意**: ステップ 2 の前に `toolkits import` を実行すると失敗します。wxO はインポート時に実際に MCP サーバーを起動してツールを列挙するため、認証情報が先に必要です。

### 4. テスト

wxO チャットで `M_postgres_agent` を選択して話しかけます：

```
テーブル一覧を見せて
→ products テーブルが表示される

products テーブルのデータをすべて表示して
→ 12行のデータが返ってくる

1万円以下の商品を教えて
→ price <= 10000 の商品が絞り込まれて返ってくる
```

---

## ローカル PostgreSQL（Docker）への切り替え

接続文字列を変えるだけで動作します：

```bash
docker run -d --name pg-test \
  -e POSTGRES_PASSWORD=testpass \
  -p 5432:5432 postgres:16

DATABASE_URL="postgresql://postgres:testpass@host.docker.internal:5432/postgres" \
  ./import-all.sh
```

---

## 注意事項

- `@modelcontextprotocol/server-postgres` は archived のため、セキュリティアップデートは期待できません
- `query` ツール1本のみ（`BEGIN TRANSACTION READ ONLY` でラップ）— SELECT 専用
- 本番利用や R/W が必要な場合は [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp) や独自 FastMCP を検討してください
