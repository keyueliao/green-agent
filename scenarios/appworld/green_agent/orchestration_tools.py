import agentbeats as ab
import requests
import json

# AppWorld endpoints
APPWORLD_ENV_SERVER = "http://127.0.0.1:8000"
APPWORLD_MCP_SERVER = "http://127.0.0.1:10000"
APPWORLD_API_SERVER = "http://127.0.0.1:9000"



# ─────────────────────────────────────────────
# 1️⃣  Environment setup
# ─────────────────────────────────────────────
@ab.tool
def setup_appworld_environment(task_id: str) -> str:
    """Initialize AppWorld environment and return task info + MCP URL as JSON."""
    battle_id = ab.get_battle_id()
    experiment_name = f"{battle_id}_{task_id}"

    init_response = requests.post(
        f"{APPWORLD_ENV_SERVER}/initialize",
        json={"task_id": task_id, "experiment_name": experiment_name},
        timeout=60,
    )
    init_response.raise_for_status()
    task_info = init_response.json()["output"]

    result = {
        "task_id": task_info["task_id"],
        "instruction": task_info["instruction"],
        "supervisor": task_info["supervisor"],
        "datetime": task_info["datetime"],
        "mcp_server": APPWORLD_MCP_SERVER,  # <── tell Blue where to connect
    }
    return json.dumps(result)


# ─────────────────────────────────────────────
# 2️⃣  Task message builder
# ─────────────────────────────────────────────
@ab.tool
def build_task_message(task_info_json: str, battle_id: str) -> str:
    """Build task assignment message for Blue Agent (uses AppWorld MCP)."""
    task_info = json.loads(task_info_json)
    task_id = task_info["task_id"]

    message = f"""
You are the Blue Agent solving an AppWorld task.

TASK INFO:
- Supervisor: {task_info['supervisor']['first_name']} {task_info['supervisor']['last_name']} ({task_info['supervisor']['email']})
- DateTime: {task_info['datetime']}
- Instruction: {task_info['instruction']}

MCP SERVER:
Connect to: {task_info['mcp_server']}

AVAILABLE TOOLS (from MCP):
- apis.api_docs.show_app_descriptions()
- apis.api_docs.show_api_descriptions(app_name)
- apis.supervisor.show_profile()
- apis.supervisor.complete_task(answer=...)

PATTERN OF EXECUTION:
1. Use the listed MCP server to call AppWorld APIs.
2. Interact step-by-step until you finish the task.
3. When done, call:
   call_tool("apis.supervisor.complete_task", {{"answer": <final_answer>}})
   This marks task completion and triggers Green's evaluator.
4. Never attempt to run local code; use only tool calls.
5. Variables and session state persist inside AppWorld.

battle_id = {battle_id}
task_id   = {task_id}
"""
    return message


# ─────────────────────────────────────────────
# 3️⃣  Evaluation trigger
# ─────────────────────────────────────────────
@ab.tool
def run_appworld_evaluator(task_id: str, report: bool = False) -> str:
    """Run AppWorld evaluation and return JSON results."""
    response = requests.post(
        f"{APPWORLD_ENV_SERVER}/evaluate",
        json={
            "task_id": task_id,
            "suppress_errors": True,
            "report": report,
        },
        timeout=60,
    )
    response.raise_for_status()
    return json.dumps(response.json())
