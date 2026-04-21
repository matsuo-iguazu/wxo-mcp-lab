# GitHub リポジトリをそのまま MCP サーバー化して wxO エージェントから検索する（GitMCP × SSE）

IBM watsonx Orchestrate（wxO）のリモート MCP 接続を試しています。

Track A では Streamable HTTP を使いましたが、今回は **SSE（Server-Sent Events）** を使います。

接続先はちょっと変わったサービス「**GitMCP**」。GitHub リポジトリの URL を入れるだけで、そのリポジトリを MCP サーバーとして公開してくれます。自分のリポジトリを wxO エージェントで検索させる、というメタな構成です。

コードは [wxo-mcp-lab/03_remote-mcp/track-b](https://github.com/matsuo-iguazu/wxo-mcp-lab/tree/main/03_remote-mcp/track-b) に置いています。

---

## GitMCP とは

[GitMCP](https://gitmcp.io) は任意の GitHub リポジトリをリモート MCP サーバーとして公開するサービスです。

```
https://gitmcp.io/{owner}/{repo}
```

この URL に接続するだけで、対象リポジトリの README やドキュメントを MCP ツールで検索・取得できるようになります。

- GitHub アカウント不要
- GitMCP へのサインアップ不要
- サーバー構築不要
- 認証不要

公開リポジトリであればどんなリポジトリでも即座に MCP サーバー化できます。

今回は自分のリポジトリ `matsuo-iguazu/wxo-mcp-lab`（この実験を含むリポジトリ）に接続します。wxO エージェントが wxo-mcp-lab の手順書を参照して回答する、というメタな構成です。

---

## SSE とは

Track A で使った Streamable HTTP との違いを簡単に整理します。

| | Streamable HTTP | SSE |
|---|---|---|
| 通信方式 | HTTP リクエスト/レスポンス | サーバーからのイベントストリーム |
| wxO YAML | `transport: streamable_http` | `transport: sse` |
| 用途 | 汎用（現在の主流） | 古い MCP サーバーや一部サービス |

YAML の `transport:` の値が変わるだけで、他の書き方は同じです。

---

## YAML ファイル

### Toolkit（toolkits/m-gitmcp.yaml）

```yaml
spec_version: v1
kind: mcp
name: m-gitmcp
description: >
  GitMCP 経由で matsuo-iguazu/wxo-mcp-lab リポジトリのドキュメントを検索するリモート MCP ツールキット。
  SSE でパブリックサーバーに接続する。認証不要。
transport: sse
server_url: https://gitmcp.io/matsuo-iguazu/wxo-mcp-lab
tools:
  - "*"
```

Track A の Toolkit と比べると `transport: sse` と `server_url:` が変わっただけです。

### Agent（agents/M-gitmcp-agent.yaml）

```yaml
spec_version: v1
kind: native
name: M_gitmcp_agent
description: >
  GitMCP 経由で matsuo-iguazu/wxo-mcp-lab の README や手順書を自然言語で検索するエージェント。
  リモート MCP ツールキット m-gitmcp を通じて GitHub リポジトリのドキュメントを参照する。
instructions: |
  あなたは wxo-mcp-lab リポジトリ（https://github.com/matsuo-iguazu/wxo-mcp-lab）のナビゲーターです。
  ユーザーの質問に応じて、以下のツールを使ってリポジトリのドキュメントやコードを検索し、日本語で回答してください。

  ツールの使い方:
  - search_wxo_mcp_lab_documentation: ドキュメント（README など）をキーワード検索する
  - fetch_wxo_mcp_lab_documentation: ドキュメントの内容を取得する
  - search_wxo_mcp_lab_code: コードファイルをキーワード検索する
  - fetch_generic_url_content: 特定の URL のコンテンツを取得する

  回答ルール:
  1. 必ず日本語で回答すること
  2. 参照したファイル名（README.md など）を明示すること
  3. 手順や設定例はそのまま引用して見やすく提示すること
llm: groq/openai/gpt-oss-120b
style: react
tools:
  - m-gitmcp:search_wxo_mcp_lab_documentation
  - m-gitmcp:fetch_wxo_mcp_lab_documentation
  - m-gitmcp:search_wxo_mcp_lab_code
  - m-gitmcp:fetch_generic_url_content
```

---

## ツール名の確認が必要

GitMCP が公開するツール名はリポジトリ名から**自動生成**されます。

`matsuo-iguazu/wxo-mcp-lab` に接続した場合、公開されるツールは以下の 4 本でした：

```
m-gitmcp:search_wxo_mcp_lab_documentation  ← ドキュメントのキーワード検索
m-gitmcp:fetch_wxo_mcp_lab_documentation   ← ドキュメントの内容取得
m-gitmcp:search_wxo_mcp_lab_code           ← コードのキーワード検索
m-gitmcp:fetch_generic_url_content         ← 任意 URL のコンテンツ取得
```

**別のリポジトリに接続する場合はツール名が変わります**（リポジトリ名の部分が変化）。

Toolkit をインポートした後に `orchestrate tools list` で確認し、エージェント YAML の `tools:` を更新してください。

---

## 手順

```bash
# 1. Toolkit をインポート
orchestrate toolkits import -f toolkits/m-gitmcp.yaml

# 2. インポートされたツール名を確認
orchestrate tools list | grep m-gitmcp

# 3. エージェント YAML の tools: とツール名が一致しているか確認
#    （異なる場合は agents/M-gitmcp-agent.yaml を編集）

# 4. エージェントをインポート
orchestrate agents import -f agents/M-gitmcp-agent.yaml
```

---

## 動作確認

wxO チャットで `M_gitmcp_agent` に話しかけると、リポジトリの README を参照して回答してくれます。

```
Q: このリポジトリにはどんな実験がありますか？
A: wxo-mcp-lab には以下の実験が含まれています。
   01_postgres-mcp: PostgreSQL への MCP 接続（Track A: 公式 npm パッケージ / Track B: FastMCP）
   02_google-services-mcp: Gmail 連携（OAuth refresh_token 方式）
   03_remote-mcp: リモート MCP サーバーへの接続（Streamable HTTP / SSE）
   …（README の内容を参照して回答）

Q: Track A の PostgreSQL 接続手順を教えて
A: 01_postgres-mcp/track-a/README.md を参照すると…
   （手順を引用して回答）
```

---

## 発展：IBM ADK リポジトリに接続する

自分のリポジトリは遊び心でつないでみましたが、もっと実用的な使い方があります。

**IBM ADK リポジトリ**（`IBM/ibm-watsonx-orchestrate-adk`）に接続すると、ADK のサンプルコードや設定ファイルを参照して回答するエージェントになります。

```yaml
# toolkits/m-gitmcp.yaml の server_url を変更するだけ
server_url: https://gitmcp.io/IBM/ibm-watsonx-orchestrate-adk
```

公開ドキュメントだけでなく、GitHub 上のサンプルコードまで参照できる検索エージェントができます。

---

## まとめ

- GitMCP は GitHub リポジトリをそのままリモート MCP サーバー化するサービス
- wxO Toolkit の `transport: sse` + `server_url: https://gitmcp.io/...` で接続できる
- ツール名はリポジトリ名から自動生成されるため、インポート後に `orchestrate tools list` で確認が必要
- 別のリポジトリに変えるときは `server_url:` を書き換えるだけ

Track A（Streamable HTTP）と合わせると、YAML の `transport:` を切り替えるだけで 2 種類のリモート接続に対応できることがわかります。

---

## シリーズ

- [wxO で PostgreSQL に MCP 接続する（Track A: 公式 npm パッケージ）](https://qiita.com/IG_Matsuo/items/9106a80d26fbe3b736e0)
- [wxO で PostgreSQL に MCP 接続する（Track B: FastMCP で R/W 操作）](https://qiita.com/IG_Matsuo/items/ecaf203af45d6737705b)
- [wxO から公式ドキュメントをリモート MCP で検索する（Streamable HTTP）]() ← Track A
- wxO で GitHub リポジトリを MCP サーバー化して検索する（SSE × GitMCP）← この記事
