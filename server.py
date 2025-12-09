from fastapi import FastAPI
from pathlib import Path
import tomllib

app = FastAPI()

CARD_PATH = Path(__file__).parent / "green_agent_card.toml"

@app.get("/")
async def root():
    return {"status": "green-agent-ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/.well-known/agent-card.json")
async def agent_card():
    with CARD_PATH.open("rb") as f:
        card = tomllib.load(f)
    return card

