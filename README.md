# wxo-mcp-lab

IBM watsonx Orchestrate（WxO）の **MCP Toolkit** 機能を検証するラボリポジトリです。

WxO エージェントから外部ツール・データソースを MCP（Model Context Protocol）経由で呼び出す方法を、実験ごとにまとめています。

---

## 実験一覧

| # | タイトル | 概要 |
|---|---|---|
| [01_postgres-mcp](01_postgres-mcp/) | PostgreSQL MCP Toolkit | WxO エージェントから PostgreSQL を自然言語で参照する |

---

## 前提条件

- IBM watsonx Orchestrate の環境（Developer Edition または IG/SaaS）
- `orchestrate` CLI（[ADK](https://github.com/IBM/ibm-watsonx-orchestrate-adk) に同梱）
- `orchestrate env activate <env>` で環境をアクティブにしておくこと

---

## ライセンス

MIT
