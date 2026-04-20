# Track B — GitMCP で GitHub リポジトリを MCP 化（SSE）

[GitMCP](https://gitmcp.io) は任意の GitHub リポジトリをリモート MCP サーバーとして公開するサービスです。
URL にオーナー名とリポジトリ名を入れるだけで、そのリポジトリの README や各種ドキュメントを
MCP ツールとして検索・取得できるようになります。

このトラックでは **このリポジトリ自身**（`matsuo-iguazu/wxo-mcp-lab`）を GitMCP 経由で検索する
エージェントを作ります。wxO エージェントが wxo-mcp-lab の手順書を参照して回答する、というメタな構成です。

**Transport: SSE（Server-Sent Events）**

---

## GitMCP の仕組み

```
https://gitmcp.io/{owner}/{repo}
```

このエンドポイントにアクセスするだけで、対象リポジトリの内容を検索・取得する MCP サーバーとして機能します。
GitHub への認証・GitMCP へのサインアップ・サーバー構築は一切不要です。

---

## 前提条件

- IBM watsonx Orchestrate（SaaS）
- `orchestrate` CLI（[ADK](https://github.com/IBM/ibm-watsonx-orchestrate-adk) に同梱）
- `orchestrate env activate <env>` で環境をアクティブにしておくこと

---

## セットアップ

### リポジトリを取得

```bash
git clone https://github.com/matsuo-iguazu/wxo-mcp-lab.git
cd wxo-mcp-lab/03_remote-mcp/track-b
```

### リソース名について

| リソース | サンプル名 |
|---|---|
| Toolkit | `m-gitmcp` |
| エージェント | `M_gitmcp_agent` |

---

## 手順

### 1. Toolkit をインポート

```bash
orchestrate toolkits import -f toolkits/m-gitmcp.yaml
```

### 2. インポートされたツール名を確認

```bash
orchestrate tools list | grep m-gitmcp
```

GitMCP が公開するツール名を確認します。
`agents/M-gitmcp-agent.yaml` の `tools:` に記載したツール名と一致しているか確認し、
異なる場合は YAML を編集してください。

### 3. エージェントをインポート

```bash
orchestrate agents import -f agents/M-gitmcp-agent.yaml
```

### 4. テスト

wxO チャットで `M_gitmcp_agent` を選択して話しかけます：

```
Track A の PostgreSQL 接続手順を教えて
→ 01_postgres-mcp/track-a/README.md の内容を参照して回答

FastMCP で MCP サーバーを作るにはどうすればいい？
→ 01_postgres-mcp/track-b/README.md の内容を参照して回答

このリポジトリにはどんな実験がありますか？
→ ルートの README.md を参照して実験一覧を回答
```

---

## 一括実行（import-all.sh）

```bash
chmod +x import-all.sh
./import-all.sh
```

> **注意**: スクリプト内でツール名の確認を促すメッセージが表示されます。
> `orchestrate tools list` の結果と `agents/M-gitmcp-agent.yaml` の `tools:` が一致していることを確認してから次に進んでください。

---

## 再デプロイ

```bash
orchestrate toolkits delete m-gitmcp
orchestrate agents delete M_gitmcp_agent
./import-all.sh
```

---

## 検証メモ

### GitMCP のツール名について

GitMCP が公開するツール名はリポジトリ名から自動生成されます。
`matsuo-iguazu/wxo-mcp-lab` リポジトリへの接続で確認されたツールは以下の 4 本です：

```
m-gitmcp:search_wxo_mcp_lab_documentation  ← ドキュメントのキーワード検索
m-gitmcp:fetch_wxo_mcp_lab_documentation   ← ドキュメントの内容取得
m-gitmcp:search_wxo_mcp_lab_code           ← コードのキーワード検索
m-gitmcp:fetch_generic_url_content         ← 任意 URL のコンテンツ取得
```

別のリポジトリに接続する場合はツール名が変わります（リポジトリ名部分が変化）。
**インポート後に `orchestrate tools list` で確認**してエージェント YAML を更新してください。

---

## 発展：IBM ADK リポジトリに接続する

このトラックは遊び心で自分のリポジトリに接続しましたが、
**IBM ADK リポジトリ**（`IBM/ibm-watsonx-orchestrate-adk`）に接続すると実用的な ADK 検索エージェントになります。

```yaml
# toolkits/m-gitmcp.yaml の server_url を変更するだけ
server_url: https://gitmcp.io/IBM/ibm-watsonx-orchestrate-adk
```

エージェントが ADK のサンプルコードや設定ファイルを参照して回答できるようになります。
