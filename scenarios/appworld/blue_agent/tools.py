import json  
import logging  
import os  
import subprocess  
from datetime import datetime  
from pathlib import Path  
from typing import Optional  
import agentbeats as ab


 
logger = logging.getLogger(__name__)  
  
  
class MCPToolLogger:  
    """Logger class for recording MCP tool calls"""  
      
    def __init__(self, log_dir: str = "./logs"):  
        self.log_dir = Path(log_dir)  
        self.log_dir.mkdir(exist_ok=True)  
        self.log_file = self.log_dir / "mcp_tool_calls.jsonl"  
      
    def log_call(  
        self,  
        tool_name: str,  
        arguments: dict,  
        result: dict | None,  
        success: bool,  
        error: Optional[str] = None,  
        duration_ms: Optional[float] = None  
    ) -> None:  
        """Record a single MCP tool call in JSONL format"""  
        log_entry = {  
            "timestamp": datetime.now().isoformat(),  
            "tool_name": tool_name,  
            "arguments": arguments,  
            "result": result if success else None,  
            "success": success,  
            "error": error,  
            "duration_ms": duration_ms  
        }  
          
        with open(self.log_file, "a", encoding="utf-8") as f:  
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")  
  
  
# Global logger instance
mcp_logger = MCPToolLogger()  


















@ab.tool 
def call_appworld_mcp_tool(tool_name: str, arguments: Optional[str] = None) -> str:  
    """Call an AppWorld MCP tool via subprocess inside an isolated conda environment.  
      
    Args:  
        tool_name: Name of the AppWorld MCP tool to execute  
        arguments: Optional JSON string of arguments, e.g. '{"username": "user"}'  
      
    Returns:  
        A JSON string containing either the result or an error message. 
    """  
    import time 
    import sys 
    start_time = time.time() 
    print(f"\n=== CALLING MCP TOOL: {tool_name} ===", file=sys.__stdout__, flush=True)  
    print(f"Arguments: {arguments}", file=sys.__stdout__, flush=True)  
      
    # Log: starting tool call  
    logger.info(f"Starting MCP tool call: {tool_name}")  
      
    conda_env_python = os.path.expanduser("~/miniconda3/envs/appworld/bin/python")  
      
    if not os.path.exists(conda_env_python):  
        error_msg = f"Python interpreter not found at {conda_env_python}"  
        logger.error(error_msg)  
        mcp_logger.log_call(tool_name, {}, None, False, error_msg)  
        return json.dumps({"error": error_msg, "is_error": True})  
    
    
    # Parse JSON argument string into dict  
    if arguments is None:  
        args_dict = {}  
    else:  
        try:  
            args_dict = json.loads(arguments)  
            logger.debug(f"Parsed arguments: {args_dict}")  
        except json.JSONDecodeError as e:  
            error_msg = f"Invalid JSON in arguments: {arguments}"  
            logger.error(f"{error_msg} - {str(e)}")  
            mcp_logger.log_call(tool_name, {}, None, False, error_msg)  
            return json.dumps({"error": error_msg, "is_error": True})  
      
    # Script executed inside subprocess  
    script_content = """  
import sys  
import json  
from appworld.serve._mcp import HTTPMCPClient  
  
input_data = json.loads(sys.stdin.read())  
tool_name = input_data["tool_name"]  
arguments = input_data.get("arguments", {})  
  
try:  
    with HTTPMCPClient(remote_mcp_url="http://127.0.0.1:10000") as mcp:  
        result = mcp.call_tool(tool_name, arguments=arguments)  
        print(json.dumps({"success": True, "result": result}))  
except ConnectionError as e:  
    print(json.dumps({"success": False, "error": f"MCP server connection failed: {str(e)}", "is_error": True}))  
except Exception as e:  
    print(json.dumps({"success": False, "error": str(e), "is_error": True}))  
"""    
      
    # Encode input dictionary 
    input_data = json.dumps({  
        "tool_name": tool_name,  
        "arguments": args_dict  
    })  
      
    # Log: preparing subprocess 
    logger.debug(f"Executing subprocess with input: {input_data}")  
      
    # Set subprocess environment variables  
    env = os.environ.copy()  
    env['PATH'] = "/Users/liaokeyue/miniconda3/envs/appworld/bin:" + env.get('PATH', '')  
    env['CONDA_DEFAULT_ENV'] = 'appworld'  
      
    # Run subprocess  
    try:  
        result = subprocess.run(  
            [conda_env_python, "-c", script_content],  
            input=input_data,  
            capture_output=True,  
            text=True,  
            env=env,  
            timeout=120  
        )  
    except subprocess.TimeoutExpired:  
        error_msg = "Subprocess timed out after 120 seconds"  
        logger.error(error_msg)  
        duration_ms = (time.time() - start_time) * 1000  
        mcp_logger.log_call(tool_name, args_dict, None, False, error_msg, duration_ms)  
        return json.dumps({"error": error_msg, "is_error": True})  
      
    # Log: subprocess finished  
    logger.debug(f"Subprocess returncode: {result.returncode}")  
    if result.stdout: 
        print(f"STDOUT: {result.stdout}", file=sys.__stdout__, flush=True) 
        logger.debug(f"Subprocess stdout: {result.stdout}")  
    if result.stderr:  
        print(f"STDERR: {result.stderr}", file=sys.__stdout__, flush=True)
        logger.warning(f"Subprocess stderr: {result.stderr}")  
      
    if result.returncode != 0:  
        error_msg = f"Subprocess failed: {result.stderr}"  
        logger.error(error_msg)  
        duration_ms = (time.time() - start_time) * 1000  
        mcp_logger.log_call(tool_name, args_dict, None, False, error_msg, duration_ms)  
        return json.dumps({"error": error_msg, "is_error": True})  
      
    # Parse JSON output
    try:  
        output = json.loads(result.stdout.strip())  
        duration_ms = (time.time() - start_time) * 1000  
          
        if output.get("success"):  
            logger.info(f"MCP tool call succeeded: {tool_name} (took {duration_ms:.2f}ms)")  
            logger.debug(f"Result: {output['result']}")  
            mcp_logger.log_call(tool_name, args_dict, output["result"], True, None, duration_ms)  
            # Print success to terminal
            print(f"\n=== MCP TOOL SUCCESS: {tool_name} ===", file=sys.__stdout__, flush=True)  
            print(f"Duration: {duration_ms:.2f}ms", file=sys.__stdout__, flush=True)  
            print(f"Result: {json.dumps(output['result'], indent=2)}", file=sys.__stdout__, flush=True)  
            print("=" * 50, file=sys.__stdout__, flush=True)


            return json.dumps(output["result"])  
            
        
            
        else:  
            error_msg = output.get("error", "Unknown error")  
            logger.error(f"MCP tool call failed: {error_msg}")  
            mcp_logger.log_call(tool_name, args_dict, None, False, error_msg, duration_ms)  
            return json.dumps({"error": error_msg, "is_error": True})  
    except json.JSONDecodeError as e:  
        error_msg = f"Failed to parse subprocess output: {result.stdout}"  
        logger.error(f"{error_msg} - {str(e)}")  
        duration_ms = (time.time() - start_time) * 1000  
        mcp_logger.log_call(tool_name, args_dict, None, False, error_msg, duration_ms)  
        return json.dumps({"error": error_msg, "is_error": True})  
  
