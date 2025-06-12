"""Unit tests for ManagedSystemManager.

These tests validate the file-system helpers that scaffold the managed system
folder used by the BAE runtime.  They do **not** require any external services,
therefore they belong to the unit test suite.
"""

import os
import shutil
from pathlib import Path

import pytest

from baes.core.managed_system_manager import ManagedSystemManager
from config import Config


@pytest.mark.unit
class TestManagedSystemManager:
    """Test the ManagedSystemManager functionality."""

    def setup_method(self):
        """Set up a temporary MANAGED_SYSTEM_PATH for each test."""
        # Create a unique temporary directory and point the env-var to it
        self.temp_dir = Path.cwd() / "tests" / "managed_system_tmp"
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True)

        # Override environment variable
        self.original_env = os.environ.get("MANAGED_SYSTEM_PATH")
        os.environ["MANAGED_SYSTEM_PATH"] = str(self.temp_dir / "test_managed_system")

        # Instantiate manager using the overridden path
        self.manager = ManagedSystemManager()

    def teardown_method(self):
        """Restore environment and remove temporary directory."""
        if self.original_env:
            os.environ["MANAGED_SYSTEM_PATH"] = self.original_env
        else:
            os.environ.pop("MANAGED_SYSTEM_PATH", None)

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ---------------------------------------------------------------------
    #  Actual tests
    # ---------------------------------------------------------------------

    def test_managed_system_path_configuration(self):
        """Managed system path should be resolved under the temp directory."""
        managed_path = Config.get_managed_system_path()
        assert managed_path.exists()
        assert managed_path.name == "test_managed_system"
        # Should reside inside the temporary folder we created
        assert str(managed_path).startswith(str(self.temp_dir))

    def test_ensure_managed_system_structure(self):
        """ensure_managed_system_structure should create directories/files."""
        assert self.manager.ensure_managed_system_structure() is True

        required_dirs = [
            "app",
            "app/models",
            "app/routes",
            "app/database",
            "ui",
            "ui/pages",
            "tests",
        ]
        for d in required_dirs:
            assert (self.manager.managed_system_path / d).exists(), f"Missing dir {d}"

        required_files = [
            "requirements.txt",
            "README.md",
            ".gitignore",
            "setup_venv.sh",
            "start_servers.sh",
        ]
        for f in required_files:
            assert (self.manager.managed_system_path / f).exists(), f"Missing file {f}"

    def test_write_entity_artifact_model(self):
        """write_entity_artifact should persist model code to /app/models."""
        self.manager.ensure_managed_system_structure()

        sample_code = """from pydantic import BaseModel\n\nclass Student(BaseModel):\n    name: str\n    email: str\n"""
        file_path = self.manager.write_entity_artifact("Student", "model", sample_code)

        expected_path = self.manager.managed_system_path / "app" / "models" / "student_model.py"
        assert Path(file_path) == expected_path and expected_path.exists()
        assert "class Student(BaseModel)" in expected_path.read_text()

    def test_write_entity_artifact_routes(self):
        """write_entity_artifact should persist routes code to /app/routes."""
        self.manager.ensure_managed_system_structure()

        sample_routes = """from fastapi import APIRouter\n\nrouter = APIRouter()\n"""
        file_path = self.manager.write_entity_artifact("Student", "routes", sample_routes)

        expected_path = self.manager.managed_system_path / "app" / "routes" / "student_routes.py"
        assert Path(file_path) == expected_path and expected_path.exists()
        assert "APIRouter" in expected_path.read_text()
