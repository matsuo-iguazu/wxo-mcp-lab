# gmail — Gmail MCP Toolkit for watsonx Orchestrate

**FastMCP で Gmail MCP サーバーを自作**し、受信トレイ取得・本文確認・メール送信を wxO エージェントから呼び出せることを確認する。

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

---

## 認証の考え方

### OAuth2 のトークンについて

Gmail API へのアクセスには OAuth2 認証が必要です。OAuth2 では2種類のトークンが登場します。

| トークン | 有効期限 | 役割 |
|---|---|---|
| **access_token** | 約1時間 | Gmail API を直接呼び出す際の認証キー |
| **refresh_token** | 長期間有効（※） | Gmail API には直接使わず、新しい access_token を取得するために使う |

※ Google OAuth アプリがテストステータスの場合は7日で期限切れ。本番公開後は無期限。

つまり **refresh_token さえ持っていれば、access_token を何度でも自動更新できる**ため、長期運用が可能になります。

### wxO での扱い方

wxO の MCP Toolkit が扱える Connection タイプは **key_value のみ**（OAuth auth code flow タイプは MCP Toolkit では未対応）。

そのため、次の方針で実装しています。

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

「OAuth2 を使っている」のは事実ですが、**wxO 側は refresh_token という文字列を受け取るだけ**です。OAuth のブラウザ認証フロー自体は手元 PC で1回だけ実行し、以降は MCP サーバーが自動で access_token を更新します。

---

## サンプルのリソース名について

このリポジトリのファイルは以下の名称を前提に作成されています。
ご利用の環境やチームの命名規則に合わせて、YAML ファイルを適宜変更してください。

| リソース | サンプル名 |
|---|---|
| Connection | `m-gmail-conn` |
| Toolkit | `m-gmail-mcp` |
| エージェント | `M_gmail_agent` |

---

## ツール一覧

| ツール名 | 概要 | 主な引数 |
|---|---|---|
| `list_messages` | 受信トレイの最新メール一覧（件名・送信者・日付） | `max_results`（省略可、デフォルト10） |
| `get_message` | 指定 ID のメール本文を取得 | `message_id` |
| `send_message` | メール送信 | `to`, `subject`, `body` |

---

## 前提条件

- wxO 環境がアクティブであること（`orchestrate env activate <env>`）
- Google アカウントがあること

---

## セットアップ

### リポジトリを取得

```bash
git clone https://github.com/matsuo-iguazu/wxo-mcp-lab.git
cd wxo-mcp-lab/02_google-services-mcp/gmail
```

### 1. Google Cloud Console の設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. **Gmail API** を有効化
3. **OAuth 同意画面** を設定
   - スコープ: `gmail.readonly`, `gmail.send` を追加（Gmail API 有効化時に自動設定される場合もある）
   - **テストユーザー** に操作対象の Gmail アドレスを追加（これがないと「アクセスをブロック」エラーになる）
4. **OAuth 2.0 クライアント ID** を作成（種類: ウェブアプリケーション）
   - 承認済みのリダイレクト URI に `http://localhost:8080` を追加
   - 作成後に表示される **クライアント ID** と **クライアントシークレット** を控える（または JSON をダウンロードして保存）

### 2. refresh_token を取得

`get_refresh_token.py` の `CLIENT_ID` と `CLIENT_SECRET` を手順 1.4. で控えた値に書き換えてから実行：

```bash
python get_refresh_token.py
```

表示された URL をブラウザで開いて Google アカウントで承認すると、ターミナルに `refresh_token` が表示される。

> **テストモードの注意**: Google OAuth アプリがテストステータスの場合、refresh_token は **7日で期限切れ**になる。本番公開（Google 審査通過）後は無期限。

### 3. Connection をインポート・設定

```bash
orchestrate connections import -f connections/m-gmail-conn.yaml

orchestrate connections set-credentials -a m-gmail-conn --env draft \
  -e refresh_token=<取得した refresh_token> \
  -e client_id=<Google OAuth クライアント ID> \
  -e client_secret=<Google OAuth クライアントシークレット>

orchestrate connections set-credentials -a m-gmail-conn --env live \
  -e refresh_token=<取得した refresh_token> \
  -e client_id=<Google OAuth クライアント ID> \
  -e client_secret=<Google OAuth クライアントシークレット>
```

> **フラグに注意**: key_value には `-e`（`--entries`）を使う。`-t` は OAuth タイプ専用で key_value には使えない。

### 4. Toolkit をデプロイ

```bash
orchestrate toolkits import -f toolkits/m-gmail-mcp.yaml
```

`toolkits import` 実行時に wxO が `mcp_server/` を zip 化してアップロードし、
`requirements.txt` の依存パッケージをクラウド上でインストールしてからサーバーを起動する。
3 ツールが認識されれば成功。

### 5. エージェントをインポート

```bash
orchestrate agents import -f agents/M-gmail-agent.yaml
```

---

## テスト

wxO チャットで `M_gmail_agent` を選択して話しかける。

```
受信トレイの最新メールを見せて
→ 件名・送信者・日付の一覧が返ってくる

ID: <message_id> のメール本文を見せて
→ メール本文が表示される

<宛先> に件名「テスト」、本文「テストです」でメールを送って
→ 送信完了。メッセージ ID: ... が返ってくる
```

---

## 検証メモ

### OAuth auth code flow は MCP Toolkit で使えない

当初 OAuth auth code flow Connection で実装を試みたが 401 Unauthorized となり動作しなかった。
公式ドキュメントに「OAuth connections are currently only supported by agents in the watsonx Orchestrate integrated web chat UI (not embedded web chat)」と明記されており、MCP Toolkit では OAuth credentials は注入されない。

**回避策**: key_value Connection に `refresh_token` / `client_id` / `client_secret` を格納し、サーバーが起動ごとに Google Token Endpoint へ exchange リクエストを送って `access_token` を取得する。

### key_value connection の env var 命名

Connection に登録したキー名がそのまま環境変数名になる（prefix なし）。

```python
# NG: os.environ.get("WXO_CONNECTION_m_gmail_conn_refresh_token")
# OK:
REFRESH_TOKEN = os.environ.get("refresh_token", "")
```

### Gmail API の metadataHeaders は list of tuples で渡す

`urllib.parse.urlencode` でカンマ区切り文字列として渡すと1つのパラメーターとして解釈されてしまう。

```python
# NG: {"metadataHeaders": "Subject,From,Date"}
# OK:
[("metadataHeaders", "Subject"), ("metadataHeaders", "From"), ("metadataHeaders", "Date")]
```

