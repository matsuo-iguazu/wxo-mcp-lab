# wxO エージェントから Gmail を操作する MCP を FastMCP で自作した

IBM watsonx Orchestrate（wxO）に MCP でさまざまなサービスをつなぐ実験をしています。今回は **Gmail** です。FastMCP（Python）でローカル MCP サーバーを自作し、wxO エージェントから受信トレイの確認・本文取得・メール送信ができるようにしました。

実装自体はシンプルですが、**認証の設計**に少し工夫が必要でした。

---

## 認証の設計

Gmail API には OAuth2 認証が必要です。最初は wxO の Connection を OAuth auth code flow タイプで設定しようとしましたが、公式ドキュメントに以下の記載があります。

> *"OAuth connections are currently only supported by agents in the watsonx Orchestrate integrated web chat UI"*
> （OAuth 接続は MCP Toolkit では未対応。統合 Web Chat UI のエージェント専用。）

MCP Toolkit で外部 API 認証に使えるのは **key_value タイプのみ**です。

そこで OAuth2 の仕組みを活用しました。OAuth2 には2種類のトークンがあります。

| トークン | 有効期限 | 役割 |
|---|---|---|
| **access_token** | 約1時間 | Gmail API を直接呼び出す際の認証キー |
| **refresh_token** | 長期間有効 | Gmail API には直接使わず、新しい access_token を取得するために使う |

**refresh_token があれば access_token を何度でも自動更新できる**という性質を使い、次の方針で実装しました。

```
【1回だけ・手元の PC で実施】
  get_refresh_token.py を実行 → ブラウザで Google 認証 → refresh_token を取得

【wxO に預ける】
  refresh_token / client_id / client_secret を key_value Connection に格納

【MCP サーバーが毎回実施】
  起動のたびに refresh_token → access_token に交換 → Gmail API を呼び出す
```

---

## YAML ファイル

**Connection**（key_value タイプ）

```yaml
spec_version: v1
kind: connection
app_id: m-gmail-conn
environments:
  draft:
    kind: key_value
    type: team
  live:
    kind: key_value
    type: team
```

**Toolkit**（`package_root` で Python ファイルをアップロード）

```yaml
spec_version: v1
kind: mcp
name: m-gmail-mcp
package_root: ../mcp_server
command: python server.py
connections:
  - m-gmail-conn
tools:
  - "*"
```

---

## 実装（抜粋）

key_value Connection のキー名がそのまま環境変数名になります（prefix なし）。サーバー起動時に refresh_token → access_token を交換し、各ツールから Gmail API を呼び出します。

```python
REFRESH_TOKEN = os.environ.get("refresh_token", "")
CLIENT_ID     = os.environ.get("client_id", "")
CLIENT_SECRET = os.environ.get("client_secret", "")

def _get_access_token() -> str:
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]
```

セットアップ手順・全コードは GitHub を参照してください。

https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/02_google-services-mcp/gmail

---

## 動作確認

wxO チャットで `M_gmail_agent` に話しかけると、Gmail を自然言語で操作できます。

```
受信トレイの最新メールを見せて
→ 件名・送信者・日付の一覧が表示される

ID: xxxx のメール本文を見せて
→ メール本文が表示される

xxx@example.com に件名「ご連絡」、本文「お世話になっております」でメールを送って
→ 送信完了。メッセージ ID: ... が返ってくる
```

---

## まとめ

- wxO MCP Toolkit の認証は **key_value 一択**（OAuth auth code flow は未対応）
- refresh_token を key_value に格納することで、MCP サーバーが自律的に OAuth2 認証を処理できる
- key_value の env var 名はキー名がそのまま入る（prefix なし）

---

## シリーズ

| # | タイトル |
|---|---|
| 01 | [PostgreSQL MCP（Track A: npx）](https://qiita.com/IG_Matsuo/items/9106a80d26fbe3b736e0) |
| 01 | [PostgreSQL MCP（Track B: FastMCP Python）](https://qiita.com/IG_Matsuo/items/ecaf203af45d6737705b) |
| 02 | この記事 |
| 03 | [リモート MCP（Streamable HTTP × IBM ADK 公式ドキュメント）](https://qiita.com/IG_Matsuo/items/8196b6316769fe816f7f) |
| 03 | [リモート MCP（SSE × GitMCP）](https://qiita.com/IG_Matsuo/items/d09e72bb45e5ee92309f) |

---

本記事は、執筆にあたり Anthropic Claude を利用し、その出力を参考にしています。
