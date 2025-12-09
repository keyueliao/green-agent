export PYTHONPATH=/Users/liaokeyue/agentbeats-new

python - << 'EOF'
from fastapi import FastAPI
import uvicorn
import tomllib
from pathlib import Path
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
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

