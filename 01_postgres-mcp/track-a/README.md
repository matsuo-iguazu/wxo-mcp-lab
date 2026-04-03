# Track A — @modelcontextprotocol/server-postgres (npx / STDIO)

公式 archived MCP サーバーを使って wxO エージェントから PostgreSQL を参照します。

---

## 前提条件

- IBM watsonx Orchestrate（SaaS）
- `orchestrate` CLI（[ADK](https://github.com/IBM/ibm-watsonx-orchestrate-adk) に同梱）
- `orchestrate env activate <env>` で環境をアクティブにしておくこと（初回は `-a <api-key>` で API キーを登録）
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

### 1. Supabase にサンプルテーブルを作成

Supabase ダッシュボードの **SQL Editor** で `scripts/setup_supabase.sql` を実行します。

### 2. Supabase の接続文字列を取得

Supabase ダッシュボード → **Connect** → **Session pooler** タブから接続文字列を取得します。

```
postgresql://postgres.{project-ref}:{password}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
```

> **注意**: Direct connection（IPv6）は wxO クラウドから到達できないことがあります。必ず **Session pooler**（IPv4）を使ってください。

以降の手順でこの文字列を `DATABASE_URL` として使用します。

### 3. Connection をインポート（YAML）

```bash
orchestrate connections import -f connections/m-postgres-conn.yaml
```

### 4. 認証情報を登録（CLI）

draft / live の両環境に `DATABASE_URL` を登録します。

```bash
orchestrate connections configure -a m-postgres-conn --env draft --type team --kind key_value
orchestrate connections set-credentials -a m-postgres-conn --env draft \
  -e "DATABASE_URL=postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

orchestrate connections configure -a m-postgres-conn --env live --type team --kind key_value
orchestrate connections set-credentials -a m-postgres-conn --env live \
  -e "DATABASE_URL=postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
```

> **注意**: この手順を先に完了させてから次へ進んでください。Toolkit インポート時に wxO が MCP サーバーを起動してツール一覧を取得するため、認証情報が登録済みでないと失敗します。

### 5. Toolkit をインポート（YAML）

```bash
orchestrate toolkits import -f toolkits/m-postgres-toolkit.yaml
```

### 6. エージェントをインポート（YAML）

```bash
orchestrate agents import -f agents/M-postgres-agent.yaml
```

### 7. テスト

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

## 一括実行（import-all.sh）

手順 3〜6 は `import-all.sh` でまとめて実行することもできます。

```bash
chmod +x import-all.sh
DATABASE_URL="postgresql://..." ./import-all.sh
```

> ファイル内のリソース名（`m-postgres-conn` 等）は固定です。変更する場合は YAML ファイルとスクリプトを合わせて編集してください。

---

## ローカル PostgreSQL（Docker）への切り替え

`DATABASE_URL` を変えるだけで動作します：

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
