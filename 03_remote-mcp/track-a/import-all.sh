#!/bin/bash
set -e

echo "=== [1/2] Toolkit をインポート ==="
orchestrate toolkits import -f toolkits/m-adk-docs.yaml

echo ""
echo "=== [2/2] エージェントをインポート ==="
orchestrate agents import -f agents/M-adk-docs-agent.yaml

echo ""
echo "=== 完了 ==="
echo "インポートされたツール:"
orchestrate tools list | grep m-adk-docs
