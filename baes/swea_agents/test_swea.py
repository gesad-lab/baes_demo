import re
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

    Enhanced with autonomous collaboration capabilities:
    - Analyzes test failures and coordinates fixes with other SWEAs
    - Ensures quality without exposing technical details to HBEs
    - Re-executes tests after each component regeneration
    """

    def __init__(self):
        super().__init__("TestSWEA", "Test Generation and Execution Agent", "SWEA")
        self.llm_client = OpenAIClient()
        self._managed_system_manager = None  # Lazy initialization
        self.max_fix_iterations = 10  # Maximum attempts to fix issues autonomously
        self.collaboration_history = []  # Track SWEA collaboration attempts

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
        "generate_all_tests": "_generate_all_tests_with_collaboration",
        "generate_all_tests_with_collaboration": "_generate_all_tests_with_collaboration",
        "validate_and_fix": "_validate_and_fix_system",
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
    # Enhanced Collaborative Methods
    # ------------------------------------------------------------------

    def _generate_all_tests_with_collaboration(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all tests and collaborate with other SWEAs to fix issues autonomously."""
        # entity = payload.get("entity", "Student")  # Currently unused

        self.collaboration_history = []  # Reset collaboration history

        # Step 1: Generate all tests
        base_result = self._generate_all_tests_basic(payload)

        # Step 2: Analyze failures and collaborate to fix issues
        if not self._all_tests_passed(base_result):
            collaboration_result = self._collaborate_to_fix_issues(payload, base_result)
            if collaboration_result["success"]:
                return collaboration_result

        return base_result

    def _validate_and_fix_system(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate entire system and coordinate fixes with other SWEAs."""
        # entity = payload.get("entity", "Student")  # Currently unused

        # Execute all tests to get current state
        test_result = self._execute_all_tests(payload)

        if test_result["success"]:
            return self.create_success_response(
                "validate_and_fix",
                {
                    "validation_status": "passed",
                    "system_quality": "high",
                    "tests_executed": test_result.get("data", {}).get("tests_executed", 0),
                    "collaboration_needed": False,
                },
            )

        # System has issues - collaborate to fix
        fix_result = self._collaborate_to_fix_issues(payload, test_result)
        return fix_result

    def _collaborate_to_fix_issues(
        self, payload: Dict[str, Any], test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze test failures and collaborate with other SWEAs to fix issues."""
        entity = payload.get("entity", "Student")
        # coordinating_bae = payload.get("coordinating_bae", "StudentBAE")  # Currently unused

        collaboration_log = []
        iteration = 0

        while iteration < self.max_fix_iterations:
            iteration += 1

            # Analyze all test failures
            failure_analysis = self._analyze_test_failures(test_results)

            if not failure_analysis["issues_found"]:
                break

            collaboration_log.append(
                f"Iteration {iteration}: Found {len(failure_analysis['issues'])} issues"
            )

            # Request fixes from appropriate SWEAs
            fix_requests = self._create_fix_requests(failure_analysis, entity, payload)

            # Execute fix requests (this would normally go through the RuntimeKernel)
            fixes_applied = self._execute_fix_requests(fix_requests, payload)
            collaboration_log.extend(fixes_applied)

            # Re-execute tests to see if issues are resolved
            test_results = self._execute_all_tests(payload)

            if self._all_tests_passed(test_results):
                collaboration_log.append(f"✅ All tests passing after {iteration} iteration(s)")
                break

        # Store collaboration history
        self.collaboration_history = collaboration_log

        return self.create_success_response(
            "collaborative_testing",
            {
                "final_test_status": self._all_tests_passed(test_results),
                "iterations": iteration,
                "collaboration_log": collaboration_log,
                "issues_resolved": iteration < self.max_fix_iterations,
                "final_test_results": test_results,
                "autonomous_collaboration": True,
            },
        )

    def _analyze_test_failures(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test failures and categorize issues for SWEA collaboration."""
        issues = []
        issues_found = False

        # Check if test_results contains execution results
        test_executions = test_results.get("test_executions", [])
        if not test_executions and "test_execution" in test_results:
            test_executions = [{"result": test_results}]

        for test_execution in test_executions:
            test_result = test_execution.get("result", {})
            test_data = test_result.get("data", {})
            test_exec = test_data.get("test_execution", {})

            if not test_exec.get("success", True):
                issues_found = True
                stderr = test_exec.get("stderr", "")
                stdout = test_exec.get("stdout", "")

                # Categorize the issue
                issue_category = self._categorize_test_failure(stderr, stdout)
                issues.append(
                    {
                        "category": issue_category["category"],
                        "responsible_swea": issue_category["responsible_swea"],
                        "description": issue_category["description"],
                        "fix_action": issue_category["fix_action"],
                        "stderr": stderr,
                        "stdout": stdout,
                    }
                )

        return {
            "issues_found": issues_found,
            "issues": issues,
            "total_issues": len(issues),
        }

    def _categorize_test_failure(self, stderr: str, stdout: str) -> Dict[str, str]:
        """Categorize test failure and determine which SWEA should fix it."""
        combined_output = f"{stderr} {stdout}".lower()

        # Dependency issues -> BackendSWEA should fix
        if any(
            pattern in combined_output
            for pattern in [
                "modulenotfounderror",
                "no module named",
                "importerror",
                "email-validator",
                "pydantic[email]",
            ]
        ):
            return {
                "category": "missing_dependency",
                "responsible_swea": "BackendSWEA",
                "description": "Missing Python dependencies",
                "fix_action": "update_dependencies",
            }

        # Model validation issues -> BackendSWEA should fix
        if any(
            pattern in combined_output
            for pattern in ["validationerror", "field required", "type expected", "pydantic"]
        ):
            return {
                "category": "model_validation",
                "responsible_swea": "BackendSWEA",
                "description": "Model validation or schema issues",
                "fix_action": "fix_model_schema",
            }

        # Import/syntax issues -> BackendSWEA should fix
        if any(
            pattern in combined_output
            for pattern in ["syntaxerror", "indentationerror", "cannot import"]
        ):
            return {
                "category": "code_syntax",
                "responsible_swea": "BackendSWEA",
                "description": "Code syntax or import issues",
                "fix_action": "fix_code_syntax",
            }

        # API/route issues -> BackendSWEA should fix
        if any(
            pattern in combined_output
            for pattern in ["fastapi", "router", "endpoint", "httpexception"]
        ):
            return {
                "category": "api_issues",
                "responsible_swea": "BackendSWEA",
                "description": "API routing or endpoint issues",
                "fix_action": "fix_api_routes",
            }

        # UI/Streamlit issues -> FrontendSWEA should fix
        if any(pattern in combined_output for pattern in ["streamlit", "st.", "ui", "frontend"]):
            return {
                "category": "ui_issues",
                "responsible_swea": "FrontendSWEA",
                "description": "UI or Streamlit interface issues",
                "fix_action": "fix_ui_interface",
            }

        # Database issues -> DatabaseSWEA should fix
        if any(
            pattern in combined_output
            for pattern in ["sqlite", "database", "sql", "table", "schema"]
        ):
            return {
                "category": "database_issues",
                "responsible_swea": "DatabaseSWEA",
                "description": "Database schema or connection issues",
                "fix_action": "fix_database_schema",
            }

        # Default: BackendSWEA for general issues
        return {
            "category": "general_issue",
            "responsible_swea": "BackendSWEA",
            "description": "General system issue",
            "fix_action": "general_fix",
        }

    def _create_fix_requests(
        self, failure_analysis: Dict[str, Any], entity: str, original_payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create fix requests for appropriate SWEAs based on failure analysis."""
        fix_requests = []

        for issue in failure_analysis["issues"]:
            fix_request = {
                "swea_agent": issue["responsible_swea"],
                "task_type": self._get_fix_task_type(issue),
                "payload": {
                    **original_payload,  # Include original payload
                    "fix_context": {
                        "issue_category": issue["category"],
                        "issue_description": issue["description"],
                        "fix_action": issue["fix_action"],
                        "test_stderr": issue["stderr"],
                        "test_stdout": issue["stdout"],
                        "requested_by": "TestSWEA",
                        "collaboration_mode": True,
                    },
                },
            }
            fix_requests.append(fix_request)

        return fix_requests

    def _get_fix_task_type(self, issue: Dict[str, str]) -> str:
        """Determine the appropriate task type for the SWEA to fix the issue."""
        fix_action = issue["fix_action"]
        responsible_swea = issue["responsible_swea"]

        if responsible_swea == "BackendSWEA":
            if fix_action == "update_dependencies":
                return "generate_requirements"  # New task for dependency management
            elif fix_action in ["fix_model_schema", "model_validation"]:
                return "generate_model"  # Regenerate model
            elif fix_action in ["fix_api_routes", "api_issues"]:
                return "generate_api"  # Regenerate API
            else:
                return "generate_model"  # Default

        elif responsible_swea == "FrontendSWEA":
            return "generate_ui"  # Regenerate UI

        elif responsible_swea == "DatabaseSWEA":
            return "setup_database"  # Recreate database

        return "regenerate_component"  # Fallback

    def _execute_fix_requests(
        self, fix_requests: List[Dict[str, Any]], payload: Dict[str, Any]
    ) -> List[str]:
        """Execute fix requests by simulating SWEA collaboration."""
        collaboration_log = []

        for fix_request in fix_requests:
            swea_agent = fix_request["swea_agent"]
            task_type = fix_request["task_type"]
            issue_desc = fix_request["payload"]["fix_context"]["issue_description"]

            collaboration_log.append(f"🔧 Requesting {swea_agent} to {task_type} - {issue_desc}")

            # Note: In a real implementation, this would send the fix_request
            # back to the RuntimeKernel to execute the appropriate SWEA
            # For now, we'll simulate the collaboration

            if swea_agent == "BackendSWEA" and "dependency" in issue_desc.lower():
                # Simulate dependency fix
                self._create_requirements_file(payload.get("entity", "Student"))
                collaboration_log.append(
                    "✅ BackendSWEA: Added missing dependencies to requirements.txt"
                )

        return collaboration_log

    def _create_requirements_file(self, entity: str):
        """Create or update requirements.txt with necessary dependencies."""
        managed_system_path = self.managed_system_manager.managed_system_path
        requirements_file = managed_system_path / "requirements.txt"

        # Basic requirements that are commonly needed
        basic_requirements = [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "streamlit==1.28.1",
            "pydantic[email]==2.5.0",  # Include email validation
            "sqlalchemy==2.0.23",
            "python-multipart",  # For FastAPI forms
            "requests==2.31.0",
            "pytest==7.4.3",
            "email-validator",  # Explicit email validator
        ]

        requirements_content = "\n".join(basic_requirements) + "\n"
        requirements_file.write_text(requirements_content)

    def _execute_all_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all tests in the managed system."""
        entity = payload.get("entity", "Student")

        try:
            managed_system_path = self.managed_system_manager.managed_system_path
            tests_dir = managed_system_path / "tests"

            if not tests_dir.exists():
                return self.create_error_response(
                    "execute_all_tests", f"No tests directory found for {entity}", "no_tests_found"
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
                "execute_all_tests",
                {
                    "success": result.returncode == 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "tests_directory": str(tests_dir),
                    "tests_executed": self._count_tests_executed(result.stdout),
                },
            )

        except Exception as e:
            return self.create_error_response(
                "execute_all_tests", f"Error executing all tests: {str(e)}", "execution_error"
            )

    def _count_tests_executed(self, stdout: str) -> int:
        """Count the number of tests executed from pytest output."""
        # Look for patterns like "collected X items" or "X passed"
        collected_match = re.search(r"collected (\d+) items", stdout)
        if collected_match:
            return int(collected_match.group(1))

        passed_match = re.search(r"(\d+) passed", stdout)
        if passed_match:
            return int(passed_match.group(1))

        return 0

    def _count_tests_passed(self, stdout: str) -> int:
        """Count the number of tests that passed from pytest output."""
        passed_match = re.search(r"(\d+) passed", stdout)
        if passed_match:
            return int(passed_match.group(1))

        return 0

    def _all_tests_passed(self, test_results: Dict[str, Any]) -> bool:
        """Check if all tests passed in the test results."""
        # Check overall success
        if test_results.get("success") is False:
            return False

        # Check data structure
        data = test_results.get("data", {})
        if data.get("success") is False:
            return False

        # Check individual test executions
        test_executions = test_results.get("test_executions", [])
        for test_execution in test_executions:
            test_result = test_execution.get("result", {})
            test_data = test_result.get("data", {})
            test_exec = test_data.get("test_execution", {})

            if not test_exec.get("success", True):
                return False

        return True

    def _generate_all_tests_basic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all types of tests (unit, integration, UI) for an entity."""
        entity = payload.get("entity", "Student")

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

    # ------------------------------------------------------------------
    # Internal helpers (keeping existing methods)
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
                + f"""
Generate comprehensive integration tests for the FastAPI routes including:
- CRUD operation tests (Create, Read, Update, Delete)
- HTTP status code validation
- Request/response schema validation
- Database interaction tests (mocked)
- Error handling tests
- Authentication/authorization tests (if applicable)
- Business rule enforcement tests

CRITICAL IMPORT REQUIREMENTS:
- Use 'from app.main import app' to import the FastAPI app (NOT 'from main import app')
- Use 'from fastapi.testclient import TestClient' for HTTP testing
- Mock database dependencies properly using: 'app.routes.{entity.lower()}_routes.get_db_connection'
- Import models as 'from app.routes.{entity.lower()}_routes import {entity}Create, {entity}Response'
- Use the correct file naming convention: {{entity_lower}}_routes.py (models are in the routes file)
- Note: BackendSWEA generates models inside the routes file, not separately

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

            # Run pytest with timeout and basic options to prevent hanging
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
                "--timeout=30",  # 30 second timeout per test
                "--maxfail=3",  # Stop after 3 failures to prevent hanging
            ]

            # Use a shorter timeout for the entire process
            result = subprocess.run(
                cmd,
                cwd=str(managed_system_path),
                capture_output=True,
                text=True,
                timeout=45,  # 45 second timeout for entire process
            )

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_file": test_file_path,
            }

        except subprocess.TimeoutExpired:
            print(f"⚠️  Test execution timed out for {test_file_path}")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test execution timed out after 45 seconds. This may indicate infinite loops or hanging tests.",
                "test_file": test_file_path,
                "timeout_error": True,
            }
        except FileNotFoundError:
            print(f"⚠️  Test file not found: {test_file_path}")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Test file not found: {test_file_path}",
                "test_file": test_file_path,
                "file_not_found": True,
            }
        except Exception as e:
            print(f"⚠️  Error executing tests for {test_file_path}: {str(e)}")
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error executing tests: {str(e)}",
                "test_file": test_file_path,
                "execution_error": True,
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
        execution_type = payload.get("execution_type", "standard")
        validate_after_changes = payload.get("validate_after_changes", False)

        try:
            managed_system_path = self.managed_system_manager.managed_system_path
            tests_dir = managed_system_path / "tests"

            if not tests_dir.exists():
                return self.create_error_response(
                    "execute_tests", f"No tests directory found for {entity}", "no_tests_found"
                )

            # Build test command
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

            # For evolution validation, focus on entity-specific tests
            if execution_type == "evolution_validation":
                entity_lower = entity.lower()
                test_pattern = entity_lower  # Fixed: Remove asterisks to avoid pytest syntax error
                cmd.extend(["-k", test_pattern])
                print(f"🧪 Running evolution validation tests for {entity} entity")

            import time

            start_time = time.time()

            result = subprocess.run(
                cmd,
                cwd=str(managed_system_path),
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for all tests
            )

            execution_time = time.time() - start_time
            tests_executed = self._count_tests_executed(result.stdout)
            tests_passed = (
                tests_executed
                if result.returncode == 0
                else self._count_tests_passed(result.stdout)
            )
            tests_failed = tests_executed - tests_passed

            response_data = {
                "tests_executed": tests_executed,
                "test_execution": {
                    "success": result.returncode == 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "tests_directory": str(tests_dir),
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed,
                    "execution_time": execution_time,
                    "execution_type": execution_type,
                    "entity": entity,
                },
            }

            if validate_after_changes:
                response_data["test_execution"]["validation_status"] = (
                    "passed" if result.returncode == 0 else "failed"
                )
                response_data["test_execution"]["evolution_validation"] = True

                if result.returncode != 0:
                    print(f"⚠️  Evolution validation tests failed for {entity}")
                else:
                    print(f"✅ Evolution validation tests passed for {entity}")

            return self.create_success_response("execute_tests", response_data)

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
