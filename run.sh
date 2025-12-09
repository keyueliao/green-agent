#!/bin/bash
set -e

echo "🔄 Starting AppWorld + Green Agent"


source /Users/liaokeyue/miniconda3/bin/activate appworld


cd /Users/liaokeyue/agentbeats-new


export PYTHONPATH=/Users/liaokeyue/agentbeats-new


APPWORLD_BIN="/Users/liaokeyue/miniconda3/envs/appworld/bin/appworld"
mkdir -p logs

echo "🚀 [1/4] Starting AppWorld APIs on port 9000 (with setup)..."
"$APPWORLD_BIN" serve apis \
  --port 9000 \
  --with-setup \
  > logs/apis.log 2>&1 &
PID_APIS=$!

echo "🌍 [2/4] Starting AppWorld environment on port 8000 (with setup)..."
"$APPWORLD_BIN" serve environment \
  --port 8000 \
  --with-setup \
  > logs/environment.log 2>&1 &
PID_ENV=$!

echo "🔌 [3/4] Starting MCP server on port 10000 (with setup)..."
"$APPWORLD_BIN" serve mcp \
  --port 10000 \
  --with-setup \
  > logs/mcp.log 2>&1 &
PID_MCP=$!

sleep 3

echo "🤖 [4/4] Starting Green Agent HTTP server..."


python - << 'EOF'
from fastapi import FastAPI
import uvicorn
import tomllib
from pathlib import Path
import os

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/.well-known/agent-card.json")
async def agent_card():
    
    card_path = Path("/Users/liaokeyue/agentbeats-new/scenarios/appworld/green_agent/green_agent_card.toml")
    with card_path.open("rb") as f:
        data = tomllib.load(f)
    return data

if __name__ == "__main__":
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("AGENT_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
EOF

AGENT_EXIT_CODE=$?

echo "🛑 Green agent exited with code $AGENT_EXIT_CODE. Cleaning up AppWorld servers..."
kill $PID_APIS $PID_ENV $PID_MCP 2>/dev/null || true

exit $AGENT_EXIT_CODE
