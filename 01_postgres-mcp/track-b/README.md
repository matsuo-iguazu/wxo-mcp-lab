# Track B — FastMCP Python で PostgreSQL R/W MCP サーバーを自作する

**Python で MCP サーバーを自作**し、CRUD 操作を wxO エージェントから呼び出せることを確認する。
Track A との比較は [01_postgres-mcp/README.md](../README.md) を参照。

---

## FastMCP とは

**FastMCP** は Python で MCP サーバーを書くためのフレームワーク。
`@mcp.tool()` デコレータをつけた Python 関数が、そのまま MCP ツールとして公開される。
**型ヒント** と **docstring** がツールの引数定義・説明として自動生成される。

```
┌────────────────────────────────────────────┐
│  wxO エージェント（MCP クライアント）        │
└──────────────────┬─────────────────────────┘
                   │ MCP プロトコル（STDIO）
┌──────────────────▼─────────────────────────┐
│  FastMCP サーバー（mcp_server/server.py）   │
│  @mcp.tool() list_products()               │
│  @mcp.tool() add_product()                 │
│  @mcp.tool() update_product_price()        │
│  @mcp.tool() delete_product()              │
└──────────────────┬─────────────────────────┘
                   │ psycopg2
┌──────────────────▼─────────────────────────┐
│  PostgreSQL（Supabase）                     │
└────────────────────────────────────────────┘
```

---

## サンプルのリソース名について

このリポジトリのファイルは以下の名称を前提に作成されています。
ご利用の環境やチームの命名規則に合わせて、YAML ファイルおよびスクリプトを適宜変更してください。

| リソース | サンプル名 |
|---|---|
| Connection | `m-postgres-conn` |
| Toolkit | `m-postgres-rw` |
| エージェント | `M_postgres_rw_agent` |

---

## ツール一覧

| ツール名 | SQL | 引数 |
|---|---|---|
| `list_products` | SELECT | category（省略可） |
| `add_product` | INSERT | name, category, price, stock |
| `update_product_price` | UPDATE | product_id, new_price |
| `delete_product` | DELETE | product_id |

---

## セットアップ

### リポジトリを取得

```bash
git clone https://github.com/matsuo-iguazu/wxo-mcp-lab.git
cd wxo-mcp-lab/01_postgres-mcp/track-b
```

### 前提条件

- Track A のセットアップ（Supabase テーブル作成・Connection 登録）が完了していること
- `orchestrate env activate <env>` で環境をアクティブにしておくこと

---

## 手順

### Phase 1 — MCP Inspector でローカル動作確認（省略可）

wxO にデプロイする前に、ローカルで MCP サーバーの動作を確認できる。

```bash
# ローカル環境に psycopg2-binary が必要（初回のみ）
pip install psycopg2-binary fastmcp

# Inspector を起動
DATABASE_URL="postgresql://..." fastmcp dev mcp_server/server.py
```

ターミナルに表示される `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...` をブラウザで開く。
**Tools タブ**に 4 ツールが表示され、実行できれば OK。

> **WSL2 の場合**: `127.0.0.1` ではなく `localhost` を使う。

### Phase 2 — wxO にデプロイ

Track A で Connection `m-postgres-conn` が登録済みであれば、手順 2〜3 は不要。

#### 1. Connection をインポート（Track A 未実施の場合のみ）

```bash
orchestrate connections import -f connections/m-postgres-conn.yaml

for env in draft live; do
  orchestrate connections configure -a m-postgres-conn --env $env --type team --kind key_value
  orchestrate connections set-credentials -a m-postgres-conn --env $env \
    -e "DATABASE_URL=postgresql://postgres.xxxx:[PASSWORD]@aws-1-xxx.pooler.supabase.com:5432/postgres"
done
```

#### 2. Toolkit をデプロイ

```bash
orchestrate toolkits import -f toolkits/m-postgres-rw.yaml
```

`toolkits import` 実行時に wxO が `mcp_server/` を zip 化してアップロードし、
`requirements.txt` の依存パッケージをクラウド上でインストールしてからサーバーを起動する。
4 ツールが認識されれば成功。

#### 3. エージェントをインポート

```bash
orchestrate agents import -f agents/M-postgres-rw-agent.yaml
```

#### 一括実行（手順 1〜3）

```bash
export DATABASE_URL="postgresql://..."
./import-all.sh
```

---

## テスト

wxO チャットで `M_postgres_rw_agent` を選択して話しかける。

```
商品一覧を見せて
→ products テーブルの全件が表示される

PC の商品だけ見せて
→ category = 'PC' で絞り込んで返ってくる

テスト商品を 500 円、カテゴリ test、在庫 1 で追加して
→ INSERT 実行、新しい ID が返ってくる

追加したテスト商品の価格を 999 円にして
→ UPDATE 実行、変更が反映される

追加したテスト商品を削除して
→ DELETE 実行、件数が減ることを確認
```

---

## 検証メモ

### `package_root:` の挙動

`orchestrate toolkits import` を実行すると、指定したディレクトリが **zip に圧縮されてクラウドにアップロード**される。
wxO はアップロードされたファイルを展開し、`requirements.txt` をもとに依存パッケージをインストールしてから `command:` を実行する。

```yaml
# toolkits/m-postgres-rw.yaml
package_root: ../mcp_server   # このディレクトリが zip 化される
command: python server.py     # クラウド上で実行されるコマンド
```

### Toolkit は上書き不可

同名の Toolkit が存在する場合、`toolkits import` は失敗する。
再デプロイ時は先に削除が必要。

```bash
orchestrate toolkits delete m-postgres-rw
orchestrate toolkits import -f toolkits/m-postgres-rw.yaml
```

> Toolkit を削除するとエージェントのツール参照が切れるため、**Agent も再インポートが必要**。

### Supabase の products テーブルの主キーは `id`

Track A の `setup_supabase.sql` で作成したテーブルの主キーカラム名は `product_id` ではなく `id`。
SQL は `WHERE id = %s`、`ORDER BY id` のように記述する。

### FastMCP の型ヒント・docstring がそのままツール定義になる

```python
@mcp.tool()
def list_products(category: str = None) -> str:
    """商品一覧を返す。category を指定すると絞り込む。"""
```

MCP Inspector の Tools タブでは関数名がツール名、docstring が説明文として表示される。
wxO エージェントはこの定義を読んで、どのツールをいつ呼ぶかを判断する。
