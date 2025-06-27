"""
Unit tests for robust test generation functionality in TestSWEA.

Tests the enhanced test generation that validates dependencies before generating tests
and provides fallback mechanisms when dependencies are not ready.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from baes.swea_agents.test_swea import TestSWEA


class TestRobustTestGeneration:
    """Test robust test generation functionality"""

    @pytest.fixture
    def test_swea(self):
        """Create TestSWEA instance for testing"""
        return TestSWEA()

    @pytest.fixture
    def temp_managed_system(self):
        """Create temporary managed system directory"""
        temp_dir = tempfile.mkdtemp()
        managed_system_path = Path(temp_dir) / "managed_system"
        managed_system_path.mkdir()

        # Create basic structure
        (managed_system_path / "app").mkdir()
        (managed_system_path / "app" / "models").mkdir()
        (managed_system_path / "app" / "routes").mkdir()
        (managed_system_path / "app" / "database").mkdir()
        (managed_system_path / "ui").mkdir()
        (managed_system_path / "ui" / "pages").mkdir()
        (managed_system_path / "tests").mkdir()

        yield managed_system_path

        shutil.rmtree(temp_dir)

    def test_validate_test_dependencies_model_missing(self, test_swea, temp_managed_system):
        """Test dependency validation when model file is missing"""
        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "unit_tests")

            assert validation["dependencies_ready"] is False
            assert len(validation["missing_dependencies"]) > 0
            assert "Model file" in validation["missing_dependencies"][0]
            assert "Generate model first" in validation["recommendations"][0]

    def test_validate_test_dependencies_model_empty(self, test_swea, temp_managed_system):
        """Test dependency validation when model file exists but is empty"""
        # Create empty model file
        model_file = temp_managed_system / "app" / "models" / "student_model.py"
        model_file.write_text(
            """
from pydantic import BaseModel

class Student(BaseModel):
    # Define fields here as needed
    # Example: name: str
    # Example: age: int
    pass
"""
        )

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "unit_tests")

            assert validation["dependencies_ready"] is True  # File exists
            assert len(validation["warnings"]) > 0
            assert "no actual fields defined" in validation["warnings"][0]

    def test_validate_test_dependencies_model_has_fields(self, test_swea, temp_managed_system):
        """Test dependency validation when model file has actual fields"""
        # Create model file with actual fields
        model_file = temp_managed_system / "app" / "models" / "student_model.py"
        model_file.write_text(
            """
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    email: str
    age: int
"""
        )

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "unit_tests")

            assert validation["dependencies_ready"] is True
            assert len(validation["warnings"]) == 0

    def test_validate_test_dependencies_api_missing(self, test_swea, temp_managed_system):
        """Test dependency validation when API routes file is missing"""
        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "integration_tests")

            assert validation["dependencies_ready"] is False
            assert len(validation["missing_dependencies"]) > 0
            assert "Routes file" in validation["missing_dependencies"][0]

    def test_validate_test_dependencies_api_has_endpoints(self, test_swea, temp_managed_system):
        """Test dependency validation when API routes file has actual endpoints"""
        # Create routes file with actual endpoints
        routes_file = temp_managed_system / "app" / "routes" / "student_routes.py"
        routes_file.write_text(
            """
from fastapi import APIRouter

router = APIRouter()

@router.get("/students/")
def list_students():
    return []

@router.post("/students/")
def create_student():
    return {}
"""
        )

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "integration_tests")

            assert validation["dependencies_ready"] is True
            assert len(validation["warnings"]) == 0

    def test_validate_test_dependencies_ui_missing(self, test_swea, temp_managed_system):
        """Test dependency validation when UI file is missing"""
        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "ui_tests")

            assert validation["dependencies_ready"] is False
            assert len(validation["missing_dependencies"]) > 0
            assert "UI file" in validation["missing_dependencies"][0]

    def test_validate_test_dependencies_ui_has_components(self, test_swea, temp_managed_system):
        """Test dependency validation when UI file has actual components"""
        # Create UI file with actual components
        ui_file = temp_managed_system / "ui" / "app.py"
        ui_file.write_text(
            """
import streamlit as st

def main():
    st.title("Student Management")
    st.text_input("Name")
"""
        )

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            validation = test_swea._validate_test_dependencies("Student", "ui_tests")

            assert validation["dependencies_ready"] is True
            assert len(validation["warnings"]) == 0

    def test_check_all_dependencies_ready_all_ready(self, test_swea, temp_managed_system):
        """Test checking all dependencies when everything is ready"""
        # Create all required files
        (temp_managed_system / "app" / "models" / "student_model.py").write_text(
            """
from pydantic import BaseModel
class Student(BaseModel):
    name: str
"""
        )

        (temp_managed_system / "app" / "routes" / "student_routes.py").write_text(
            """
from fastapi import APIRouter
router = APIRouter()
@router.get("/students/")
def list_students():
    return []
"""
        )

        (temp_managed_system / "ui" / "app.py").write_text(
            """
import streamlit as st
def main():
    st.title("Student Management")
"""
        )

        (temp_managed_system / "app" / "database" / "academic.db").touch()

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            status = test_swea._check_all_dependencies_ready("Student")

            assert status["all_ready"] is True
            assert status["model_ready"] is True
            assert status["api_ready"] is True
            assert status["ui_ready"] is True
            assert status["database_ready"] is True

    def test_check_all_dependencies_ready_not_ready(self, test_swea, temp_managed_system):
        """Test checking all dependencies when some are missing"""
        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            status = test_swea._check_all_dependencies_ready("Student")

            assert status["all_ready"] is False
            assert status["model_ready"] is False
            assert status["api_ready"] is False
            assert status["ui_ready"] is False
            assert status["database_ready"] is False
            assert len(status["missing_components"]) > 0

    def test_generate_fallback_test(self, test_swea):
        """Test generation of fallback test when dependencies are not ready"""
        validation = {
            "missing_dependencies": [
                "Model file: student_model.py",
                "Routes file: student_routes.py",
            ],
            "recommendations": ["Generate model first", "Generate API first"],
        }

        fallback_test = test_swea._generate_fallback_test("Student", "unit_tests", validation)

        assert "Fallback test for Student unit tests" in fallback_test
        assert "MISSING DEPENDENCIES:" in fallback_test
        assert "Model file: student_model.py" in fallback_test
        assert "RECOMMENDATIONS:" in fallback_test
        assert "Generate model first" in fallback_test
        assert "class TestStudentUnitTestsFallback:" in fallback_test
        assert '@pytest.mark.skip(reason="Dependencies not ready")' in fallback_test

    def test_generate_robust_test_code_dependencies_ready(self, test_swea, temp_managed_system):
        """Test robust test code generation when dependencies are ready"""
        # Create model file with actual fields
        (temp_managed_system / "app" / "models" / "student_model.py").write_text(
            """
from pydantic import BaseModel
class Student(BaseModel):
    name: str
    email: str
"""
        )

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            with patch.object(test_swea, "llm_client") as mock_llm:
                mock_llm.generate_code_with_domain_focus.return_value = (
                    "import pytest\n\ndef test_student():\n    pass"
                )

                test_code = test_swea._generate_robust_test_code(
                    "Student", "unit_tests", ["name:str", "email:str"], "academic"
                )

                assert "import pytest" in test_code
                assert mock_llm.generate_code_with_domain_focus.called

    def test_generate_robust_test_code_dependencies_not_ready(self, test_swea, temp_managed_system):
        """Test robust test code generation when dependencies are not ready"""
        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            test_code = test_swea._generate_robust_test_code(
                "Student", "unit_tests", ["name:str", "email:str"], "academic"
            )

            # Should generate fallback test
            assert "Fallback test for Student unit tests" in test_code
            assert "Dependencies not ready" in test_code

    def test_generate_fallback_tests_for_all_types(self, test_swea, temp_managed_system):
        """Test generation of fallback tests for all types"""
        dependencies_status = {
            "all_ready": False,
            "missing_components": ["Model file", "API file"],
            "warnings": ["No actual fields defined"],
        }

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            result = test_swea._generate_fallback_tests_for_all_types(
                "Student", dependencies_status
            )

            assert result["success"] is True
            assert result["data"]["fallback_mode"] is True
            assert len(result["data"]["test_types_generated"]) == 3  # unit, integration, ui
            assert "unit_tests" in result["data"]["test_types_generated"]
            assert "integration_tests" in result["data"]["test_types_generated"]
            assert "ui_tests" in result["data"]["test_types_generated"]

    def test_generate_all_tests_with_collaboration_dependencies_ready(
        self, test_swea, temp_managed_system
    ):
        """Test test generation when all dependencies are ready"""
        # Create all required files
        (temp_managed_system / "app" / "models" / "student_model.py").write_text(
            """
from pydantic import BaseModel
class Student(BaseModel):
    name: str
"""
        )

        (temp_managed_system / "app" / "routes" / "student_routes.py").write_text(
            """
from fastapi import APIRouter
router = APIRouter()
@router.get("/students/")
def list_students():
    return []
"""
        )

        (temp_managed_system / "ui" / "app.py").write_text(
            """
import streamlit as st
def main():
    st.title("Student Management")
"""
        )

        (temp_managed_system / "app" / "database" / "academic.db").touch()

        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            with patch.object(test_swea, "_generate_unit_tests") as mock_unit:
                with patch.object(test_swea, "_generate_integration_tests") as mock_integration:
                    with patch.object(test_swea, "_generate_ui_tests") as mock_ui:
                        mock_unit.return_value = {"success": True, "data": {}}
                        mock_integration.return_value = {"success": True, "data": {}}
                        mock_ui.return_value = {"success": True, "data": {}}

                        result = test_swea._generate_all_tests_with_collaboration(
                            {"entity": "Student", "attributes": ["name:str"], "context": "academic"}
                        )

                        assert result["success"] is True
                        assert result["data"]["dependencies_validated"] is True
                        assert len(result["data"]["test_types_generated"]) == 3

    def test_generate_all_tests_with_collaboration_dependencies_not_ready(
        self, test_swea, temp_managed_system
    ):
        """Test test generation when dependencies are not ready"""
        with patch.object(test_swea, "managed_system_manager") as mock_manager:
            mock_manager.managed_system_path = temp_managed_system

            result = test_swea._generate_all_tests_with_collaboration(
                {"entity": "Student", "attributes": ["name:str"], "context": "academic"}
            )

            assert result["success"] is True
            assert result["data"]["fallback_mode"] is True
            assert result["data"]["dependencies_validated"] is True
            assert len(result["data"]["test_types_generated"]) == 3

    def test_has_actual_model_fields(self, test_swea):
        """Test detection of actual model fields"""
        # Test with actual fields
        model_with_fields = """
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    email: str
    age: int
"""
        assert test_swea._has_actual_model_fields(model_with_fields, "Student") is True

        # Test with placeholder fields
        model_with_placeholders = """
from pydantic import BaseModel

class Student(BaseModel):
    # Define fields here as needed
    # Example: name: str
    # Example: age: int
    pass
"""
        assert test_swea._has_actual_model_fields(model_with_placeholders, "Student") is False

    def test_has_actual_endpoints(self, test_swea):
        """Test detection of actual API endpoints"""
        # Test with actual endpoints
        routes_with_endpoints = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/students/")
def list_students():
    return []

@router.post("/students/")
def create_student():
    return {}
"""
        assert test_swea._has_actual_endpoints(routes_with_endpoints) is True

        # Test without endpoints
        routes_without_endpoints = """
from fastapi import APIRouter

router = APIRouter()

# Define endpoints here
"""
        assert test_swea._has_actual_endpoints(routes_without_endpoints) is False

    def test_has_actual_ui_components(self, test_swea):
        """Test detection of actual UI components"""
        # Test with actual components
        ui_with_components = """
import streamlit as st

def main():
    st.title("Student Management")
    st.text_input("Name")
"""
        assert test_swea._has_actual_ui_components(ui_with_components) is True

        # Test without components
        ui_without_components = """
import streamlit as st

# Define UI components here
"""
        assert test_swea._has_actual_ui_components(ui_without_components) is False

    def test_generate_robust_test_code_raises_error_on_missing_dependencies(self):
        """Test that _generate_robust_test_code raises RuntimeError when dependencies are missing"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["model file", "API routes"],
                "recommendations": ["Complete model generation", "Complete API generation"],
                "warnings": [],
            }

            # Test that RuntimeError is raised
            with pytest.raises(RuntimeError) as excinfo:
                test_swea._generate_robust_test_code(
                    "Student", "unit_tests", ["name", "email"], "academic"
                )

            # Verify error message contains expected information
            error_msg = str(excinfo.value)
            assert "Cannot generate unit_tests for Student: missing dependencies" in error_msg
            assert "model file" in error_msg
            assert "API routes" in error_msg
            assert "Complete model generation" in error_msg

    def test_generate_all_tests_with_collaboration_returns_error_on_missing_dependencies(self):
        """Test that _generate_all_tests_with_collaboration returns error when dependencies are missing"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready for all test types
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["model file"],
                "recommendations": ["Complete model generation"],
                "warnings": [],
            }

            payload = {"entity": "Student", "attributes": ["name", "email"], "context": "academic"}

            result = test_swea._generate_all_tests_with_collaboration(payload)

            # Verify error response
            assert not result.get("success", True)
            assert result.get("error_type") == "missing_dependencies"
            assert "Cannot generate unit_tests for Student: missing dependencies" in result.get(
                "error", ""
            )

    def test_generate_unit_tests_returns_error_on_missing_dependencies(self):
        """Test that _generate_unit_tests returns error when dependencies are missing"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["model file"],
                "recommendations": ["Complete model generation"],
                "warnings": [],
            }

            payload = {"entity": "Student", "attributes": ["name", "email"], "context": "academic"}

            result = test_swea._generate_unit_tests(payload)

            # Verify error response
            assert not result.get("success", True)
            assert result.get("error_type") == "missing_dependencies"
            assert "Cannot generate unit_tests for Student: missing dependencies" in result.get(
                "error", ""
            )

    def test_generate_integration_tests_returns_error_on_missing_dependencies(self):
        """Test that _generate_integration_tests returns error when dependencies are missing"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["API routes"],
                "recommendations": ["Complete API generation"],
                "warnings": [],
            }

            payload = {"entity": "Student", "attributes": ["name", "email"], "context": "academic"}

            result = test_swea._generate_integration_tests(payload)

            # Verify error response
            assert not result.get("success", True)
            assert result.get("error_type") == "missing_dependencies"
            assert (
                "Cannot generate integration_tests for Student: missing dependencies"
                in result.get("error", "")
            )

    def test_generate_ui_tests_returns_error_on_missing_dependencies(self):
        """Test that _generate_ui_tests returns error when dependencies are missing"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["UI components"],
                "recommendations": ["Complete UI generation"],
                "warnings": [],
            }

            payload = {"entity": "Student", "attributes": ["name", "email"], "context": "academic"}

            result = test_swea._generate_ui_tests(payload)

            # Verify error response
            assert not result.get("success", True)
            assert result.get("error_type") == "missing_dependencies"
            assert "Cannot generate ui_tests for Student: missing dependencies" in result.get(
                "error", ""
            )

    def test_no_fallback_test_generation_occurs(self):
        """Test that no fallback test generation methods exist or are called"""
        test_swea = TestSWEA()

        # Verify that _generate_fallback_test method does not exist
        assert not hasattr(test_swea, "_generate_fallback_test")

        # Verify that _generate_fallback_tests_for_all_types method does not exist
        assert not hasattr(test_swea, "_generate_fallback_tests_for_all_types")

        # Verify that _check_all_dependencies_ready method does not exist
        assert not hasattr(test_swea, "_check_all_dependencies_ready")

    def test_handle_task_propagates_missing_dependencies_errors(self):
        """Test that handle_task properly propagates missing dependencies errors"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["model file"],
                "recommendations": ["Complete model generation"],
                "warnings": [],
            }

            payload = {"entity": "Student", "attributes": ["name", "email"], "context": "academic"}

            # Test all test generation tasks
            test_tasks = [
                "generate_all_tests_with_collaboration",
                "generate_unit_tests",
                "generate_integration_tests",
                "generate_ui_tests",
            ]

            for task in test_tasks:
                result = test_swea.handle_task(task, payload)

                # Verify error response
                assert not result.get("success", True)
                assert result.get("error_type") == "missing_dependencies"
                assert "missing dependencies" in result.get("error", "")

    def test_logging_and_presentation_logger_called_on_missing_dependencies(self):
        """Test that logging and presentation logger are called when dependencies are missing"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["model file"],
                "recommendations": ["Complete model generation"],
                "warnings": [],
            }

            # Mock presentation logger
            with patch(
                "baes.utils.presentation_logger.get_presentation_logger"
            ) as mock_presentation_logger:
                mock_logger = MagicMock()
                mock_presentation_logger.return_value = mock_logger

                # Mock logger.error
                with patch("logging.getLogger") as mock_logging:
                    mock_logger_instance = MagicMock()
                    mock_logging.return_value = mock_logger_instance

                    # This should raise RuntimeError
                    with pytest.raises(RuntimeError):
                        test_swea._generate_robust_test_code(
                            "Student", "unit_tests", ["name", "email"], "academic"
                        )

                    # Verify logging was called
                    mock_logger_instance.error.assert_called_once()
                    mock_logger.error.assert_called_once()

    def test_different_test_types_have_different_dependency_requirements(self):
        """Test that different test types validate different dependencies"""
        test_swea = TestSWEA()

        # Test that each test type calls _validate_test_dependencies with correct test_type
        test_types = ["unit_tests", "integration_tests", "ui_tests"]

        for test_type in test_types:
            with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
                mock_validate.return_value = {
                    "dependencies_ready": True,
                    "missing_dependencies": [],
                    "recommendations": [],
                    "warnings": [],
                }

                # Mock _get_generated_code to return some content
                with patch.object(test_swea, "_get_generated_code") as mock_get_code:
                    mock_get_code.return_value = "test code content"

                    # Mock _build_test_prompt to return a prompt
                    with patch.object(test_swea, "_build_test_prompt") as mock_build_prompt:
                        mock_build_prompt.return_value = "test prompt"

                        # Mock llm_client.generate_code_with_domain_focus
                        with patch.object(
                            test_swea.llm_client, "generate_code_with_domain_focus"
                        ) as mock_generate:
                            mock_generate.return_value = "generated test code"

                            test_swea._generate_robust_test_code(
                                "Student", test_type, ["name", "email"], "academic"
                            )

                            # Verify _validate_test_dependencies was called with correct test_type
                            mock_validate.assert_called_once_with("Student", test_type)

    def test_error_messages_are_actionable_and_clear(self):
        """Test that error messages for missing dependencies are actionable and clear"""
        test_swea = TestSWEA()

        # Mock _validate_test_dependencies to return dependencies not ready
        with patch.object(test_swea, "_validate_test_dependencies") as mock_validate:
            mock_validate.return_value = {
                "dependencies_ready": False,
                "missing_dependencies": ["model file", "API routes", "UI components"],
                "recommendations": [
                    "Complete model generation using BackendSWEA",
                    "Complete API generation using BackendSWEA",
                    "Complete UI generation using FrontendSWEA",
                ],
                "warnings": [],
            }

            # Test that RuntimeError is raised with clear message
            with pytest.raises(RuntimeError) as excinfo:
                test_swea._generate_robust_test_code(
                    "Student", "unit_tests", ["name", "email"], "academic"
                )

            error_msg = str(excinfo.value)

            # Verify error message contains all required elements
            assert "Cannot generate unit_tests for Student: missing dependencies" in error_msg
            assert "model file" in error_msg
            assert "API routes" in error_msg
            assert "UI components" in error_msg
            assert "Complete model generation using BackendSWEA" in error_msg
            assert "Complete API generation using BackendSWEA" in error_msg
            assert "Complete UI generation using FrontendSWEA" in error_msg
