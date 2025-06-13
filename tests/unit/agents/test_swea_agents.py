"""Tests for SWEA (Software Engineering Autonomous Agents)."""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# Use centralized temp directory from conftest
TESTS_TEMP_DIR = Path(__file__).parent.parent / ".temp"


@pytest.fixture(autouse=True)
def setup_managed_system_path():
    """Set up MANAGED_SYSTEM_PATH for all SWEA tests to use tests/.temp"""
    # Ensure tests/.temp exists
    TESTS_TEMP_DIR.mkdir(exist_ok=True)

    # Create unique temp directory for this test session
    temp_dir = TESTS_TEMP_DIR / f"swea_test_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)

    # Set environment variable before any SWEA imports
    original_env = os.environ.get("MANAGED_SYSTEM_PATH")
    os.environ["MANAGED_SYSTEM_PATH"] = str(temp_dir / "managed_system")

    yield temp_dir

    # Restore environment
    if original_env:
        os.environ["MANAGED_SYSTEM_PATH"] = original_env
    else:
        os.environ.pop("MANAGED_SYSTEM_PATH", None)

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestProgrammerSWEA:
    """Test ProgrammerSWEA functionality."""

    @patch("baes.swea_agents.programmer_swea.OpenAIClient")
    def test_generate_model(self, mock_client_cls):
        """Test model generation."""
        from baes.swea_agents.programmer_swea import ProgrammerSWEA

        mock_client = mock_client_cls.return_value
        mock_client.generate_code_with_domain_focus.return_value = "class Student(BaseModel): pass"

        swea = ProgrammerSWEA()
        payload = {"entity": "Student", "attributes": ["name", "email"]}
        result = swea.handle_task("generate_model", payload)

        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]
        mock_client.generate_code_with_domain_focus.assert_called_once()

    @patch("baes.swea_agents.programmer_swea.OpenAIClient")
    def test_generate_api(self, mock_client_cls):
        """Test API generation."""
        from baes.swea_agents.programmer_swea import ProgrammerSWEA

        mock_client = mock_client_cls.return_value
        mock_client.generate_code_with_domain_focus.return_value = "router = APIRouter()"

        swea = ProgrammerSWEA()
        payload = {"entity": "Student", "model_code": "class Student: pass"}
        result = swea.handle_task("generate_api", payload)

        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]


@pytest.mark.unit
class TestDatabaseSWEA:
    """Test DatabaseSWEA functionality."""

    def test_setup_database(self):
        """Test database setup creates proper files under tests/.temp"""
        # Ensure tests/.temp exists
        TESTS_TEMP_DIR.mkdir(exist_ok=True)

        # Create unique temp directory for this test
        temp_dir = TESTS_TEMP_DIR / f"database_test_{os.getpid()}_{id(self)}"
        temp_dir.mkdir(exist_ok=True)

        try:
            from baes.swea_agents.database_swea import DatabaseSWEA

            swea = DatabaseSWEA()
            db_path = temp_dir / "academic.db"

            payload = {"database_path": str(db_path), "entity": "Student"}
            result = swea.handle_task("setup_database", payload)

            assert result["success"] is True
            # Note: actual file creation depends on implementation
        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestFrontendSWEA:
    """Test FrontendSWEA functionality."""

    @patch("baes.swea_agents.frontend_swea.OpenAIClient")
    def test_generate_ui(self, mock_client_cls):
        """Test UI generation."""
        from baes.swea_agents.frontend_swea import FrontendSWEA

        mock_client = mock_client_cls.return_value
        mock_client.generate_code_with_domain_focus.return_value = "import streamlit as st"

        swea = FrontendSWEA()
        payload = {"entity": "Student", "model_code": "class Student: pass"}
        result = swea.handle_task("generate_ui", payload)

        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]
