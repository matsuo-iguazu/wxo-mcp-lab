# WxO エージェントから PostgreSQL を自然言語で参照する — MCP Toolkit 接続手順

> **対象読者**: IBM watsonx Orchestrate（WxO）を使っていて、エージェントから DB を参照したい方
> **検証環境**: WxO SaaS環境 / Supabase（クラウド PostgreSQL）

---

## はじめに

「WxO エージェントからデータベースを参照したい」というユースケースはよくあります。
WxO には MCP（Model Context Protocol）サーバーを Toolkit として登録する機能があり、
公式の PostgreSQL MCP サーバーを使えば、自然言語 → SQL 変換 → DB 参照が実現できます。

この記事では **Supabase に接続するまでの構成**と、検証中に気づいた **WxO の MCP 実行モデルの特徴**、
そして遭遇した**5つのハマりポイント**を紹介します。

手順の詳細はリポジトリの [track-a/README.md](https://github.com/matsuo-iguazu/wxo-mcp-lab/blob/main/01_postgres-mcp/track-a/README.md) を参照してください。

---

## WxO における MCP サーバーの2つの接続方式

WxO の MCP サーバーには、[公式ドキュメント](https://www.ibm.com/docs/ja/watsonx/watson-orchestrate/base?topic=tools-mcp-servers)で定義された2つの接続方式があります。

```mermaid
flowchart LR
  subgraph p2["リモート MCP サーバー（StreamableHTTP / SSE）"]
    C["WxO Agent"] -->|HTTPS| D["MCP Server\n📍自前でホスト\nRailway 等"]
  end
  subgraph p3["ローカル MCP サーバー（STDIO）— 今回"]
    E["WxO Agent"] -->|"STDIO（WxO内部）"| F["npx mcp-server\n📍WxO クラウド内\nPC不要・公開URL不要"]
  end
  D -->|TCP| PG[("PostgreSQL")]
  F -->|TCP| PG
```

**リモート MCP サーバー**: MCP サーバーを公開 URL でホストし、WxO から HTTPS または SSE で接続します。サーバーの用意・運用が必要です。

**ローカル MCP サーバー（今回）**: WxO が `command:` に書いたプロセスを WxO クラウド内部で起動し、STDIO で通信します。PC も公開サーバーも不要です。

> **注意**: WxO ドキュメントの「ローカル」はユーザーの手元 PC を指しません。WxO クラウド内でコマンドとして起動される MCP サーバーのことです。

---

## 実は MCP サーバーは PC で動いていない

これが今回一番の発見でした。

以前は「MCP サーバーを使うには手元の PC で Node.js を動かす必要がある」と説明してきましたが、
WxO の MCP Toolkit 機能を使えばその必要はありません。

エラー発生時のスタックトレースに `/opt/app-root/lib64/python3.12/` というパスが含まれており、
これが OpenShift コンテナ（WxO クラウドの実行環境）のパスであることで確認できました。

---

## 構成の概要

```
WxO Connection（m-postgres-conn）
  → DATABASE_URL をセキュアストレージで管理。Git に認証情報を入れない。

WxO MCP Toolkit（m-postgres）
  → npx で @modelcontextprotocol/server-postgres を起動
  → 公開ツール: query（SELECT 専用）

WxO エージェント（M_postgres_agent）
  → 自然言語 → SQL を生成して m-postgres:query を呼び出す
```

詳しい設定内容・手順は [track-a/README.md](https://github.com/matsuo-iguazu/wxo-mcp-lab/blob/main/01_postgres-mcp/track-a/README.md) を参照してください。

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

`$DATABASE_URL` を展開するためにシェル経由（`sh -c`）が必要で、この形式が必要になります。

---

### ② `toolkits:` フィールドは `react` スタイルで使えない

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

### ③ エージェント名にハイフンは使えない

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
# ❌ Direct connection（IPv6 の可能性）
postgresql://postgres:pass@db.xxxxx.supabase.co:5432/postgres

# ✅ Session Pooler（IPv4）
postgresql://postgres.xxxxx:pass@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
```

Supabase ダッシュボードの **Connect → Session pooler** から取得します。
ユーザー名が `postgres.{project-ref}` 形式になる点も注意。

---

### ⑤ toolkit インポート前に認証情報の登録が必須

`orchestrate toolkits import` を実行すると、WxO は実際に MCP サーバーを起動してツール一覧を取得しに行きます。
つまり **インポート前に `DATABASE_URL` が登録済みでないと、サーバーが起動できず失敗します**。

必ず Connection の `set-credentials` を先に実行してから `toolkits import` を行ってください。

---

## 考慮点

**`@modelcontextprotocol/server-postgres` について**

- 公式の archived リポジトリのため、今後のメンテナンスは期待できない
- `query` ツール1本（`BEGIN TRANSACTION READ ONLY` でラップ）— SELECT 専用
- 検証・デモ用途には十分だが、本番利用には向かない

**本番利用を検討する場合**

- R/W が必要 → [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp)（Python、アクティブ維持）
- 目的別ツールを設計したい → 独自 FastMCP サーバー（STDIO モードなら PC・公開サーバー不要）

---

## まとめ

| ポイント | 内容 |
|---|---|
| MCP サーバーの実行場所 | WxO クラウド（PC も公開サーバーも不要） |
| Supabase 接続文字列 | Session Pooler URL（IPv4）を使う |
| `command:` の書き方 | JSON リスト形式 |
| ツールの指定方法 | `tools: - toolkit名:tool名` |
| エージェント名 | アンダースコアのみ（ハイフン不可） |
| インポート順序 | credentials 登録 → toolkits import |

サンプルコード一式は [wxo-mcp-lab/01_postgres-mcp/track-a](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/01_postgres-mcp/track-a) にあります。
