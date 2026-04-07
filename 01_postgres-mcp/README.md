# 01_postgres-mcp — PostgreSQL MCP Toolkit for watsonx Orchestrate

watsonx Orchestrate (wxO) エージェントから PostgreSQL データベースを **自然言語で参照**する実験です。
MCP（Model Context Protocol）サーバーを wxO の MCP Toolkit として登録し、
エージェントが自動的に SQL を生成して結果を返します。

---

## トラック構成

| トラック | タイトル | 概要 |
|---|---|---|
| [Track A](track-a/) | 公式 MCP サーバー `@modelcontextprotocol/server-postgres` を使った PostgreSQL 接続 | npm 公式パッケージで SELECT 専用の PostgreSQL アクセスを実現 |
| [Track B](track-b/) | Python 公式 MCP フレームワーク FastMCP で PostgreSQL R/W サーバーを自作する | Python で MCP サーバーを自作し CRUD 操作を wxO エージェントから呼び出す |

## Track A vs Track B

| | Track A | Track B |
|---|---|---|
| MCP サーバー | `@modelcontextprotocol/server-postgres`（npm 公式） | `server.py`（Python 公式 MCP フレームワーク FastMCP で自作） |
| デプロイ方式 | `command:` で npx 実行 | `package_root:` でローカルファイルをアップロード |
| 操作 | SELECT のみ | SELECT / INSERT / UPDATE / DELETE |
| ツール数 | 1本（query） | 4本 |

---

詳しい手順は各トラックの README を参照してください。
