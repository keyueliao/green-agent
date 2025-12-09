import json
import inspect
import importlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import tomllib

app = FastAPI()

# =========================================================
# 1. Load agent card (TOML → JSON)
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
CARD_PATH = BASE_DIR / "green_agent_card.toml"
TOOLS_PATH = BASE_DIR / "orchestration_tools.py"

with CARD_PATH.open("rb") as f:
    agent_card = tomllib.load(f)


@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    """Return the agent-card as JSON (required by AgentBeats platform)."""
    return JSONResponse(agent_card)


# =========================================================
# 2. Import all tools from orchestration_tools.py
# =========================================================

module = importlib.import_module("scenarios.appworld.green_agent.orchestration_tools")

def get_all_tools():
    """Return dict {tool_name: python_function} for all callable tools."""
    tools = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and not name.startswith("_"):
            tools[name] = obj
    return tools

TOOLS = get_all_tools()


# =========================================================
# 3. Generate dynamic tool endpoints
# =========================================================

@app.post("/tools/{tool_name}")
async def run_tool(tool_name: str, payload: dict):
    """
    Called by the AgentBeats platform when LLM wants to execute a tool.
    Payload is a dict of arguments that will be passed directly to the function.
    Returns the result (must be JSON-serializable).
    """
    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

    func = TOOLS[tool_name]

    try:
        result = func(**payload)
        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# 4. Health check
# =========================================================

@app.get("/health")
async def health():
    return {"status": "ok", "tools_loaded": list(TOOLS.keys())}
