import os
from unittest.mock import patch, Mock

import pytest

from baes.swea_agents.programmer_swea import ProgrammerSWEA
from baes.swea_agents.database_swea import DatabaseSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA


@pytest.mark.unit
class TestProgrammerSWEA:
    """Unit tests for the Programmer SWEA agent"""

    @patch('baes.swea_agents.programmer_swea.OpenAIClient')
    def test_generate_model(self, mock_client_cls, tmp_path):
        mock_instance = Mock()
        mock_instance.generate_code_with_domain_focus.return_value = "class Student: pass"
        mock_client_cls.return_value = mock_instance

        agent = ProgrammerSWEA()
        payload = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str", "course: str"],
            "context": "academic"
        }
        result = agent.handle_task("generate_model", payload)

        assert result["success"] is True
        file_path = result["data"]["file_path"]
        assert os.path.exists(file_path)
        with open(file_path, "r") as f:
            contents = f.read()
        assert "class" in contents

    @patch('baes.swea_agents.programmer_swea.OpenAIClient')
    def test_generate_api(self, mock_client_cls):
        mock_instance = Mock()
        mock_instance.generate_code_with_domain_focus.return_value = "from fastapi import APIRouter"
        mock_client_cls.return_value = mock_instance

        agent = ProgrammerSWEA()
        payload = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str", "course: str"],
            "context": "academic"
        }
        result = agent.handle_task("generate_api", payload)
        assert result["success"] is True
        file_path = result["data"]["file_path"]
        assert os.path.exists(file_path)


@pytest.mark.unit
class TestDatabaseSWEA:
    """Unit tests for the Database SWEA agent"""

    def test_setup_database(self, tmp_path):
        agent = DatabaseSWEA()
        db_path = tmp_path / "academic.db"
        payload = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str", "course: str"],
            "database_path": str(db_path)
        }
        result = agent.handle_task("setup_database", payload)
        assert result["success"] is True
        assert os.path.exists(str(db_path))


@pytest.mark.unit
class TestFrontendSWEA:
    """Unit tests for the Frontend SWEA agent"""

    @patch('baes.swea_agents.frontend_swea.OpenAIClient')
    def test_generate_ui(self, mock_client_cls):
        mock_instance = Mock()
        mock_instance.generate_code_with_domain_focus.return_value = "import streamlit as st"
        mock_client_cls.return_value = mock_instance

        agent = FrontendSWEA()
        payload = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str", "course: str"],
            "context": "academic"
        }
        result = agent.handle_task("generate_ui", payload)
        assert result["success"] is True
        file_path = result["data"]["file_path"]
        assert os.path.exists(file_path) 