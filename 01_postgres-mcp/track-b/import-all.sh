#!/usr/bin/env bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "=== Track B: FastMCP Python PostgreSQL R/W ==="

# --- DATABASE_URL チェック ---
if [ -z "${DATABASE_URL}" ]; then
  echo "ERROR: DATABASE_URL 環境変数が未設定です。"
  echo "  export DATABASE_URL=\"postgresql://postgres.xxxx:[PASSWORD]@aws-1-xxx.pooler.supabase.com:5432/postgres\""
  exit 1
fi

# --- 1. Connection ---
echo "[1/3] Connection をインポート..."
orchestrate connections import -f "${SCRIPT_DIR}/connections/m-postgres-conn.yaml"

for env in draft live; do
  orchestrate connections configure -a m-postgres-conn --env $env --type team --kind key_value
  orchestrate connections set-credentials -a m-postgres-conn --env $env \
    -e "DATABASE_URL=${DATABASE_URL}"
done

# --- 2. Toolkit（--package-root で Python ファイルをアップロード）---
echo "[2/3] Toolkit をデプロイ中（package_root: mcp_server/）..."
orchestrate toolkits import -f "${SCRIPT_DIR}/toolkits/m-postgres-rw.yaml"

# --- 3. Agent ---
echo "[3/3] エージェントをインポート..."
orchestrate agents import -f "${SCRIPT_DIR}/agents/M-postgres-rw-agent.yaml"

echo ""
echo "=== 完了 ==="
echo "wxO チャットで M_postgres_rw_agent を選択して動作確認してください。"
