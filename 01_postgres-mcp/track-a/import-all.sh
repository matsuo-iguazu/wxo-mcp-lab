#!/usr/bin/env bash
# =============================================================================
# import-all.sh  —  04_postgres-mcp セットアップスクリプト
#
# 実行前提:
#   - orchestrate env activate IG  (WxO IG 環境がアクティブ)
#   - DATABASE_URL 環境変数に Supabase 接続文字列がセットされていること
#     例: export DATABASE_URL="postgresql://postgres:xxxx@db.xxx.supabase.co:5432/postgres"
#
# 使い方:
#   chmod +x import-all.sh
#   DATABASE_URL="postgresql://..." ./import-all.sh
# =============================================================================

set -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "=== Step 1: Connection 定義をインポート ==="
orchestrate connections import -f "${SCRIPT_DIR}/connections/m-postgres-conn.yaml"

echo "=== Step 2: Connection に DATABASE_URL を登録 ==="
if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL 環境変数がセットされていません。"
  echo "実行例: DATABASE_URL='postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres' ./import-all.sh"
  exit 1
fi

for env in draft live; do
  orchestrate connections configure -a m-postgres-conn --env $env --type team --kind key_value
  orchestrate connections set-credentials -a m-postgres-conn --env $env \
    -e "DATABASE_URL=${DATABASE_URL}"
done
echo "  DATABASE_URL を draft / live 両環境に登録しました。"

echo "=== Step 3: MCP ツールキットをインポート ==="
orchestrate toolkits import -f "${SCRIPT_DIR}/toolkits/m-postgres-toolkit.yaml"

echo "=== Step 4: エージェントをインポート ==="
orchestrate agents import -f "${SCRIPT_DIR}/agents/M-postgres-agent.yaml"

echo ""
echo "=== 完了 ==="
echo "WxO チャットで M_postgres_agent を選択してテストしてください。"
echo ""
echo "確認コマンド:"
echo "  orchestrate toolkits list"
echo "  orchestrate agents list"
