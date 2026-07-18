"""Run manifest helpers for M2+."""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


def new_run_id() -> str:
    """Generate a simple unique run id based on UTC timestamp + microseconds."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def ensure_artifact_dir(run_id: str, root: str = "artifacts") -> str:
    """Create artifacts/<run_id>/ and return the absolute path."""
    d = os.path.abspath(os.path.join(root, run_id))
    os.makedirs(d, exist_ok=True)
    return d


def write_manifest(run_id: str, data: Dict[str, Any], root: str = "artifacts") -> str:
    """Write run_manifest.json under artifacts/<run_id>/ and return path."""
    d = ensure_artifact_dir(run_id, root=root)
    path = os.path.join(d, "run_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path
