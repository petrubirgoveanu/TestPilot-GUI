"""Unit tests for reporting helpers (pure, no browser)."""
import os
import json
import tempfile
import shutil

import pytest

from testpilot.reporting.run_manifest import new_run_id, ensure_artifact_dir, write_manifest


@pytest.mark.unit
def test_run_id_is_unique():
    a = new_run_id()
    b = new_run_id()
    assert a != b
    # basic format sanity
    assert a.endswith("Z")
    assert len(a) > 15


@pytest.mark.unit
def test_artifact_directory_is_under_artifacts_root(tmp_path):
    # Use a temp root to not pollute real artifacts/
    root = str(tmp_path / "artifacts")
    run_id = "testrun123"
    d = ensure_artifact_dir(run_id, root=root)
    assert os.path.isdir(d)
    assert d.startswith(os.path.abspath(root))
    assert run_id in d


@pytest.mark.unit
def test_write_manifest_creates_json(tmp_path):
    root = str(tmp_path / "artifacts")
    run_id = new_run_id()
    data = {"run_id": run_id, "status": "passed", "mutation_id": "baseline"}
    path = write_manifest(run_id, data, root=root)
    assert os.path.exists(path)
    assert path.endswith("run_manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["run_id"] == run_id
    assert loaded["status"] == "passed"
