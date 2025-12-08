#!/bin/bash
set -e

echo "🔄 Activating environment..."
source /Users/liaokeyue/miniconda3/bin/activate appworld

echo "🚀 Starting AppWorld APIs on port 9000..."
appworld serve apis --port 9000 &
PID_APIS=$!

echo "🌍 Starting AppWorld environment on port 8000..."
appworld serve environment --port 8000 &
PID_ENV=$!

echo "🔌 Starting MCP server on port 10000..."
appworld serve mcp http \
  --remote-apis-url http://localhost:9000 \
  --app-names supervisor,amazon,spotify,gmail,phone,venmo,splitwise,simple_note,todoist,file_system \
  --port 10000 &
PID_MCP=$!

# 给环境一点时间启动
sleep 3

echo "🤖 Starting GREEN agent via run_agent..."
agentbeats run_agent --agent-card scenarios/appworld/green_agent/green_agent_card.toml

echo "🛑 Green agent exited. Cleaning up servers..."
kill $PID_APIS $PID_ENV $PID_MCP || true
