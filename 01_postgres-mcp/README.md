# 01_postgres-mcp — PostgreSQL MCP Toolkit for watsonx Orchestrate (wxO)

wxO エージェントから PostgreSQL データベースを **自然言語で参照**する実験です。
MCP（Model Context Protocol）サーバーを wxO の MCP Toolkit として登録し、
エージェントが自動的に SQL を生成して結果を返します。

---

## アーキテクチャ

```
ユーザー発話（自然言語）
  ↓
wxO エージェント（M_postgres_agent）
  ↓  ローカル MCP Toolkit（STDIO）
wxO クラウド上で npx が起動
  ↓  @modelcontextprotocol/server-postgres
PostgreSQL（Supabase 等）
```

> **ポイント**: MCP サーバーは wxO クラウド上で動くため、手元の PC に Node.js 環境は不要です。

---

## トラック構成

| トラック | 方式 | MCP サーバー | ツール数 |
|---|---|---|---|
| [track-a/](track-a/) | ローカル STDIO（npx） | 公式 archived `@modelcontextprotocol/server-postgres` | 1（`query`） |
| track-b/ | ローカル STDIO（Python） | 独自 FastMCP サーバー | 4（`list_tables` / `describe_table` / `query` / `count_rows`） |

> **track-b** は近日公開予定です。

---

詳しい手順は各トラックの README を参照してください。
