#!/bin/bash
set -e

echo "=== [1/2] Toolkit をインポート ==="
orchestrate toolkits import -f toolkits/m-gitmcp.yaml

echo ""
echo "=== インポートされたツールを確認 ==="
orchestrate tools list | grep m-gitmcp
echo "↑ 上記のツール名を agents/M-gitmcp-agent.yaml の tools: に反映してください"

echo ""
echo "=== [2/2] エージェントをインポート ==="
orchestrate agents import -f agents/M-gitmcp-agent.yaml

echo ""
echo "=== 完了 ==="
