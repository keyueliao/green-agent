#!/bin/bash
set -e


conda activate agentbeats-311

echo "Starting AppWorld APIs..."
appworld serve apis --port 9000 &
PID_APIS=$!

echo "Starting AppWorld Environment..."
appworld serve environment --port 8000 &
PID_ENV=$!

echo "Starting AppWorld MCP..."
appworld serve mcp http \
  --remote-apis-url http://localhost:9000 \
  --app-names supervisor,amazon,spotify,gmail,phone,venmo,splitwise,simple_note,todoist,file_system \
  --port 10000 &
PID_MCP=$!

sleep 2

echo "Starting GREEN agent..."
agentbeats run_agent --agent-card scenarios/appworld/green_agent/green_agent_card.toml

kill $PID_APIS $PID_ENV $PID_MCP || true
