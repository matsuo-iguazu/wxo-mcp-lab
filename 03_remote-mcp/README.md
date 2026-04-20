# 03_remote-mcp — リモート MCP サーバーへの接続

watsonx Orchestrate (wxO) エージェントから **インターネット上の公開 MCP サーバーに接続する**実験です。

ローカル MCP（`01_postgres-mcp` / `02_google-services-mcp`）との最大の違いは、
MCP サーバーを自前で用意・起動しなくていい点です。
URL を指定するだけで接続できます。

---

## ローカル MCP vs リモート MCP

| | ローカル MCP（`command:`） | **リモート MCP（`server_url:`）** |
|---|---|---|
| サーバーの用意 | 必要（npm パッケージ / Python ファイル） | **不要**（誰かが公開しているサーバーを使う） |
| 起動場所 | wxO クラウド上で npx / python を実行 | インターネット上のサーバーに HTTP で接続 |
| 通信方式 | STDIO（標準入出力） | **Streamable HTTP** または **SSE** |
| YAML の違い | `command:` を使う | `transport:` + `server_url:` を使う |
| 認証 | `connections:` で環境変数を注入 | サーバー次第（公開サーバーは不要なことも） |

---

## トラック構成

| トラック | タイトル | 接続先 | Transport |
|---|---|---|---|
| [Track A](track-a/) | IBM watsonx Orchestrate 公式ドキュメント検索 | `developer.watson-orchestrate.ibm.com/mcp` | **Streamable HTTP** |
| [Track B](track-b/) | GitMCP — GitHub リポジトリを MCP で検索 | `gitmcp.io/matsuo-iguazu/wxo-mcp-lab` | **SSE** |

---

## YAML の違いを一目で

```yaml
# ローカル MCP（01_postgres-mcp/track-a の例）
spec_version: v1
kind: mcp
name: m-postgres
command: '["sh", "-c", "npx -y @modelcontextprotocol/server-postgres $DATABASE_URL"]'
connections:
  - m-postgres-conn   # 認証情報を Connection で渡す

# リモート MCP（本実験）
spec_version: v1
kind: mcp
name: m-adk-docs
transport: streamable_http          # ← transport を指定
server_url: https://developer.watson-orchestrate.ibm.com/mcp  # ← URL を指定
# connections: 不要（認証なし）
```

---

詳しい手順は各トラックの README を参照してください。
