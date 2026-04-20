# wxo-mcp-lab

IBM watsonx Orchestrate（wxO）の **MCP Toolkit** 機能を検証するラボリポジトリです。

wxO エージェントから外部ツール・データソースを MCP（Model Context Protocol）経由で呼び出す方法を、実験ごとにまとめています。

---

## 実験一覧

| # | タイトル | 概要 |
|---|---|---|
| [01_postgres-mcp](01_postgres-mcp/) | PostgreSQL MCP Toolkit | wxO エージェントから PostgreSQL を自然言語で参照する |
| [02_google-services-mcp](02_google-services-mcp/) | Google サービス MCP Toolkit | wxO エージェントから Gmail など Google サービスを自然言語で操作する |
| [03_remote-mcp](03_remote-mcp/) | リモート MCP サーバーへの接続 | 公開リモート MCP サーバー（Streamable HTTP / SSE）に接続する |

---

## 前提条件

- IBM watsonx Orchestrate の環境（Developer Edition または SaaS）
- `orchestrate` CLI（[ADK](https://github.com/IBM/ibm-watsonx-orchestrate-adk) に同梱）
- `orchestrate env activate <env>` で環境をアクティブにしておくこと

---

## ライセンス

MIT
