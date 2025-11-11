# scenarios/appworld/green_agent/tools.py
from __future__ import annotations

import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import requests
import agentbeats as ab

# =========================
# Globals & basic settings
# =========================
_APPWORLD_CONFIG: Dict[str, Any] = {}
_TASK_QUEUE: List[str] = []
_QUEUE_LOCK = threading.Lock()

HTTP_DEFAULT_TIMEOUT = 30
HTTP_RETRIES = 3
HTTP_BACKOFF_BASE = 0.8  # seconds, exponential backoff

RETRY_STATUS = {429, 500, 502, 503, 504}


def _log(line: str) -> None:
    """Structured stdout logging that actually shows up under Uvicorn."""
    print(line, file=sys.__stdout__, flush=True)


def _j(ok: bool, **kw) -> str:
    """Uniform JSON response encoder."""
    return json.dumps({"ok": ok, **kw}, ensure_ascii=False, indent=2 if ok else None)


def _maybe_json(obj: str | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    try:
        return json.loads(obj)
    except Exception:
        return {}


def _request_with_retry(
    method: str,
    url: str,
    *,
    timeout: int = HTTP_DEFAULT_TIMEOUT,
    max_retries: int = HTTP_RETRIES,
    backoff_base: float = HTTP_BACKOFF_BASE,
    **kwargs,
) -> requests.Response:
    """Retry on network errors & typical transient HTTP statuses."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
            if resp.status_code in RETRY_STATUS:
                _log(f"⚠️  HTTP {resp.status_code} @ {url} (attempt {attempt}/{max_retries})")
                raise requests.RequestException(f"Transient status {resp.status_code}")
            return resp
        except Exception as e:
            last_exc = e
            if attempt >= max_retries:
                break
            sleep_s = backoff_base * (2 ** (attempt - 1))
            time.sleep(sleep_s)
    assert last_exc is not None
    raise last_exc


def _require_fields(src: Dict[str, Any], fields: List[str]) -> Tuple[bool, str]:
    missing = [f for f in fields if f not in src or src[f] in (None, "")]
    if missing:
        return False, f"missing required fields: {', '.join(missing)}"
    return True, ""


@ab.tool
def setup_appworld_environment(appworld_root: str | None = None,
                               experiment_name: str = "default",
                               split: str = "dev",
                               scenario_filter: Optional[List[str]] = None,
                               *,
                               remote_environment_url: str = "http://127.0.0.1:8000",
                               remote_docker: bool = True,
                               max_tasks: int | None = None) -> str:
    """
    Initialize for Docker-based AppWorld (no host-side appworld import).
    - Reads task IDs from <APPWORLD_ROOT>/data/datasets/{split}.txt
    - Stores config in globals; returns JSON string.
    """
    global _APPWORLD_CONFIG, _TASK_QUEUE

    root = Path(appworld_root or os.environ.get("APPWORLD_ROOT", "/Users/liaokeyue/appworld")).expanduser()
    if not root.exists():
        return _j(False, msg=f"AppWorld root not found: {root}")

    # Make host-visible for debugging; container has its own APPWORLD_ROOT
    os.environ["APPWORLD_ROOT"] = str(root)

    task_file = root / "data" / "datasets" / f"{split}.txt"
    if not task_file.exists():
        return _j(False, msg=f"Task IDs file not found: {task_file}")

    try:
        task_ids = [line.strip() for line in task_file.read_text().splitlines() if line.strip()]
    except Exception as e:
        return _j(False, msg=f"Failed to read {task_file}: {e}")

    # Optional: filter by scenario prefixes or exact IDs
    if scenario_filter:
        keys = list(scenario_filter)
        task_ids = [tid for tid in task_ids if any(tid == k or tid.startswith(k) for k in keys)]

    # Optional: limit number of tasks
    if isinstance(max_tasks, int) and max_tasks > 0:
        task_ids = task_ids[:max_tasks]

    try:
        battle_id = ab.get_battle_id()
    except Exception:
        battle_id = "unknown-battle-id"

    _APPWORLD_CONFIG = {
        "root": str(root),
        "experiment_name": experiment_name,
        "split": split,
        "battle_id": battle_id,
        "remote_environment_url": remote_environment_url,
        "remote_docker": bool(remote_docker),
    }

    with _QUEUE_LOCK:
        _TASK_QUEUE = list(task_ids)

    _log(f"✅ AppWorld ready (docker mode) | split={split} | tasks={len(_TASK_QUEUE)} | exp={experiment_name}")
    return _j(True,
              root=str(root),
              experiment=experiment_name,
              split=split,
              battle_id=battle_id,
              remote_environment_url=remote_environment_url,
              remote_docker=bool(remote_docker),
              num_tasks=len(_TASK_QUEUE),
              example_ids=_TASK_QUEUE[:3])


@ab.tool
def get_next_appworld_task(api_docs_format: str = "function_calling") -> str:
    """
    Pop next task and fetch minimal safe metadata via the remote environment API.
    Returns JSON:
    {
      ok, msg?, task_id, instruction, supervisor,
      api_docs: null, app_descriptions: null,
      docker_access_info: { task_id, experiment_name, remote_environment_url, remote_docker }
    }
    """
    if not _APPWORLD_CONFIG:
        return _j(False, msg="config not set; call setup_appworld_environment first")

    with _QUEUE_LOCK:
        if not _TASK_QUEUE:
            return _j(False, msg="no more tasks")
        task_id = _TASK_QUEUE.pop(0)

    base = str(_APPWORLD_CONFIG["remote_environment_url"]).rstrip("/")
    url = f"{base}/tasks/{task_id}"
    _log(f"📋 Fetching task meta via HTTP: {url}")

    try:
        r = _request_with_retry("GET", url, timeout=HTTP_DEFAULT_TIMEOUT)
        out = r.json().get("output", {})
    except Exception as e:
        return _j(False, msg=f"failed to fetch task via HTTP: {e}")

    ok_fields, why = _require_fields(out, ["instruction", "supervisor"])
    if not ok_fields:
        return _j(False, msg=f"bad task metadata for {task_id}: {why}")

    docker_access_info = {
        "task_id": task_id,
        "experiment_name": _APPWORLD_CONFIG.get("experiment_name", "default"),
        "remote_environment_url": _APPWORLD_CONFIG.get("remote_environment_url", ""),
        "remote_docker": bool(_APPWORLD_CONFIG.get("remote_docker", True)),
    }

    return _j(True,
              task_id=task_id,
              instruction=out["instruction"],
              supervisor=out["supervisor"],
              api_docs=None,           # Blue fetches inside Docker
              app_descriptions=None,   # Blue fetches inside Docker
              docker_access_info=docker_access_info)


@ab.tool
def run_appworld_evaluator(task_id: str,
                           docker_info_json: str,
                           print_report: bool = True) -> str:
    """
    Evaluate a finished AppWorld task via the remote Docker environment API (HTTP).
    Returns JSON with pass/fail counts and a text report.
    """
    try:
        info = _maybe_json(docker_info_json)
        ok_info, why = _require_fields(info, ["remote_environment_url"])
        if not ok_info:
            return _j(False, task_id=task_id, msg=f"invalid docker_info_json: {why}")

        base = str(info["remote_environment_url"]).rstrip("/")
        exp = info.get("experiment_name") or _APPWORLD_CONFIG.get("experiment_name", "default")

        # 1) Initialize (idempotent); ensure remote_docker True for docker-served env
        init_body = {"task_id": task_id, "experiment_name": exp, "remote_docker": True}
        init_url = f"{base}/initialize"
        _log(f"🧪 Evaluator init: POST {init_url} body={init_body}")
        r_init = _request_with_retry("POST", init_url, json=init_body, timeout=60)

        if r_init.status_code != 200:
            return _j(False, task_id=task_id, msg=f"Initialization failed: {r_init.text}")

        # 2) Evaluate (pass task + experiment for stateless servers)
        eval_body = {"task_id": task_id, "experiment_name": exp, "suppress_errors": True}
        eval_url = f"{base}/evaluate"
        _log(f"✅ Run evaluate: POST {eval_url} body={eval_body}")
        r_eval = _request_with_retry("POST", eval_url, json=eval_body, timeout=180)

        if r_eval.status_code != 200:
            return _j(False, task_id=task_id, msg=f"Evaluation failed: {r_eval.text}")

        tracker = r_eval.json() if r_eval.headers.get("content-type", "").startswith("application/json") else {}
        passes = tracker.get("passes", []) or []
        failures = tracker.get("failures", []) or []
        tests_passed = len(passes)
        tests_total = tests_passed + len(failures)

        report = (
            f"Task {task_id} Evaluation Report\n"
            f"----------------------------------\n"
            f"Num Passed Tests : {tests_passed}\n"
            f"Num Failed Tests : {len(failures)}\n"
            f"Num Total  Tests : {tests_total}\n"
        )
        if print_report:
            _log(report)

        return _j(True,
                  task_id=task_id,
                  tests_passed=tests_passed,
                  tests_total=tests_total,
                  report=report,
                  passes=passes,
                  failures=failures)

    except Exception as e:
        return _j(False, task_id=task_id, msg=str(e))

    finally:
        # 3) Best-effort close (do not override main result)
        try:
            base = (info.get("remote_environment_url") if "info" in locals() else
                    _APPWORLD_CONFIG.get("remote_environment_url", ""))
            if base:
                close_url = f"{str(base).rstrip('/')}/close"
                _log(f"🧹 Close environment: POST {close_url}")
                requests.post(close_url, timeout=10)
        except Exception:
            pass
