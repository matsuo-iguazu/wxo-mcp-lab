"""
FastMCP PostgreSQL R/W サーバー

wxO の --package-root 機能でクラウドにデプロイされる MCP サーバー。
DATABASE_URL は wxO Connection (m-postgres-conn) から環境変数として注入される。
"""

import os
import json
import psycopg2
from fastmcp import FastMCP

mcp = FastMCP("postgres-rw")


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


@mcp.tool()
def list_products(category: str = None) -> str:
    """商品一覧を返す。category を指定すると絞り込む。"""
    conn = get_conn()
    cur = conn.cursor()
    if category:
        cur.execute(
            "SELECT * FROM products WHERE category = %s ORDER BY id",
            (category,),
        )
    else:
        cur.execute("SELECT * FROM products ORDER BY id")
    cols = [d[0] for d in cur.description]
    result = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def add_product(name: str, category: str, price: int, stock: int) -> str:
    """新しい商品を追加する。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s) RETURNING id",
        (name, category, price, stock),
    )
    pid = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return json.dumps({"status": "ok", "product_id": pid})


@mcp.tool()
def update_product_price(product_id: int, new_price: int) -> str:
    """商品の価格を変更する。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET price = %s WHERE id = %s",
        (new_price, product_id),
    )
    conn.commit()
    conn.close()
    return json.dumps({"status": "ok", "product_id": product_id, "new_price": new_price})


@mcp.tool()
def delete_product(product_id: int) -> str:
    """商品を削除する。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()
    return json.dumps({"status": "ok", "deleted_product_id": product_id})


if __name__ == "__main__":
    mcp.run()
