# 02_google-services-mcp — Google サービス MCP Toolkit for watsonx Orchestrate

watsonx Orchestrate (wxO) エージェントから **Google サービスを自然言語で操作**する実験です。
FastMCP で MCP サーバーを自作し、Google API と連携させます。

---

## 実験一覧

| 実験 | タイトル | 概要 |
|---|---|---|
| [gmail](gmail/) | Gmail MCP — メール読み書き | 受信トレイ取得・本文確認・送信を wxO エージェントから操作 |

---

## Google サービス × MCP の設計方針

### 認証は key_value 一択

wxO の MCP Toolkit（Local MCP）が対応している Connection タイプは **key_value のみ**。
OAuth auth code flow は MCP Toolkit では使えない（Python/OpenAPI ツール専用）。

| Connection タイプ | Python ツール | OpenAPI | **MCP Toolkit** |
|---|---|---|---|
| OAuth (Auth Code) | ✅ | ✅ | ❌ |
| **key_value** | ✅ | ❌ | **✅** |

公式ドキュメント: [connections/overview — Support by tool type](https://developer.watson-orchestrate.ibm.com/connections/overview#why-use-connections)

### key_value connection の env var

Connection に登録したキー名がそのまま環境変数名になる（prefix なし）。

```python
# Connection キー "refresh_token" → 環境変数 "refresh_token"
REFRESH_TOKEN = os.environ.get("refresh_token", "")
```

### Google 個人アカウント vs Workspace

| | 個人 Gmail | Google Workspace |
|---|---|---|
| 認証方式 | OAuth2 (refresh_token を key_value に格納) | サービスアカウント + ドメイン全委任 |
| トークン期限 | 7日（テストモード） / 無期限（本番公開後） | 無期限 |
| 複数ユーザー対応 | 不可（1アカウント固定） | 可（impersonate） |

---

詳しい手順は各実験の README を参照してください。
