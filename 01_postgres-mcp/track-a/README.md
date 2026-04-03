# Track A — 公式 MCP サーバー @modelcontextprotocol/server-postgres を使った PostgreSQL 接続

公式 archived MCP サーバーを使って wxO エージェントから PostgreSQL を参照します。

---

## 前提条件

- IBM watsonx Orchestrate（SaaS）
- `orchestrate` CLI（[ADK](https://github.com/IBM/ibm-watsonx-orchestrate-adk) に同梱）
- `orchestrate env activate <env>` で環境をアクティブにしておくこと（初回は `-a <api-key>` で API キーを登録）
- Supabase アカウント（無料プランで可）

---

## セットアップ

### リポジトリを取得

```bash
git clone https://github.com/matsuo-iguazu/wxo-mcp-lab.git
cd wxo-mcp-lab/01_postgres-mcp/track-a
```

### サンプルのリソース名について

このリポジトリのファイルは以下の名称を前提に作成されています。
ご利用の環境やチームの命名規則に合わせて、YAML ファイルおよびスクリプトを適宜変更してください。

| リソース | サンプル名 |
|---|---|
| Connection | `m-postgres-conn` |
| Toolkit | `m-postgres` |
| エージェント | `M_postgres_agent` |

---

## 手順

### 1. Supabase にサンプルテーブルを作成

対象プロジェクトのダッシュボードの **SQL Editor** を開き、`scripts/setup_supabase.sql` の内容を貼り付けて **Run** します。

### 2. Supabase の接続文字列を取得

対象プロジェクトのページ → **Connect** → **Direct** → **Session pooler** を選択し、**Connection string** を取得します。

```
postgresql://postgres.xxxxxxxxxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
```

取得した文字列は手順 4 の `DATABASE_URL` として使用します。

### 3. Connection をインポート（YAML）

`connections/m-postgres-conn.yaml` を適宜編集してから実行します。

```bash
orchestrate connections import -f connections/m-postgres-conn.yaml
```

### 4. 認証情報を登録（CLI）

手順 2 で取得した接続文字列を、キー `DATABASE_URL` の値として登録します。接続文字列内の `[YOUR-PASSWORD]` は Supabase プロジェクトのパスワードに置き換えてください。draft / live の両環境に登録します。

> **パスワードに特殊文字が含まれる場合**: シェルがパスワードを解釈してエラーになることがあります。英数字のみのパスワードに変更することを推奨します（対象プロジェクト → **Database** → **Settings** → **Database password**）。

```bash
orchestrate connections configure -a m-postgres-conn --env draft --type team --kind key_value
orchestrate connections set-credentials -a m-postgres-conn --env draft \
  -e "DATABASE_URL=postgresql://postgres.xxxxxxxxxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

orchestrate connections configure -a m-postgres-conn --env live --type team --kind key_value
orchestrate connections set-credentials -a m-postgres-conn --env live \
  -e "DATABASE_URL=postgresql://postgres.xxxxxxxxxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
```

### 5. Toolkit をインポート（YAML）

`toolkits/m-postgres-toolkit.yaml` を適宜編集してから実行します。

```bash
orchestrate toolkits import -f toolkits/m-postgres-toolkit.yaml
```

### 6. エージェントをインポート（YAML）

`agents/M-postgres-agent.yaml` を適宜編集してから実行します。

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
DATABASE_URL="postgresql://..." ./import-all.sh
```

> ファイル内のリソース名（`m-postgres-conn` 等）は固定です。変更する場合は YAML ファイルとスクリプトを合わせて編集してください。

---

## 参考: ローカル PostgreSQL（Docker）への切り替え

`DATABASE_URL` を変えるだけで動作します：

```bash
docker run -d --name pg-test \
  -e POSTGRES_PASSWORD=testpass \
  -p 5432:5432 postgres:16

DATABASE_URL="postgresql://postgres:testpass@host.docker.internal:5432/postgres" \
  ./import-all.sh
```

---

## `@modelcontextprotocol/server-postgres` についての注意

- 公式の archived リポジトリのため、セキュリティアップデートは期待できません
- `query` ツール1本のみ（`BEGIN TRANSACTION READ ONLY` でラップ）— SELECT 専用
- 本番利用や R/W が必要な場合は [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp) や独自 FastMCP を検討してください

---

## 検証メモ

### `command:` のスペース分割問題

wxO は `command:` に文字列を書くと、スペースで分割して引数リストを作ります。
そのため `sh -c '...'` のようなシェル経由の起動は文字列では書けません。

```yaml
# ❌ スペース分割されて sh が正しく動かない
command: "sh -c 'npx -y @modelcontextprotocol/server-postgres $DATABASE_URL'"

# ✅ JSON リスト形式で書く
command: '["sh", "-c", "npx -y @modelcontextprotocol/server-postgres $DATABASE_URL"]'
```

`$DATABASE_URL` を展開するためにシェル経由（`sh -c`）が必要で、この形式が必要になります。

---

### `toolkits:` フィールドは `react` スタイルで使えない

エージェント YAML に `toolkits: - m-postgres` と書いたところ、インポートが失敗しました。

```
Toolkits are only supported for experimental_customer_care style agents
```

`react` スタイルでは `toolkits:` は使えず、`tools:` に `toolkit名:tool名` 形式で指定します。

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

### Supabase は Session Pooler URL を使う

Supabase のデフォルト接続文字列（Direct connection）は IPv6 アドレスに解決されることがあります。
wxO クラウドから IPv6 には到達できず `ENETUNREACH` エラーになりました。

```
# ❌ Direct connection（IPv6 の可能性）
postgresql://postgres:pass@db.xxxxx.supabase.co:5432/postgres

# ✅ Session Pooler（IPv4）
postgresql://postgres.xxxxx:pass@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
```

対象プロジェクトのページ → **Connect** → **Session pooler** から取得します。
ユーザー名が `postgres.{project-ref}` 形式になる点も注意。

---

### toolkit インポート前に認証情報の登録が必須

`orchestrate toolkits import` を実行すると、wxO は実際に MCP サーバーを起動してツール一覧を取得しに行きます。
つまり **インポート前に `DATABASE_URL` が登録済みでないと、サーバーが起動できず失敗します**。

必ず Connection の `set-credentials` を先に実行してから `toolkits import` を行ってください。
