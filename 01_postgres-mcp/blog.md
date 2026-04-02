# WxO エージェントから PostgreSQL を自然言語で参照する — MCP Toolkit 接続手順

> **対象読者**: IBM watsonx Orchestrate（WxO）を使っていて、エージェントから DB を参照したい方
> **検証環境**: WxO IG（SaaS）/ Supabase（クラウド PostgreSQL）

---

## はじめに

「WxO エージェントからデータベースを参照したい」というユースケースはよくあります。
WxO には MCP（Model Context Protocol）サーバーを Toolkit として登録する機能があり、
公式の PostgreSQL MCP サーバーを使えば、自然言語 → SQL 変換 → DB 参照 が実現できます。

この記事では **Supabase（クラウド PostgreSQL）に接続するまでの手順**と、
途中で遭遇した**5つのハマりポイント**を記録します。

---

## アーキテクチャ

```
ユーザー発話（自然言語）
  ↓
WxO エージェント（M_postgres_agent）
  ↓  MCP Toolkit 呼び出し（STDIO）
WxO クラウド上で npx が起動
  ↓  @modelcontextprotocol/server-postgres
Supabase PostgreSQL
```

### 実はMCPサーバーはPCで動いていない

これが今回一番の発見でした。

WxO の MCP Toolkit（STDIO モード）は `npx` や `python` コマンドを **WxO クラウド（OpenShift コンテナ）上で実行**します。手元の PC に Node.js 環境は不要です。

エラー発生時のスタックトレースに `/opt/app-root/lib64/python3.12/` というパスが出てきたことで確認できました。これは OpenShift コンテナのパスです。

以前は「MCP サーバーを使うには手元の PC で Node.js を動かす必要がある」と説明してきましたが、WxO の MCP Toolkit 機能を使えばその必要はありません。

---

## 使ったもの

- **IBM watsonx Orchestrate**: IG 環境（SaaS）
- **MCP サーバー**: [`@modelcontextprotocol/server-postgres`](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/postgres)（公式 archived）
- **データベース**: [Supabase](https://supabase.com)（無料プランで十分）
- **WxO ADK CLI**: `orchestrate` コマンド

---

## 手順

### 1. Supabase にサンプルテーブルを作成

Supabase の SQL Editor で以下を実行します（[`scripts/setup_supabase.sql`](track-a/scripts/setup_supabase.sql) に同じ内容があります）。

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
  ('ノートPC',           98000, 'PC',         15),
  ('マウス',              2500, 'peripheral',  50),
  ('モニター 24インチ',  45000, 'display',      8),
  -- ... 全12行は setup_supabase.sql 参照
```

### 2. WxO Connection を定義する

`DATABASE_URL` を WxO のセキュアストレージで管理するために Connection を使います。

```yaml
# connections/m-postgres-conn.yaml
spec_version: v1
kind: connection
app_id: m-postgres-conn
environments:
  draft:
    security_scheme: key_value_creds
    type: team
  live:
    security_scheme: key_value_creds
    type: team
```

Connection YAML 自体には認証情報を書きません。実際の `DATABASE_URL` は後で CLI で登録します。

### 3. MCP Toolkit を定義する

```yaml
# toolkits/m-postgres-toolkit.yaml
spec_version: v1
kind: mcp
name: m-postgres
description: PostgreSQL 読み取り専用クエリツールキット
command: '["sh", "-c", "npx -y @modelcontextprotocol/server-postgres $DATABASE_URL"]'
connections:
  - m-postgres-conn
tools:
  - "*"
```

### 4. エージェントを定義する

```yaml
# agents/M-postgres-agent.yaml
spec_version: v1
kind: native
name: M_postgres_agent
description: PostgreSQL データベースを自然言語で参照するエージェント
instructions: |
  You are a helpful data assistant with read-only access to a PostgreSQL database.
  When the user asks about data, tables, or database contents:
  1. Use the `m-postgres:query` tool to run appropriate SELECT statements.
  2. To list tables, query: SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
  3. Always generate correct SQL based on the user's natural language request.
  4. Present results clearly and concisely in Japanese.
  Constraints:
  - Only SELECT queries are allowed. Never attempt INSERT, UPDATE, DELETE, or DDL.
llm: groq/openai/gpt-oss-120b
style: react
tools:
  - m-postgres:query
```

### 5. インポートする

```bash
# Connection 定義をインポート
orchestrate connections import -f connections/m-postgres-conn.yaml

# DATABASE_URL を登録（draft / live 両環境に）
orchestrate connections configure -a m-postgres-conn --env draft --type team --kind key_value
orchestrate connections set-credentials -a m-postgres-conn --env draft \
  -e "DATABASE_URL=postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

orchestrate connections configure -a m-postgres-conn --env live --type team --kind key_value
orchestrate connections set-credentials -a m-postgres-conn --env live \
  -e "DATABASE_URL=postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

# Toolkit をインポート（ここで実際に npx が起動してツール一覧を取得する）
orchestrate toolkits import -f toolkits/m-postgres-toolkit.yaml

# エージェントをインポート
orchestrate agents import -f agents/M-postgres-agent.yaml
```

`import-all.sh` を使えばワンコマンドで実行できます：

```bash
DATABASE_URL="postgresql://..." ./import-all.sh
```

### 6. テスト

WxO チャットで `M_postgres_agent` を選択して話しかけます：

```
テーブル一覧を見せて
→ public スキーマのテーブル一覧が返ってくる

products テーブルのデータをすべて表示して
→ 12行のデータが表示される

1万円以下の商品を教えて
→ 価格が10000円以下の商品が絞り込まれて返ってくる
```

---

## ハマりポイント 5選

### ① `command:` のスペース分割問題

WxO は `command:` に文字列を書くと、スペースで分割して引数リストを作ります。
そのため `sh -c '...'` のようなシェル経由の起動は文字列では書けません。

```yaml
# ❌ スペース分割されて sh が正しく動かない
command: "sh -c 'npx -y @modelcontextprotocol/server-postgres $DATABASE_URL'"

# ✅ JSON リスト形式で書く
command: '["sh", "-c", "npx -y @modelcontextprotocol/server-postgres $DATABASE_URL"]'
```

`$DATABASE_URL` を展開するためにシェル経由（`sh -c`）が必要なので、この形式が必要になります。

---

### ② `toolkits:` フィールドは `react` スタイルで使えない

エージェント YAML に `toolkits: - m-postgres` と書いたところ、インポートが失敗しました。

```
Toolkits are only supported for experimental_customer_care style agents
```

`react` スタイル（と `default` スタイル）では `toolkits:` は使えません。
`tools:` フィールドに `toolkit名:tool名` 形式で指定します。

```yaml
# ❌ react スタイルでは動かない
toolkits:
  - m-postgres

# ✅ tools に toolkit名:tool名 形式で指定
tools:
  - m-postgres:query
```

ツール名は `orchestrate tools list` で確認できます。

---

### ③ エージェント名にハイフンは使えない

`M-postgres-agent` という名前でインポートしようとしたところ：

```
Name must start with a letter and contain only alphanumeric characters and underscores
```

エージェント名は英数字とアンダースコアのみ。`M_postgres_agent` に変更して解決。

Toolkit 名や Connection 名はハイフン OK なので混乱しやすいポイントです。

---

### ④ Supabase は Session Pooler URL を使う

Supabase のデフォルト接続文字列（Direct connection）は IPv6 アドレスに解決されることがあります。
WxO クラウドから IPv6 には到達できず `ENETUNREACH` エラーになりました。

```
# ❌ Direct connection（IPv6）
postgresql://postgres:pass@db.xxxxx.supabase.co:5432/postgres

# ✅ Session Pooler（IPv4）
postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
```

Supabase ダッシュボードの **Connect → Session pooler** から取得します。
ユーザー名が `postgres.{project-ref}` 形式になる点も注意。

---

### ⑤ toolkit インポート前に認証情報の登録が必須

`orchestrate toolkits import` を実行すると、WxO は実際に MCP サーバーを起動してツール一覧を取得しに行きます。
つまり、**インポート時点で `DATABASE_URL` が登録済みでないとサーバーが起動できず失敗します**。

必ず以下の順序で実行してください：

1. `connections import`（接続定義）
2. `connections configure` + `set-credentials`（認証情報を登録）
3. `toolkits import`（ここで初めてサーバーが起動する）
4. `agents import`

---

## 補足: archived サーバーについて

`@modelcontextprotocol/server-postgres` は公式の archived リポジトリのため、今後のメンテナンスは期待できません。
また `query` ツール1本のみ（`BEGIN TRANSACTION READ ONLY` でラップされた SELECT 専用）なので、機能は限定的です。

**本番利用や R/W が必要な場合**は [`crystaldba/postgres-mcp`](https://github.com/crystaldba/postgres-mcp) やカスタム FastMCP サーバーへの移行を推奨します。

---

## まとめ

| ポイント | 内容 |
|---|---|
| MCP サーバーの実行場所 | WxO クラウド（PC 不要） |
| Supabase 接続文字列 | Session Pooler URL（IPv4）を使う |
| `command:` の書き方 | JSON リスト形式 |
| ツールの指定方法 | `tools: - toolkit名:tool名` |
| エージェント名 | アンダースコアのみ（ハイフン不可） |
| インポート順序 | credentials 登録 → toolkits import |

サンプルコード一式は [wxo-mcp-lab/01_postgres-mcp/track-a](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/01_postgres-mcp/track-a) にあります。
