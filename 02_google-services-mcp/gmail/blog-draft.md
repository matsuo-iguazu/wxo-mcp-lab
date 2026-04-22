# wxO × Gmail MCP：FastMCP で Gmail を読む・送る

## シリーズ

| # | タイトル | リポジトリ |
|---|---|---|
| 01 | [PostgreSQL MCP（Track A: npx）](https://qiita.com/IG_Matsuo/items/9106a80d26fbe3b736e0) | [wxo-mcp-lab/01_postgres-mcp/track-a](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/01_postgres-mcp/track-a) |
| 01 | [PostgreSQL MCP（Track B: FastMCP Python）](https://qiita.com/IG_Matsuo/items/ecaf203af45d6737705b) | [wxo-mcp-lab/01_postgres-mcp/track-b](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/01_postgres-mcp/track-b) |
| 02 | この記事 | [wxo-mcp-lab/02_google-services-mcp/gmail](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/02_google-services-mcp/gmail) |
| 03 | [リモート MCP（Streamable HTTP × IBM ADK 公式ドキュメント）](https://qiita.com/IG_Matsuo/items/8196b6316769fe816f7f) | [wxo-mcp-lab/03_remote-mcp/track-a](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/03_remote-mcp/track-a) |
| 03 | [リモート MCP（SSE × GitMCP）](https://qiita.com/IG_Matsuo/items/d09e72bb45e5ee92309f) | [wxo-mcp-lab/03_remote-mcp/track-b](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/03_remote-mcp/track-b) |

---

## はじめに

このシリーズでは、IBM watsonx Orchestrate（wxO）に MCP でさまざまなサービスをつなぐ実験をしています。

今回は **Gmail** です。FastMCP（Python）でローカル MCP サーバーを自作し、受信トレイの確認・本文取得・メール送信を wxO エージェントから自然言語で操作できるようにしました。

> **UI vs CLI について**
> wxO の設定は UI でできる部分も多いですが、今回は Python ファイルのアップロード（`package_root`）と refresh_token の取得スクリプト実行が必要なため、CLI で進めます。

---

## 完成イメージ

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

## アーキテクチャ

```
┌────────────────────────────────────────────┐
│  wxO エージェント（MCP クライアント）        │
└──────────────────┬─────────────────────────┘
                   │ MCP プロトコル（STDIO）
┌──────────────────▼─────────────────────────┐
│  FastMCP サーバー（mcp_server/server.py）   │
│  @mcp.tool() list_messages()               │
│  @mcp.tool() get_message()                 │
│  @mcp.tool() send_message()                │
└──────────────────┬─────────────────────────┘
                   │ refresh_token → access_token に交換
                   │ Gmail REST API
┌──────────────────▼─────────────────────────┐
│  Gmail（個人アカウント）                     │
└────────────────────────────────────────────┘
```

## 認証の考え方

Gmail API へのアクセスには OAuth2 認証が必要です。OAuth2 では2種類のトークンが登場します。

| トークン | 有効期限 | 役割 |
|---|---|---|
| **access_token** | 約1時間 | Gmail API を呼び出す際に使う実際の認証キー |
| **refresh_token** | 長期間有効（※） | 期限切れの access_token を新しく取得するために使う |

※ Google OAuth アプリがテストステータスの場合は7日で期限切れ。本番公開後は無期限。

**refresh_token さえ持っていれば、access_token を何度でも自動更新できる**ため、長期運用が可能になります。

wxO の MCP Toolkit が扱える Connection タイプは **key_value のみ**（OAuth auth code flow タイプは MCP Toolkit では未対応）。そのため次の方針で実装しています。

```
【1回だけ・手元の PC で実施】
  get_refresh_token.py を実行
  → ブラウザで Google アカウントに同意
  → refresh_token を取得

【wxO に預ける】
  refresh_token / client_id / client_secret を
  key_value Connection に格納（ただの文字列として保存）

【MCP サーバーが毎回実施】
  起動のたびに refresh_token → access_token に交換
  → Gmail API を呼び出す
```

---

## ツール一覧

| ツール名 | 概要 | 主な引数 |
|---|---|---|
| `list_messages` | 受信トレイの最新メール一覧（件名・送信者・日付） | `max_results`（省略可、デフォルト 10） |
| `get_message` | 指定 ID のメール本文を取得 | `message_id` |
| `send_message` | メール送信 | `to`, `subject`, `body` |

---

## セットアップ

### 1. Google Cloud Console の設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. **Gmail API** を有効化
3. **OAuth 同意画面** を設定
   - スコープ: `gmail.readonly`, `gmail.send` を追加
   - **テストユーザー** に操作対象の Gmail アドレスを追加（ここを忘れると「アクセスをブロック」エラーになる）
4. **OAuth 2.0 クライアント ID** を作成（種類: ウェブアプリケーション）
   - 承認済みのリダイレクト URI に `http://localhost:8080` を追加
   - クライアント ID・シークレットを控える

### 2. refresh_token を取得

`get_refresh_token.py` の `CLIENT_ID` と `CLIENT_SECRET` を書き換えて実行します。

```bash
python get_refresh_token.py
```

表示された URL をブラウザで開いて Google アカウントで承認すると、ターミナルに `refresh_token` が表示されます。

> `prompt=consent` を指定することで refresh_token が確実に発行されます。省略すると2回目以降は発行されないことがあります。

> **テストモードの注意**: OAuth アプリがテストステータスの場合、refresh_token は **7日で期限切れ**になります。

### 3. Connection をインポート・設定

**connections/m-gmail-conn.yaml**

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

```bash
orchestrate connections import -f connections/m-gmail-conn.yaml

orchestrate connections set-credentials -a m-gmail-conn --env draft \
  -e refresh_token=<取得した refresh_token> \
  -e client_id=<クライアント ID> \
  -e client_secret=<クライアントシークレット>

orchestrate connections set-credentials -a m-gmail-conn --env live \
  -e refresh_token=<取得した refresh_token> \
  -e client_id=<クライアント ID> \
  -e client_secret=<クライアントシークレット>
```

> key_value の credentials 設定には `-e` フラグを使います（`-t` は OAuth タイプ専用）。

### 4. MCP サーバー実装

**mcp_server/server.py**

```python
#!/usr/bin/env python3
"""Gmail MCP Server — key_value + refresh_token で Gmail を操作"""
import os, json, base64, urllib.request, urllib.parse
from fastmcp import FastMCP

mcp = FastMCP("gmail-mcp")

# WxO key_value connection から注入される環境変数（キー名がそのまま env var 名になる）
REFRESH_TOKEN = os.environ.get("refresh_token", "")
CLIENT_ID = os.environ.get("client_id", "")
CLIENT_SECRET = os.environ.get("client_secret", "")

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def _get_access_token() -> str:
    """refresh_token を使って access_token を取得する"""
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN, "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def _gmail_get(path: str, params=None) -> dict:
    access_token = _get_access_token()
    url = f"{GMAIL_API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _gmail_post(path: str, body: dict) -> dict:
    access_token = _get_access_token()
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{GMAIL_API_BASE}{path}", data=data,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


@mcp.tool()
def list_messages(max_results: int = 10) -> str:
    """受信トレイの最新メール一覧を返す。件名・送信者・日付を含む。"""
    data = _gmail_get("/messages", {"labelIds": "INBOX", "maxResults": max_results})
    messages = data.get("messages", [])
    if not messages:
        return "メールが見つかりませんでした。"
    results = []
    for msg in messages:
        detail = _gmail_get(f"/messages/{msg['id']}",
            [("format", "metadata"), ("metadataHeaders", "Subject"),
             ("metadataHeaders", "From"), ("metadataHeaders", "Date")])
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        results.append(
            f"ID: {msg['id']}\n"
            f"  件名: {headers.get('Subject', '(件名なし)')}\n"
            f"  送信者: {headers.get('From', '(不明)')}\n"
            f"  日付: {headers.get('Date', '(不明)')}"
        )
    return "\n\n".join(results)


@mcp.tool()
def get_message(message_id: str) -> str:
    """指定した ID のメール本文を返す。"""
    detail = _gmail_get(f"/messages/{message_id}", {"format": "full"})
    headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}

    def extract_body(part):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        for p in part.get("parts", []):
            result = extract_body(p)
            if result:
                return result
        return ""

    body = extract_body(detail.get("payload", {})) or "(本文を取得できませんでした)"
    return f"件名: {headers.get('Subject')}\n送信者: {headers.get('From')}\n日付: {headers.get('Date')}\n\n{body}"


@mcp.tool()
def send_message(to: str, subject: str, body: str) -> str:
    """メールを送信する。"""
    raw = base64.urlsafe_b64encode(f"To: {to}\nSubject: {subject}\n\n{body}".encode()).decode()
    result = _gmail_post("/messages/send", {"raw": raw})
    return f"送信完了。メッセージ ID: {result.get('id', '不明')}"


if __name__ == "__main__":
    mcp.run()
```

**mcp_server/requirements.txt**

```
fastmcp
```

### 5. Toolkit をデプロイ

**toolkits/m-gmail-mcp.yaml**

```yaml
spec_version: v1
kind: mcp
name: m-gmail-mcp
description: FastMCP Python による Gmail 読み書きツールキット
package_root: ../mcp_server
command: python server.py
connections:
  - m-gmail-conn
tools:
  - "*"
```

```bash
orchestrate toolkits import -f toolkits/m-gmail-mcp.yaml
```

`package_root` を指定すると、wxO が `mcp_server/` を zip 化してクラウドにアップロードし、`requirements.txt` の依存パッケージをインストールしてからサーバーを起動します。3 ツールが認識されれば成功。

### 6. エージェントをインポート

**agents/M-gmail-agent.yaml**

```yaml
spec_version: v1
kind: native
name: M_gmail_agent
description: Gmail を自然言語で操作するエージェント。
llm: watsonx/meta-llama/llama-3-3-70b-instruct
style: react
instructions: |
  あなたは Gmail を操作するアシスタントです。
  ユーザーの指示に従い、メールの一覧取得・本文確認・送信を行ってください。
  日本語で応答してください。
tools:
  - m-gmail-mcp:list_messages
  - m-gmail-mcp:get_message
  - m-gmail-mcp:send_message
```

```bash
orchestrate agents import -f agents/M-gmail-agent.yaml
```

---

## 検証メモ

### key_value connection の env var はキー名がそのまま入る

```python
# ❌ WXO_CONNECTION_ prefix はない
REFRESH_TOKEN = os.environ.get("WXO_CONNECTION_m_gmail_conn_refresh_token")

# ✅ キー名がそのまま env var 名になる
REFRESH_TOKEN = os.environ.get("refresh_token")
```

### Gmail API の metadataHeaders は list of tuples で渡す

```python
# ❌ カンマ区切り文字列は1つのパラメーターとして解釈される
params = {"metadataHeaders": "Subject,From,Date"}

# ✅ tuple のリストで同名パラメーターを複数渡す
params = [("format", "metadata"), ("metadataHeaders", "Subject"),
          ("metadataHeaders", "From"), ("metadataHeaders", "Date")]
```

### OAuth auth code flow は MCP Toolkit では使えない

試してみたところ、`oauth_auth_code_flow` タイプの Connection では credentials が MCP サーバープロセスに注入されませんでした。[公式ドキュメント](https://developer.watson-orchestrate.ibm.com/connections/overview#why-use-connections)にも「OAuth connections are currently only supported by agents in the watsonx Orchestrate integrated web chat UI」と記載があります。**MCP Toolkit での外部 API 認証は key_value 一択**です。

---

## まとめ

FastMCP（Python）で Gmail MCP サーバーを自作し、wxO エージェントから Gmail を自然言語で操作できることを確認しました。

認証のポイントは **key_value connection に refresh_token を格納し、サーバー自身がトークン交換を行う**という設計です。Python の標準ライブラリだけで実装できるのもシンプルで気に入っています。

ソースコード全体は GitHub に置いてあります。

https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/02_google-services-mcp/gmail
