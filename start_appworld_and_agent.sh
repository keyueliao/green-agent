#!/bin/bash
set -e

echo "🚀 Starting AppWorld + Green Agent..."


cd /Users/liaokeyue/agentbeats-new

source /Users/liaokeyue/miniconda3/bin/activate appworld

# 3. AppWorld CLI
APPWORLD_BIN="/Users/liaokeyue/miniconda3/envs/appworld/bin/appworld"

mkdir -p logs

echo "🌍 [1/4] Starting AppWorld APIs on port 9000..."
$APPWORLD_BIN serve apis \
  --port 9000 \
  --with-setup \
  > logs/apis.log 2>&1 &
PID_APIS=$!

echo "🏞️ [2/4] Starting AppWorld Environment on port 8000..."
$APPWORLD_BIN serve environment \
  --port 8000 \
  --with-setup \
  > logs/environment.log 2>&1 &
PID_ENV=$!

echo "🔌 [3/4] Starting MCP server on port 10000..."
$APPWORLD_BIN serve mcp \
  --port 10000 \
  --with-setup \
  > logs/mcp.log 2>&1 &
PID_MCP=$!

echo "🤖 [4/4] Starting Green Agent (FastAPI) on port 8001..."
python green_agent_server.py > logs/green_agent.log 2>&1 &
PID_AGENT=$!

echo ""
echo "🎉 All services started!"
echo "📌 AppWorld APIs: http://localhost:9000"
echo "📌 Environment:   http://localhost:8000"
echo "📌 MCP Server:    http://localhost:10000"
echo "📌 Green Agent:   http://localhost:8001"
echo ""
echo "Press CTRL+C to stop all processes."

wait

