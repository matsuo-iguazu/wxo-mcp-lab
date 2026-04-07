# 01_postgres-mcp — PostgreSQL MCP Toolkit for wxO

watsonx Orchestrate (wxO) エージェントから PostgreSQL データベースを **自然言語で参照**する実験です。
MCP（Model Context Protocol）サーバーを wxO の MCP Toolkit として登録し、
エージェントが自動的に SQL を生成して結果を返します。

---

## トラック構成

| トラック | MCP サーバー | デプロイ方式 | 操作 | ツール数 |
|---|---|---|---|---|
| [track-a/](track-a/) | 公式 `@modelcontextprotocol/server-postgres`（npm） | `command:` で npx 実行 | SELECT のみ | 1（`query`） |
| [track-b/](track-b/) | 独自 FastMCP サーバー（Python） | `package_root:` でファイルアップロード | CRUD | 4（`list_products` / `add_product` / `update_product_price` / `delete_product`） |

## Track A vs Track B

| | Track A | Track B |
|---|---|---|
| MCP サーバー | `@modelcontextprotocol/server-postgres`（npm 公式） | `server.py`（FastMCP で自作） |
| デプロイ方式 | `command:` で npx 実行 | `package_root:` でローカルファイルをアップロード |
| 操作 | SELECT のみ | SELECT / INSERT / UPDATE / DELETE |
| ツール数 | 1本（query） | 4本 |

---

詳しい手順は各トラックの README を参照してください。
