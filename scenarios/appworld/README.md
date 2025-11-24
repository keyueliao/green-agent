

# **AppWorld Blue & Green Agents**

This repository contains custom **Blue Agent** (task executor) and **Green Agent** (task evaluator) built on top of the **AppWorld benchmark**.
All custom implementation lives under:

```
scenarios/appworld/
```

---

# **📦 External Dependency (Required)**

This project **depends on the AppWorld benchmark**.
Please install AppWorld following the official instructions:

👉 [https://appworld.dev/](https://appworld.dev/)

The Green Agent interacts with AppWorld by launching its servers through `subprocess`, so the `appworld` CLI must be available in your environment.

---

# **🔑 API Key Setup**

Before running the scenario, set your own OpenAI API key:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

No API keys are included in this repository.

---

# **📁 Project Structure**

```
scenarios/appworld/
├── blue_agent/
│   ├── tools.py                # Blue Agent tool-call logic (MCP)
│   └── blue_agent_card.toml    # Model + tool configuration
│
├── green_agent/
│   ├── orchestration_tools.py  # Green Agent evaluation logic
│   ├── green_agent_card.toml   # Model configuration for evaluator
│   └── __init__.py
│
├── logs/                       # Runtime logs (tool calls, trajectories)
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

### **4. Run the full scenario (Blue performs → Green evaluates)**

```bash
agentbeats run_scenario scenarios/appworld --backend http://localhost:9002
```

---

# **📊 Output & Logs**

AppWorld tool-call trajectories and evaluation logs are written to:

```
scenarios/appworld/logs/
```

The Green Agent reads these logs to evaluate:

* correctness (via AppWorld unit tests)
* tool-call efficiency
* retries / failed calls
* execution time
* unique tools used

---

# **🛠 Modifying Components**

**Blue Agent Source**

```
scenarios/appworld/blue_agent/tools.py  
scenarios/appworld/blue_agent/blue_agent_card.toml
```

**Green Agent Source**

```
scenarios/appworld/green_agent/orchestration_tools.py  
scenarios/appworld/green_agent/green_agent_card.toml
```

**Scenario Configuration**

```
scenarios/appworld/scenario.toml
```

---

# **✔ Summary**

* The Blue Agent executes AppWorld multi-app tasks via MCP tool calls
* The Green Agent evaluates correctness and analyzes the tool-call trajectory
* AppWorld must be installed separately (external dependency)
* All implementation is self-contained under `scenarios/appworld/`
* Run the system using the commands above

