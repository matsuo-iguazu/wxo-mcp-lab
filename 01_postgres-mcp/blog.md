# wxO エージェントから PostgreSQL を自然言語で参照する — MCP Toolkit を使った接続

> **対象読者**: IBM watsonx Orchestrate（wxO）を使っていて、エージェントから DB を参照したい方
> **検証環境**: wxO SaaS 環境 / Supabase（クラウド PostgreSQL）

---

## はじめに

wxO エージェントからデータベースを自然言語で参照したい、というユースケースがあります。
wxO には MCP（Model Context Protocol）サーバーを Toolkit として登録する機能があり、
これを使えば自然言語 → SQL 変換 → DB 参照が実現できます。

今回は GitHub の [modelcontextprotocol/servers-archived](https://github.com/modelcontextprotocol/servers-archived) にある
PostgreSQL 向け MCP サーバー `@modelcontextprotocol/server-postgres` を試してみました。

サンプルコードは [wxo-mcp-lab/01_postgres-mcp/track-a](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/01_postgres-mcp/track-a) にあります。

---

## wxO の MCP 接続方式：ローカルとリモート

wxO の MCP サーバーには、[公式ドキュメント](https://www.ibm.com/docs/ja/watsonx/watson-orchestrate/base?topic=tools-mcp-servers)で定義された2つの接続方式があります。

![MCP接続方式の比較](2種類の実装.png)

| | ローカル MCP サーバー | リモート MCP サーバー |
|---|---|---|
| 通信方式 | STDIO | StreamableHTTP / SSE |
| 実行場所 | wxO クラウド内 | 自前でホスト |
| PC・公開 URL | 不要 | 必要 |

今回は**ローカル MCP サーバー**（STDIO）方式を使いました。

---

## 発見：MCP サーバーは PC で動いていない

Toolkit YAML の `command:` に `npx -y @modelcontextprotocol/server-postgres` と書くだけで、
wxO がクラウド内部でそのプロセスを起動し、STDIO で通信してくれます。

手元の PC に Node.js 環境は不要です。
エラー発生時のスタックトレースに `/opt/app-root/lib64/python3.12/` というパスが含まれており、
wxO クラウド（OpenShift コンテナ）上で動作していることが確認できました。

---

## `@modelcontextprotocol/server-postgres` の考慮点

- 公式の **archived** リポジトリのため、今後のメンテナンスは期待できない
- ツールは `query` 1本のみ（`BEGIN TRANSACTION READ ONLY` でラップ）— **SELECT 専用**
- 検証・デモ用途には十分だが、本番利用には向かない

R/W が必要な場合や、目的別のツールを設計したい場合は独自 FastMCP サーバーの実装も検討しています（Track B として続報予定）。

---

## 詳細手順

セットアップの詳細は [track-a/README.md](https://github.com/matsuo-iguazu/wxo-mcp-lab/blob/main/01_postgres-mcp/track-a/README.md) を参照してください。
