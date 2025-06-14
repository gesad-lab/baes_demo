import subprocess
import sys
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient


class TestSWEA(BaseAgent):
    """
    Software Engineering Autonomous Agent responsible for generating and executing
    comprehensive tests for all generated artifacts (models, APIs, UI, database).
    """

    def __init__(self):
        super().__init__("TestSWEA", "Test Generation and Execution Agent", "SWEA")
        self.llm_client = OpenAIClient()
        self._managed_system_manager = None  # Lazy initialization

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "generate_unit_tests": "_generate_unit_tests",
        "generate_integration_tests": "_generate_integration_tests",
        "generate_ui_tests": "_generate_ui_tests",
        "execute_tests": "_execute_tests",
        "generate_all_tests": "_generate_all_tests",
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch task to internal test generation/execution methods."""
        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                f"Unknown task. Supported tasks: {list(self._SUPPORTED_TASKS.keys())}",
                "invalid_task",
            )

        method = getattr(self, self._SUPPORTED_TASKS[task])
        try:
            return method(payload)
        except Exception as e:
            return self.create_error_response(task, str(e), "execution_error")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_test_prompt(
        self,
        entity: str,
        attributes: List[str],
        test_type: str,
        context: str,
        generated_code: str = "",
    ) -> str:
        """Build prompt for test generation based on test type."""
        base_prompt = f"""
You are a TestSWEA (Test Software Engineering Autonomous Agent) responsible for generating comprehensive tests.

Entity: {entity}
Attributes: {attributes}
Context: {context}
Test Type: {test_type}

Generated Code to Test:
{generated_code}

Requirements:
1. Use pytest framework with proper fixtures and mocking
2. Mock external dependencies (OpenAI API, file operations, etc.)
3. Include both positive and negative test cases
4. Test edge cases and error conditions
5. Use proper assertions and test structure
6. Include setup and teardown as needed
7. Generate complete, runnable test code
8. Focus on testing business logic and domain coherence

"""

        if test_type == "unit_tests":
            return (
                base_prompt
                + """
Generate comprehensive unit tests for the Pydantic model including:
- Field validation tests
- Type checking tests
- Business rule validation tests
- Serialization/deserialization tests
- Edge case handling
- Invalid data rejection tests

Return ONLY complete Python test code with imports and test classes.
"""
            )

        elif test_type == "integration_tests":
            return (
                base_prompt
                + """
Generate comprehensive integration tests for the FastAPI routes including:
- CRUD operation tests (Create, Read, Update, Delete)
- HTTP status code validation
- Request/response schema validation
- Database interaction tests (mocked)
- Error handling tests
- Authentication/authorization tests (if applicable)
- Business rule enforcement tests

Return ONLY complete Python test code with imports, fixtures, and test classes.
"""
            )

        elif test_type == "ui_tests":
            return (
                base_prompt
                + """
Generate comprehensive UI tests for the Streamlit interface including:
- Form submission tests
- Data display tests
- User interaction simulation
- Error message display tests
- Navigation tests
- Session state tests
- API integration tests (mocked)

Return ONLY complete Python test code with imports and test classes using appropriate mocking.
"""
            )

        else:
            return base_prompt + "Generate appropriate test code based on the context provided."

    def _write_test_to_managed_system(self, entity: str, test_type: str, test_code: str) -> str:
        """Write test code to the managed system tests directory."""
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()

        # Create tests directory structure
        managed_system_path = self.managed_system_manager.managed_system_path
        tests_dir = managed_system_path / "tests"
        tests_dir.mkdir(exist_ok=True)

        # Create subdirectories for different test types
        unit_tests_dir = tests_dir / "unit"
        integration_tests_dir = tests_dir / "integration"
        ui_tests_dir = tests_dir / "ui"

        for test_dir in [unit_tests_dir, integration_tests_dir, ui_tests_dir]:
            test_dir.mkdir(exist_ok=True)
            # Create __init__.py files
            (test_dir / "__init__.py").touch()

        # Determine target directory and filename
        if test_type == "unit_tests":
            test_file = unit_tests_dir / f"test_{entity.lower()}_model.py"
        elif test_type == "integration_tests":
            test_file = integration_tests_dir / f"test_{entity.lower()}_api.py"
        elif test_type == "ui_tests":
            test_file = ui_tests_dir / f"test_{entity.lower()}_ui.py"
        else:
            test_file = tests_dir / f"test_{entity.lower()}_{test_type}.py"

        # Write test code
        test_file.write_text(test_code)

        return str(test_file)

    def _execute_pytest(self, test_file_path: str) -> Dict[str, Any]:
        """Execute pytest on the generated test file and return results."""
        try:
            # Change to the managed system directory for test execution
            managed_system_path = self.managed_system_manager.managed_system_path

            # Run pytest with coverage and verbose output
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                test_file_path,
                "-v",
                "--tb=short",
                "--no-header",
                "--no-summary",
                "-q",
            ]

            result = subprocess.run(
                cmd,
                cwd=str(managed_system_path),
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_file": test_file_path,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test execution timed out after 60 seconds",
                "test_file": test_file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error executing tests: {str(e)}",
                "test_file": test_file_path,
            }

    def _get_generated_code(self, entity: str, code_type: str) -> str:
        """Retrieve generated code from managed system for test generation."""
        try:
            managed_system_path = self.managed_system_manager.managed_system_path

            if code_type == "model":
                model_file = managed_system_path / "app" / "models" / f"{entity.lower()}.py"
                if model_file.exists():
                    return model_file.read_text()
            elif code_type == "routes":
                routes_file = managed_system_path / "app" / "routes" / f"{entity.lower()}_routes.py"
                if routes_file.exists():
                    return routes_file.read_text()
            elif code_type == "ui":
                ui_file = managed_system_path / "ui" / "pages" / f"{entity.lower()}_page.py"
                if ui_file.exists():
                    return ui_file.read_text()
                # Fallback to app.py
                ui_file = managed_system_path / "ui" / "app.py"
                if ui_file.exists():
                    return ui_file.read_text()

            return ""
        except Exception:
            return ""

    # -------------------- task implementations ------------------------
    def _generate_unit_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unit tests for Pydantic models."""
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        # Get the generated model code
        model_code = self._get_generated_code(entity, "model")

        prompt = self._build_test_prompt(entity, attributes, "unit_tests", context, model_code)
        test_code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="Unit Tests",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "test_type": "unit_tests",
            },
        )

        test_file_path = self._write_test_to_managed_system(entity, "unit_tests", test_code)

        # Execute the tests
        test_results = self._execute_pytest(test_file_path)

        return self.create_success_response(
            "generate_unit_tests",
            {
                "test_file_path": test_file_path,
                "test_code": test_code,
                "test_execution": test_results,
                "managed_system": True,
            },
        )

    def _generate_integration_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate integration tests for FastAPI routes."""
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        # Get the generated API code
        api_code = self._get_generated_code(entity, "routes")

        prompt = self._build_test_prompt(entity, attributes, "integration_tests", context, api_code)
        test_code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="Integration Tests",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "test_type": "integration_tests",
            },
        )

        test_file_path = self._write_test_to_managed_system(entity, "integration_tests", test_code)

        # Execute the tests
        test_results = self._execute_pytest(test_file_path)

        return self.create_success_response(
            "generate_integration_tests",
            {
                "test_file_path": test_file_path,
                "test_code": test_code,
                "test_execution": test_results,
                "managed_system": True,
            },
        )

    def _generate_ui_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI tests for Streamlit interface."""
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        # Get the generated UI code
        ui_code = self._get_generated_code(entity, "ui")

        prompt = self._build_test_prompt(entity, attributes, "ui_tests", context, ui_code)
        test_code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="UI Tests",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "test_type": "ui_tests",
            },
        )

        test_file_path = self._write_test_to_managed_system(entity, "ui_tests", test_code)

        # Execute the tests
        test_results = self._execute_pytest(test_file_path)

        return self.create_success_response(
            "generate_ui_tests",
            {
                "test_file_path": test_file_path,
                "test_code": test_code,
                "test_execution": test_results,
                "managed_system": True,
            },
        )

    def _execute_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all tests in the managed system."""
        entity = payload.get("entity", "Student")

        try:
            managed_system_path = self.managed_system_manager.managed_system_path
            tests_dir = managed_system_path / "tests"

            if not tests_dir.exists():
                return self.create_error_response(
                    "execute_tests", f"No tests directory found for {entity}", "no_tests_found"
                )

            # Run all tests
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(tests_dir),
                "-v",
                "--tb=short",
                "--no-header",
                "-q",
            ]

            result = subprocess.run(
                cmd,
                cwd=str(managed_system_path),
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for all tests
            )

            return self.create_success_response(
                "execute_tests",
                {
                    "success": result.returncode == 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "tests_directory": str(tests_dir),
                },
            )

        except Exception as e:
            return self.create_error_response(
                "execute_tests", f"Error executing all tests: {str(e)}", "execution_error"
            )

    def _generate_all_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all types of tests (unit, integration, UI) for an entity."""
        entity = payload.get("entity", "Student")
        # attributes and context will be used in future enhancements
        # attributes = payload.get("attributes", [])
        # context = payload.get("context", "academic")

        results = {
            "entity": entity,
            "test_types_generated": [],
            "test_executions": [],
            "overall_success": True,
        }

        # Generate unit tests
        unit_result = self._generate_unit_tests(payload)
        results["test_types_generated"].append("unit_tests")
        results["test_executions"].append({"test_type": "unit_tests", "result": unit_result})
        if not unit_result.get("success", False):
            results["overall_success"] = False

        # Generate integration tests
        integration_result = self._generate_integration_tests(payload)
        results["test_types_generated"].append("integration_tests")
        results["test_executions"].append(
            {"test_type": "integration_tests", "result": integration_result}
        )
        if not integration_result.get("success", False):
            results["overall_success"] = False

        # Generate UI tests
        ui_result = self._generate_ui_tests(payload)
        results["test_types_generated"].append("ui_tests")
        results["test_executions"].append({"test_type": "ui_tests", "result": ui_result})
        if not ui_result.get("success", False):
            results["overall_success"] = False

        return self.create_success_response("generate_all_tests", results)
