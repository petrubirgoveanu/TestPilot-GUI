"""Unit tests verifying that LangSmith configuration is optional and the app runs without it (M7)."""
import os
import pytest
import importlib
from unittest.mock import patch

from testpilot.ui import services

@pytest.fixture
def mock_run_journey():
    with patch("testpilot.workflow.graph.run_journey") as mock:
        mock.return_value = {
            "run_id": "test_langsmith_run",
            "status": "passed",
            "manifest_path": "path/to/manifest"
        }
        yield mock

@pytest.fixture
def mock_write_manifest():
    with patch("testpilot.workflow.graph.write_manifest") as mock:
        yield mock

@pytest.fixture
def mock_ensure_dir():
    with patch("testpilot.workflow.graph.ensure_artifact_dir") as mock:
        yield mock


@pytest.mark.unit
def test_app_runs_when_langsmith_env_vars_are_absent(mock_run_journey, mock_write_manifest, mock_ensure_dir):
    """Test that the application runs successfully when LANGSMITH_* env vars are absent."""
    original_env = {}
    for key in [
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGCHAIN_PROJECT",
    ]:
        if key in os.environ:
            original_env[key] = os.environ[key]
            del os.environ[key]

    try:
        # Run a regression using services wrapper (which runs the graph)
        result = services.run_original_regression("baseline", headless=True)
        assert result["status"] == "passed"
        assert "Passed" in result["timeline"]
    finally:
        # Restore environment variables
        for key, val in original_env.items():
            os.environ[key] = val


@pytest.mark.unit
def test_app_runs_when_langsmith_tracing_is_false(mock_run_journey, mock_write_manifest, mock_ensure_dir):
    """Test that the application runs successfully when LANGSMITH_TRACING is set to false."""
    original_env = {}
    for key in ["LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"]:
        if key in os.environ:
            original_env[key] = os.environ[key]

    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    try:
        result = services.run_original_regression("baseline", headless=True)
        assert result["status"] == "passed"
    finally:
        for key in ["LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"]:
            if key in original_env:
                os.environ[key] = original_env[key]
            elif key in os.environ:
                del os.environ[key]


@pytest.mark.unit
def test_langsmith_configuration_is_optional():
    """Assert that LangSmith environment variables are completely optional and don't cause config issues."""
    import testpilot.config
    importlib.reload(testpilot.config)

    assert hasattr(testpilot.config, "LANGSMITH_TRACING")
    assert hasattr(testpilot.config, "LANGSMITH_API_KEY")
    assert hasattr(testpilot.config, "LANGSMITH_PROJECT")


@pytest.mark.unit
def test_browser_artifacts_do_not_depend_on_langsmith(mock_run_journey, mock_write_manifest, mock_ensure_dir):
    """Ensure browser artifacts/manifests are written properly regardless of LangSmith environment variables."""
    original_env = {}
    for key in ["LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"]:
        if key in os.environ:
            original_env[key] = os.environ[key]
            del os.environ[key]

    try:
        result = services.run_original_regression("baseline", headless=True)
        assert result["status"] == "passed"
        # Confirm ensure_artifact_dir and write_manifest were called
        assert mock_ensure_dir.call_count >= 1
        assert mock_write_manifest.call_count >= 1
    finally:
        for key, val in original_env.items():
            os.environ[key] = val
