"""
Test suite for Managed System functionality.
Validates the transition from legacy generated/ directory to managed system approach.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from baes.core.managed_system_manager import ManagedSystemManager
from config import Config


class TestManagedSystemManager:
    """Test the ManagedSystemManager functionality."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        # Override the managed system path for testing
        self.original_env = os.environ.get("MANAGED_SYSTEM_PATH")
        os.environ["MANAGED_SYSTEM_PATH"] = str(Path(self.temp_dir) / "test_managed_system")

        self.manager = ManagedSystemManager()

    def teardown_method(self):
        """Clean up test environment."""
        if self.original_env:
            os.environ["MANAGED_SYSTEM_PATH"] = self.original_env
        elif "MANAGED_SYSTEM_PATH" in os.environ:
            del os.environ["MANAGED_SYSTEM_PATH"]

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_managed_system_path_configuration(self):
        """Test that managed system path is properly configured."""
        managed_path = Config.get_managed_system_path()
        assert managed_path.exists()
        assert managed_path.name == "test_managed_system"

    def test_ensure_managed_system_structure(self):
        """Test that managed system structure is created correctly."""
        success = self.manager.ensure_managed_system_structure()
        assert success

        # Check required directories
        required_dirs = [
            "app",
            "app/models",
            "app/routes",
            "app/database",
            "ui",
            "ui/pages",
            "tests",
        ]
        for dir_name in required_dirs:
            assert (self.manager.managed_system_path / dir_name).exists()

        # Check required files
        required_files = [
            "requirements.txt",
            "README.md",
            ".gitignore",
            "setup_venv.sh",
            "start_servers.sh",
        ]
        for file_name in required_files:
            assert (self.manager.managed_system_path / file_name).exists()

    def test_write_entity_artifact_model(self):
        """Test writing entity model artifacts to managed system."""
        self.manager.ensure_managed_system_structure()

        sample_model_code = """from pydantic import BaseModel

class Student(BaseModel):
    name: str
    email: str
    age: int
"""

        file_path = self.manager.write_entity_artifact("Student", "model", sample_model_code)

        # Verify file was created in correct location
        expected_path = self.manager.managed_system_path / "app" / "models" / "student_model.py"
        assert Path(file_path) == expected_path
        assert expected_path.exists()

        # Verify content
        content = expected_path.read_text()
        assert "class Student(BaseModel)" in content

    def test_write_entity_artifact_routes(self):
        """Test writing entity routes artifacts to managed system."""
        self.manager.ensure_managed_system_structure()

        sample_routes_code = """from fastapi import APIRouter

router = APIRouter()

@router.get("/students")
async def get_students():
    return []
"""

        file_path = self.manager.write_entity_artifact("Student", "routes", sample_routes_code)

        # Verify file was created in correct location
        expected_path = self.manager.managed_system_path / "app" / "routes" / "student_routes.py"
        assert Path(file_path) == expected_path
        assert expected_path.exists()

        # Verify content
        content = expected_path.read_text()
        assert "router = APIRouter()" in content
