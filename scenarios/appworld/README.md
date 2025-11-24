
# **AppWorld Blue & Green Agents**

This repository contains custom **Blue Agent** (task executor) and **Green Agent** (task evaluator) for the AppWorld environment.
All custom implementation lives under:

```
scenarios/appworld/
```

---

## **📁 Project Structure**

```
scenarios/appworld/
├── blue_agent/
│   ├── tools.py                # Blue Agent tool-call logic
│   └── blue_agent_card.toml    # Model + tool config
│
├── green_agent/
│   ├── orchestration_tools.py  # Green Agent evaluation logic
│   ├── green_agent_card.toml   # Model config for evaluator
│   └── __init__.py
│
├── logs/                       # Execution logs (generated at runtime)
└── scenario.toml               # Scenario definition (tasks, agents, flow)
```

---

# **🚀 How to Run the System**

### **1. Start AppWorld API services**

```bash
appworld serve apis --port 9000
appworld serve environment --port 8000
```

### **2. Start AgentBeats backend**

```bash
agentbeats run_backend --backend_port 9002 --mcp_port 9001
```

### **3. Start AppWorld MCP server (Blue Agent tools)**

```bash
appworld serve mcp http \
  --remote-apis-url http://localhost:9000 \
  --app-names supervisor,amazon,spotify,gmail,phone,venmo,splitwise,simple_note,todoist,file_system \
  --port 10000
```

### **4. Run the full scenario (Blue executes → Green evaluates)**

```bash
agentbeats run_scenario scenarios/appworld --backend http://localhost:9002
```

---

# **📊 Output & Logs**

Execution logs and tool-calls are written to:

```
scenarios/appworld/logs/
```

The Green Agent reads these logs during evaluation.

---

# **🛠 Modify Components**

* **Blue Agent**
  `scenarios/appworld/blue_agent/tools.py`
  `scenarios/appworld/blue_agent/blue_agent_card.toml`

* **Green Agent**
  `scenarios/appworld/green_agent/orchestration_tools.py`
  `scenarios/appworld/green_agent/green_agent_card.toml`

* **Tasks / scenario configuration**
  `scenarios/appworld/scenario.toml`

---

# **✔ Summary**

* Blue Agent performs multi-app tasks in AppWorld
* Green Agent evaluates correctness and tool-call quality
* All components are fully runnable using the commands above
* Implementation is fully self-contained under `scenarios/appworld/`

---
