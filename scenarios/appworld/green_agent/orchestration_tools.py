import agentbeats as ab  
import requests  
import json  
import time  
import subprocess
import os
  
# AppWorld endpoints  
APPWORLD_ENV_SERVER = "http://127.0.0.1:8000"    
APPWORLD_API_SERVER = "http://127.0.0.1:9000"  
  
   
@ab.tool  
def setup_appworld_environment(task_id: str) -> str:  
    """Initialize AppWorld environment and return task info as JSON."""  
    
    battle_id = ab.get_battle_id()  
    experiment_name = f"{battle_id}_{task_id}"  
      
    init_response = requests.post(  
        f"{APPWORLD_ENV_SERVER}/initialize",  
        json={  
            "task_id": task_id,  
            "experiment_name": experiment_name,  
            "remote_apis_url": APPWORLD_API_SERVER,  
            "raise_on_failure": False,  
            "max_interactions": 100,  
            "show_api_response_schemas": False,  
        },  
        timeout=60,  
    )  
    init_response.raise_for_status()  
    result = init_response.json()  
      
    output = result["output"]  
      
    task_info = {  
        "task_id": task_id,  
        "experiment_name": experiment_name,  
        "instruction": output.get("instruction", ""),  
        "supervisor": output.get("supervisor", {}),  
        "datetime": output.get("datetime", ""),  
    }  
      
    return json.dumps(task_info)  
  
  

    
@ab.tool  
def build_task_message(  
    task_info_json: str,   
    predicted_apis_json: str,  
    battle_id: str  
) -> str:  
    task_info = json.loads(task_info_json)  
    predicted_apis_data = json.loads(predicted_apis_json)  
    predicted_apis = predicted_apis_data["predicted_apis"]  
      
    
    predicted_apis_formatted = [api.replace(".", "__") for api in predicted_apis]  
      
      
    message = f"""  
**Task ID**: {task_info['task_id']}  
**Experiment**: {task_info['experiment_name']}  
**Instruction**: {task_info['instruction']}  
  
**Supervisor Information**:  
- Name: {task_info['supervisor']['first_name']} {task_info['supervisor']['last_name']}  
- Email: {task_info['supervisor']['email']}  
- Phone: {task_info['supervisor']['phone_number']}  
  
**Current DateTime**: {task_info['datetime']}  
  
**Available APIs for this task**:  
{chr(10).join(f"- {api}" for api in predicted_apis_formatted)}  
  
**Battle Context**:  
- Battle ID: {battle_id}  
- Task ID: {task_info['task_id']}  
"""  
    return message

  
@ab.tool  
def check_task_completed(task_id: str) -> str:  
    """Check if Blue Agent has completed the task."""  
    response = requests.post(  
        f"{APPWORLD_ENV_SERVER}/task_completed",  
        json={"task_id": task_id},  
        timeout=60  
    )  
    response.raise_for_status()  
    result = response.json()  
      
    return json.dumps({  
        "task_completed": result["output"],  # Boolean  
        "task_id": task_id  
    })


  

@ab.tool    
def save_appworld_state(task_id: str) -> str:    
    """Save AppWorld database state and logs before evaluation.""" 

  

    response = requests.post(    
        f"{APPWORLD_ENV_SERVER}/save",    
        json={"task_id": task_id},    
        timeout=60,    
    )    
    response.raise_for_status()    
    return json.dumps({"status": "saved", "task_id": task_id})
  

@ab.tool    
def run_appworld_evaluator(task_id: str) -> str:    
    """Run AppWorld evaluation and return JSON results."""    
    response = requests.post(    
        f"{APPWORLD_ENV_SERVER}/evaluate",    
        json={  
            "task_id": task_id,  
            "suppress_errors": True,  # Don't raise on test failures  
            "report": False,  # Get dict format, not text report  
        },    
        timeout=60,    
    )    
    response.raise_for_status()    
    result = response.json()    
    return json.dumps(result["output"], indent=2)
  











  
 
@ab.tool  
def close_appworld_environment(task_id: str) -> str:  
    """Close the AppWorld environment for the task."""  
    response = requests.post(  
        f"{APPWORLD_ENV_SERVER}/close",  
        json={"task_id": task_id},  
        timeout=60,  
    )  
    response.raise_for_status()  
    return json.dumps({"status": "closed", "task_id": task_id})

@ab.tool    
def predict_required_apis(task_id: str) -> str:    
    """Predict required APIs for the task using subprocess."""    
       
    conda_env_python = os.path.expanduser("~/miniconda3/envs/appworld/bin/python")    
    appworld_root = os.path.expanduser("~/appworld")   
      
    
    if not os.path.exists(conda_env_python):    
        return json.dumps({    
            "error": f"Python interpreter not found at {conda_env_python}",    
            "is_error": True    
        })  
      
    if not os.path.exists(appworld_root):  
        return json.dumps({  
            "error": f"AppWorld root directory not found at {appworld_root}",  
            "is_error": True  
        })  
        
    
    script_content = """    
import sys    
import json    
from appworld.task import Task    
from appworld_agents.code.simplified.api_predictor import APIPredictor    
    
try:    
    input_data = json.loads(sys.stdin.read())    
    task_id = input_data["task_id"]    
    mode = input_data.get("mode", "predicted")    
      
    
    task = Task.load(  
        task_id=task_id,   
        load_ground_truth=False,   
         
    )
    model_config = {    
        "client_name": "openai",  
        "api_type": "chat_completions",  
        "name": "gpt-5-2025-08-07",    
        "temperature": 1,  
        "api_key_env_name": "OPENAI_API_KEY",  
        "cost_per_token": {    
            "input_cache_hit": 5e-06,    
            "input_cache_miss": 5e-06,    
            "input_cache_write": 0.0,    
            "output": 1.5e-05    
        },  
        "retry_after_n_seconds": 15,  
        "use_cache": False,  
        "max_retries": 100  
    }    
         
      
    api_predictor = APIPredictor(  
        model_config=model_config,  
        prompt_file_path="experiments/prompts/api_predictor.txt",  
        demo_task_ids=["82e2fac_1", "29caf6f_1", "d0b1f43_1"],  
        max_predicted_apis=20,  
        mode=mode  
    )  
      
    predicted_apis, _ = api_predictor.predict(task)  
      
    print(json.dumps({  
        "success": True,  
        "predicted_apis": predicted_apis,  
        "message": f"Predicted {len(predicted_apis)} APIs"  
    }))  
      
except Exception as e:  
    import traceback  
    print(json.dumps({  
        "success": False,  
        "error": str(e),  
        "traceback": traceback.format_exc()  
    }))  
    sys.exit(1)  
"""
    input_data = json.dumps({  
        "task_id": task_id,  
        "mode": "predicted"  
    })  
      
    try:  
        result = subprocess.run(  
            [conda_env_python, "-c", script_content],  
            input=input_data,  
            capture_output=True,  
            text=True,  
            timeout=60,  
            cwd=appworld_root
           
        )  
          
        if result.returncode != 0:  
            return json.dumps({  
                "error": f"Subprocess failed with return code {result.returncode}",  
                "stderr": result.stderr,  
                "stdout": result.stdout,  
                "is_error": True  
            })  
          
        output = json.loads(result.stdout)  
          
        if output.get("success"):  
            return json.dumps({  
                "predicted_apis": output["predicted_apis"],  
                "message": output.get("message", "")  
            })  
        else:  
            return json.dumps({  
                "error": output.get("error", "Unknown error"),  
                "traceback": output.get("traceback", ""),  
                "is_error": True  
            })  
                
    except subprocess.TimeoutExpired:  
        return json.dumps({  
            "error": "API predictor subprocess timed out",  
            "is_error": True  
        })  
    except json.JSONDecodeError as e:  
        return json.dumps({  
            "error": f"Failed to parse subprocess output: {result.stdout}",  
            "stderr": result.stderr,  
            "is_error": True  
        })  
    except Exception as e:  
        return json.dumps({  
            "error": f"Failed to run API predictor: {str(e)}",  
            "is_error": True  
        })





@ab.tool    
def analyze_mcp_trajectory(battle_id: str, task_id: str) -> str:    
    """Analyze MCP calling trajectory from agentbeats logs and extract metrics."""    
      
    log_path = os.path.expanduser(    
        "~/agentbeats-new/scenarios/appworld/logs/mcp_tool_calls.jsonl"    
    )    
      
    if not os.path.exists(log_path):    
        return json.dumps({    
            "error": f"MCP tool calls log not found at {log_path}",    
            "is_error": True    
        })    
      
    try:    
        trajectory_data = []    
        with open(log_path, 'r') as f:    
            for line in f:    
                if line.strip():    
                    trajectory_data.append(json.loads(line))    
          
        if not trajectory_data:    
            return json.dumps({    
                "error": "No MCP tool calls found in log",    
                "is_error": True    
            })    
          
        from datetime import datetime    
          
        # Check both success field and result.response.is_error  
        def is_call_successful(call):  
            if not call.get("success", True):  
                return False  
            result = call.get("result", {})  
            if isinstance(result, dict):  
                response = result.get("response", {})  
                if isinstance(response, dict) and response.get("is_error"):  
                    return False  
            return True  
          
        total_calls = len(trajectory_data)    
        successful_calls = sum(1 for call in trajectory_data if is_call_successful(call))  
        failed_calls = total_calls - successful_calls    
          
        durations = [call.get("duration_ms", 0) for call in trajectory_data]    
        avg_duration_ms = sum(durations) / len(durations) if durations else 0    
          
        if trajectory_data:    
            first_time = datetime.fromisoformat(    
                trajectory_data[0]["timestamp"].replace('Z', '+00:00')    
            )    
            last_time = datetime.fromisoformat(    
                trajectory_data[-1]["timestamp"].replace('Z', '+00:00')    
            )    
            total_duration_seconds = (last_time - first_time).total_seconds()    
            calls_per_minute = (total_calls / total_duration_seconds * 60) if total_duration_seconds > 0 else 0    
        else:    
            total_duration_seconds = 0    
            calls_per_minute = 0    
          
        tool_usage = {}    
        for call in trajectory_data:    
            tool_name = call.get("tool_name", "")    
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1    
          
        retry_count = 0    
        for i in range(1, len(trajectory_data)):    
            curr = trajectory_data[i]    
            prev = trajectory_data[i-1]    
            if (curr.get("tool_name") == prev.get("tool_name") and    
                not is_call_successful(prev) and is_call_successful(curr)):    
                retry_count += 1    
          
        pagination_sequences = 0    
        i = 0    
        while i < len(trajectory_data) - 1:    
            current_tool = trajectory_data[i].get("tool_name", "")    
            if "library" in current_tool or "list" in current_tool or "search" in current_tool:    
                sequence_length = 1    
                j = i + 1    
                while j < len(trajectory_data) and trajectory_data[j].get("tool_name") == current_tool:    
                    sequence_length += 1    
                    j += 1    
                if sequence_length >= 2:    
                    pagination_sequences += 1    
                    i = j    
                    continue    
            i += 1    
          
        metrics = {    
            "battle_id": battle_id,    
            "task_id": task_id,    
            "total_calls": total_calls,    
            "successful_calls": successful_calls,    
            "failed_calls": failed_calls,    
            "error_rate": round((failed_calls / total_calls * 100), 2) if total_calls > 0 else 0,    
            "avg_duration_ms": round(avg_duration_ms, 2),    
            "total_duration_seconds": round(total_duration_seconds, 2),    
            "calls_per_minute": round(calls_per_minute, 2),    
            "unique_tools": len(tool_usage),    
            "retry_count": retry_count,    
            "pagination_sequences": pagination_sequences,    
            "tool_usage": tool_usage    
        }    
          
        return json.dumps(metrics, indent=2)    
          
    except Exception as e:    
        import traceback    
        return json.dumps({    
            "error": f"Failed to analyze MCP trajectory: {str(e)}",    
            "traceback": traceback.format_exc(),    
            "is_error": True    
        })




@ab.tool  
def get_complete_task_metrics(battle_id: str, task_id: str) -> str:  
    """Get complete task metrics including evaluation and trajectory analysis."""  
      
    try:  
        # Print to terminal for visibility  
        print(f"[get_complete_task_metrics] Starting metrics collection for task {task_id}")  
        # 1. Run AppWorld evaluation  
        evaluation_json = run_appworld_evaluator(task_id)  
        evaluation = json.loads(evaluation_json)  
          
        # 2. Analyze MCP trajectory  
        trajectory_json = analyze_mcp_trajectory(battle_id, task_id)  
        trajectory = json.loads(trajectory_json)  
          
        # 3. Check for errors  
        if evaluation.get("is_error") or trajectory.get("is_error"):  
            return json.dumps({  
                "error": "Failed to get complete metrics",  
                "evaluation_error": evaluation.get("error"),  
                "trajectory_error": trajectory.get("error"),  
                "is_error": True  
            })  
          
        # 4. Combine into demo-friendly format  
        complete_metrics = {  
            "task_id": task_id,  
            "battle_id": battle_id,  
              
            # Evaluation results  
            "success": evaluation.get("success", False),  
            "tests_passed": len(evaluation.get("passes", [])),  
            "tests_failed": len(evaluation.get("failures", [])),  
            "total_tests": len(evaluation.get("passes", [])) + len(evaluation.get("failures", [])),    
              
            # Execution efficiency  
            "total_api_calls": trajectory.get("total_calls", 0),  
            "error_rate": trajectory.get("error_rate", 0),  
            "execution_time_seconds": trajectory.get("total_duration_seconds", 0),  
            "retry_count": trajectory.get("retry_count", 0),  
              
            # Optional: detailed breakdown  
            "details": {  
                "evaluation": evaluation,  
                "trajectory": trajectory  
            }  
        }  


        # Print complete metrics directly to terminal  
        import sys  
        print("\n=== COMPLETE TASK METRICS ===", file=sys.__stdout__, flush=True)  
        print(json.dumps(complete_metrics, indent=2), file=sys.__stdout__, flush=True)  
        print("=" * 30, file=sys.__stdout__, flush=True) 
          
        return json.dumps(complete_metrics, indent=2)  
    
          
    except Exception as e:  
        import traceback  

          
        return json.dumps({  
            "error": f"Failed to get complete task metrics: {str(e)}",  
            "traceback": traceback.format_exc(),  
            "is_error": True  
        })