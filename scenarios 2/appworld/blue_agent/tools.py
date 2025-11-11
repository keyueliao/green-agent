
from __future__ import annotations  
  
import json  
import requests  
  
import agentbeats as ab  
from pydantic import BaseModel, Field, ConfigDict  
  
  
class DockerAccessInfo(BaseModel):  
    """精确描述 Blue 连接 AppWorld 环境所需信息。"""  
    model_config = ConfigDict(extra="forbid")  
  
    remote_environment_url: str = Field(..., description="AppWorld 环境服务地址")  
    remote_docker: bool = Field(..., description="是否在 Docker 环境中运行")  
    experiment_name: str = Field(..., description="实验名称")  
    task_id: str = Field(..., description="任务 ID")  
  
  
class ExecuteCodePayload(BaseModel):  
    model_config = ConfigDict(extra="forbid")  
    code: str = Field(..., description="要执行的 Python 代码")  
    docker: DockerAccessInfo  
  
  
class CompletionCheckPayload(BaseModel):  
    model_config = ConfigDict(extra="forbid")  
    docker: DockerAccessInfo  
  
  
@ab.tool  
def connect_to_appworld_docker(docker: DockerAccessInfo) -> str:  
    """初始化远端 AppWorld 环境（/initialize）。"""  
    try:  
        payload = {  
            "task_id": docker.task_id,  
            "experiment_name": docker.experiment_name,  
            "remote_environment_url": docker.remote_environment_url,  
            "remote_docker": docker.remote_docker  # 关键修改  
        }  
        resp = requests.post(  
            f"{docker.remote_environment_url}/initialize",  
            json=payload,  
            timeout=15,  
        )  
        if resp.ok:  
            return json.dumps({  
                "ok": True,  
                "task_id": docker.task_id,  
                "message": "Connected to AppWorld environment"  
            }, ensure_ascii=False)  
        else:  
            return json.dumps({  
                "ok": False,  
                "task_id": docker.task_id,  
                "error": f"Initialize failed: {resp.status_code} {resp.text[:500]}"  
            }, ensure_ascii=False)  
    except Exception as e:  
        return json.dumps({"ok": False, "task_id": docker.task_id, "error": str(e)}, ensure_ascii=False)  
  
  
@ab.tool  
def execute_code_in_docker(payload: ExecuteCodePayload) -> str:  
    """在远端 AppWorld 中执行代码（/execute）。"""  
    try:  
        docker = payload.docker  
        req = {  
            "task_id": docker.task_id,  
            "code": payload.code,  
        }  
        resp = requests.post(  
            f"{docker.remote_environment_url}/execute",  
            json=req,  
            timeout=60,  
        )  
        if resp.ok:  
            data = {}  
            try:  
                data = resp.json()  
            except Exception:  
                pass  
            return json.dumps({  
                "ok": True,  
                "output": data.get("output", "") if isinstance(data, dict) else resp.text  
            }, ensure_ascii=False)  
        else:  
            return json.dumps({  
                "ok": False,  
                "error": f"Execution failed: {resp.status_code} {resp.text[:500]}"  
            }, ensure_ascii=False)  
    except Exception as e:  
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)  
  
  
@ab.tool  
def check_task_completion(payload: CompletionCheckPayload) -> str:  
    """查询任务是否完成（/task_completed）。"""  
    try:  
        docker = payload.docker  
        resp = requests.get(  
            f"{docker.remote_environment_url}/task_completed",  
            params={"task_id": docker.task_id},  
            timeout=10,  
        )  
        if resp.ok:  
            try:  
                data = resp.json()  
            except Exception:  
                return json.dumps({  
                    "ok": False,  
                    "completed": False,  
                    "error": "Non-JSON response from /task_completed",  
                    "raw": resp.text[:500]  
                }, ensure_ascii=False)  
            completed = bool(data.get("completed", False))  
            return json.dumps({"ok": True, "completed": completed, "detail": data}, ensure_ascii=False)  
        else:  
            return json.dumps({  
                "ok": False,  
                "completed": False,  
                "error": f"Status failed: {resp.status_code} {resp.text[:500]}"  
            }, ensure_ascii=False)  
    except Exception as e:  
        return json.dumps({"ok": False, "completed": False, "error": str(e)}, ensure_ascii=False)  
  
  
@ab.tool  
def close_appworld_session(docker: DockerAccessInfo) -> str:  
    """关闭 AppWorld 任务会话（/close）。"""  
    try:  
        resp = requests.post(  
            f"{docker.remote_environment_url}/close",  
            json={"task_id": docker.task_id},  
            timeout=10,  
        )  
        if resp.ok:  
            return json.dumps({  
                "ok": True,  
                "message": "Session closed successfully"  
            }, ensure_ascii=False)  
        else:  
            return json.dumps({  
                "ok": False,  
                "error": f"Close failed: {resp.status_code} {resp.text[:500]}"  
            }, ensure_ascii=False)  
    except Exception as e:  
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)