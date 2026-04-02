# 01_postgres-mcp — PostgreSQL MCP Toolkit for WxO

WxO エージェントから PostgreSQL データベースを **自然言語で参照**する実験です。
MCP（Model Context Protocol）サーバーを WxO の MCP Toolkit として登録し、
エージェントが自動的に SQL を生成して結果を返します。

---

## アーキテクチャ

```
ユーザー発話（自然言語）
  ↓
WxO エージェント（M_postgres_agent）
  ↓  MCP Toolkit 呼び出し（STDIO）
WxO クラウド上で npx が起動
  ↓  @modelcontextprotocol/server-postgres
PostgreSQL（Supabase / ローカル Docker）
```

> **ポイント**: MCP サーバーは WxO クラウド上で動くため、手元の PC に Node.js 環境は不要です。

---

## トラック構成

| トラック | 方式 | MCP サーバー | ツール数 |
|---|---|---|---|
| [track-a/](track-a/) | STDIO（npx） | 公式 archived `@modelcontextprotocol/server-postgres` | 1（`query`） |
| track-b/ | STDIO（Python） | 独自 FastMCP サーバー | 4（`list_tables` / `describe_table` / `query` / `count_rows`） |

> **track-b** は準備中です。

---

## Track A クイックスタート

### 1. Supabase にサンプルデータを作成

[Supabase](https://supabase.com) の SQL Editor で `track-a/scripts/setup_supabase.sql` を実行します。

### 2. 接続文字列を取得

Supabase ダッシュボード → **Connect** → **Session pooler** から接続文字列を取得します。

```
postgresql://postgres.{project-ref}:{password}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
```

> **注意**: Direct connection（IPv6）は WxO クラウドから到達できない場合があります。**Session pooler（IPv4）**を使ってください。

### 3. インポート

```bash
cd track-a
chmod +x import-all.sh
DATABASE_URL="postgresql://..." ./import-all.sh
```

`import-all.sh` は以下の順序で実行します：

1. Connection 定義をインポート
2. `DATABASE_URL` を draft / live 両環境に登録
3. MCP Toolkit をインポート
4. エージェントをインポート

### 4. WxO チャットでテスト

```
テーブル一覧を見せて
products テーブルのデータをすべて表示して
1万円以下の商品を教えて
```

---

## ファイル構成（Track A）

```
track-a/
├── connections/
│   └── m-postgres-conn.yaml     # WxO Connection 定義（DATABASE_URL を env var で管理）
├── toolkits/
│   └── m-postgres-toolkit.yaml  # MCP Toolkit（npx で archived server を起動）
├── agents/
│   └── M-postgres-agent.yaml    # エージェント定義
├── scripts/
│   └── setup_supabase.sql       # サンプルテーブル + データ（products 12行）
└── import-all.sh                # 一括インポートスクリプト
```

---

## ローカル PostgreSQL（Docker）への切り替え

接続文字列を変えるだけで動作します：

```bash
docker run -d --name pg-test \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=testdb \
  -p 5432:5432 postgres:16

DATABASE_URL="postgresql://postgres:testpass@host.docker.internal:5432/testdb" ./import-all.sh
```

---

## 注意事項

- `@modelcontextprotocol/server-postgres` は archived リポジトリのため、セキュリティアップデートは期待できません。本番利用には [`crystaldba/postgres-mcp`](https://github.com/crystaldba/postgres-mcp) 等の検討を推奨します。
- `query` ツールは `BEGIN TRANSACTION READ ONLY` でラップされるため、SELECT のみ実行可能です。
