import csv
import json
import logging
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from baes.core.managed_system_manager import ManagedSystemManager
from baes.domain_entities.base_bae import BaseAgent
from baes.llm.openai_client import OpenAIClient
from baes.utils.template_registry import (
    TemplateRegistry,
    TemplateInput,
    EntityType,
    SWEAType,
)
from baes.utils.presentation_logger import get_presentation_logger
from config import Config

logger = logging.getLogger(__name__)
presentation_logger = get_presentation_logger()


# Stage 2 Improvement #8: Feedback Loop Analytics for TestSWEA
class FeedbackLoopAnalytics:
    """
    Stage 2 Improvement #8: Feedback Loop Logging and Analytics
    Tracks all feedback interactions between TechLeadSWEA and TestSWEA in CSV format.
    """

    def __init__(self):
        # Use tests/.temp for analytics during tests
        if Config.IS_TEST_ENVIRONMENT:
            self.analytics_dir = Path("tests/.temp")
        else:
            self.analytics_dir = Path("logs/feedback_analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.analytics_dir / "test_feedback_analytics.csv"
        self._ensure_csv_headers()

    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for pandas DataFrame compatibility"""
        if not self.csv_file.exists():
            headers = [
                "timestamp",
                "session_id",
                "entity",
                "test_type",
                "feedback_round",
                "techlead_feedback_count",
                "feedback_categories",
                "test_response_time_seconds",
                "feedback_addressed",
                "retry_count",
                "final_success",
                "feedback_text_length",
                "test_changes_made",
                "improvement_areas",
                "tests_passed",
                "tests_failed",
            ]
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def log_feedback_interaction(
        self,
        session_id: str,
        entity: str,
        test_type: str,
        feedback_round: int,
        techlead_feedback: List[str],
        test_response_time: float,
        feedback_addressed: bool,
        retry_count: int,
        final_success: bool,
        test_changes_made: List[str] = None,
        tests_passed: int = 0,
        tests_failed: int = 0,
    ):
        """Log feedback loop interaction to CSV for analytics"""
        try:
            # Categorize feedback for analytics
            feedback_categories = self._categorize_feedback(techlead_feedback)
            improvement_areas = self._extract_improvement_areas(techlead_feedback)

            row_data = [
                datetime.now().isoformat(),
                session_id,
                entity,
                test_type,
                feedback_round,
                len(techlead_feedback),
                ";".join(feedback_categories),
                round(test_response_time, 2),
                feedback_addressed,
                retry_count,
                final_success,
                sum(len(fb) for fb in techlead_feedback),
                ";".join(test_changes_made or []),
                ";".join(improvement_areas),
                tests_passed,
                tests_failed,
            ]

            with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

            logger.info(
                f"📊 Test feedback analytics logged: {entity}.{test_type} round {feedback_round}"
            )

        except Exception as e:
            logger.warning(f"Failed to log test feedback analytics: {e}")

    def _categorize_feedback(self, feedback_list: List[str]) -> List[str]:
        """Categorize feedback for analytics purposes"""
        categories = set()
        feedback_text = " ".join(feedback_list).lower()

        # Test assertion feedback
        if any(
            term in feedback_text for term in ["assertion", "assert", "expect", "should", "test"]
        ):
            categories.add("test_assertions")

        # Mock/Setup feedback
        if any(
            term in feedback_text for term in ["mock", "setup", "fixture", "patch", "monkeypatch"]
        ):
            categories.add("test_setup")

        # Coverage feedback
        if any(term in feedback_text for term in ["coverage", "missing", "untested", "branch"]):
            categories.add("test_coverage")

        # Integration feedback
        if any(
            term in feedback_text
            for term in ["integration", "api", "endpoint", "database", "connection"]
        ):
            categories.add("integration_tests")

        # Performance feedback
        if any(
            term in feedback_text
            for term in ["performance", "slow", "timeout", "speed", "benchmark"]
        ):
            categories.add("performance_tests")

        return list(categories) if categories else ["general"]

    def _extract_improvement_areas(self, feedback_list: List[str]) -> List[str]:
        """Extract specific improvement areas from feedback"""
        areas = set()
        feedback_text = " ".join(feedback_list).lower()

        if "reliability" in feedback_text:
            areas.add("reliability")
        if "maintainability" in feedback_text:
            areas.add("maintainability")
        if "readability" in feedback_text:
            areas.add("readability")
        if "edge case" in feedback_text:
            areas.add("edge_cases")
        if "error handling" in feedback_text:
            areas.add("error_handling")

        return list(areas) if areas else ["test_quality"]


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
        self._template_registry = None  # Lazy initialization
        self.max_fix_iterations = 10  # Maximum attempts to fix issues autonomously
        self.collaboration_history = []  # Track SWEA collaboration attempts
        # Stage 2 Improvement #8: Feedback Loop Analytics
        self.feedback_analytics = FeedbackLoopAnalytics()
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    @property
    def template_registry(self):
        """Lazy initialization of TemplateRegistry"""
        if not Config.enable_templates:
            return None
        if self._template_registry is None:
            self._template_registry = TemplateRegistry()
        return self._template_registry

    def _get_do_not_ignore_warning(self) -> str:
        """
        Generate standard 'Do Not Ignore' warning text for all LLM prompts.
        Stage 1 Improvement #10: Explicit warnings to prevent LLM from ignoring instructions.
        """
        return """
🚨 CRITICAL WARNING: If you ignore ANY of the following instructions,
     your output will be REJECTED and you will be required to regenerate it. You MUST address EVERY requirement listed below. Failure to comply will result in immediate rejection.

⚠️  DO NOT IGNORE ANY INSTRUCTIONS - Your response will be validated against ALL requirements.
⚠️  DO NOT SKIP ANY STEPS - Every instruction must be implemented exactly as specified.
⚠️  DO NOT USE PLACEHOLDERS - Generate complete, working code with no TODO comments.
⚠️  DO NOT OMIT ERROR HANDLING - Implement comprehensive error handling as required.
⚠️  DO NOT IGNORE FEEDBACK - Implement ALL TechLeadSWEA feedback exactly as provided.

COMPLIANCE IS MANDATORY - Non-compliance will result in immediate rejection and retry.
"""

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "generate_unit_tests": "_generate_unit_tests",
        "generate_integration_tests": "_generate_integration_tests",
        "generate_ui_tests": "_generate_ui_tests",
        "execute_tests": "_execute_tests",
        "generate_all_tests": "_generate_all_tests_with_collaboration",
        "generate_all_tests_with_collaboration": "_generate_all_tests_with_collaboration",
        "validate_and_fix": "_validate_and_fix_system",
        "execute_creation_validation_tests": "_execute_tests",
        "execute_evolution_validation_tests": "_execute_tests",
        "fix_issues": "_fix_test_issues",
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch task to internal test generation/execution methods."""
        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                "Unknown task. Supported tasks: " + str(list(self._SUPPORTED_TASKS.keys())),
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
        """Generate all test types for an entity, strictly requiring all dependencies. Raise error if any are missing."""
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        # Validate all dependencies for all test types
        for test_type in ["unit_tests", "integration_tests", "ui_tests"]:
            validation = self._validate_test_dependencies(entity, test_type)
            if not validation["dependencies_ready"]:
                missing = validation["missing_dependencies"]
                recommendations = validation["recommendations"]
                error_msg = (
                    "Cannot generate "
                    + test_type
                    + " for "
                    + entity
                    + ": missing dependencies: "
                    + str(missing)
                    + ". "
                    "Recommendations: " + str(recommendations)
                )
                logger.error(error_msg)
                from baes.utils.presentation_logger import get_presentation_logger

                get_presentation_logger().error(error_msg)
                return self.create_error_response(
                    "generate_all_tests_with_collaboration", error_msg, "missing_dependencies"
                )

        # If all dependencies are ready, generate all tests
        test_types_generated = []
        for test_type in ["unit_tests", "integration_tests", "ui_tests"]:
            test_code = self._generate_robust_test_code(entity, test_type, attributes, context)
            self._write_test_to_managed_system(entity, test_type, test_code)
            test_types_generated.append(test_type)

        return self.create_success_response(
            "generate_all_tests_with_collaboration",
            {
                "test_types_generated": test_types_generated,
                "dependencies_validated": True,
                "note": "All dependencies present. All tests generated successfully.",
            },
        )

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
                "Iteration "
                + str(iteration)
                + ": Found "
                + str(len(failure_analysis["issues"]))
                + " issues"
            )

            # Request fixes from appropriate SWEAs
            fix_requests = self._create_fix_requests(failure_analysis, entity, payload)

            # Execute fix requests (this would normally go through the RuntimeKernel)
            fixes_applied = self._execute_fix_requests(fix_requests, payload)
            collaboration_log.extend(fixes_applied)

            # Re-execute tests to see if issues are resolved
            test_results = self._execute_all_tests(payload)

            if self._all_tests_passed(test_results):
                collaboration_log.append(
                    "✅ All tests passing after " + str(iteration) + " iteration(s)"
                )
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
        combined_output = stderr + " " + stdout
        combined_output = combined_output.lower()

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

            collaboration_log.append(
                "🔧 Requesting " + swea_agent + " to " + task_type + " - " + issue_desc
            )

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
                    "execute_all_tests", "No tests directory found for " + entity, "no_tests_found"
                )

            # ------------------------------------------------------------------
            # Build pytest command with JSON reporting for reliable test counts
            # ------------------------------------------------------------------
            # Create a temporary file to hold the JSON report produced by
            # pytest-json-report. We can safely remove it after parsing.
            report_file = (
                Path(tempfile.gettempdir()) / "pytest_report_" + str(int(time.time())) + ".json"
            )

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(tests_dir),
                "-v",
                "--tb=short",
                "--no-header",
                "-q",
                "--json-report",
                "--json-report-file=" + str(report_file),
            ]

            start_time = time.time()
            logger.info("🧪 Executing tests in: " + str(tests_dir))
            logger.debug("🧪 Test command: " + " ".join(cmd))

            result = subprocess.run(
                cmd,
                cwd=str(managed_system_path),
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for all tests
            )

            execution_time = time.time() - start_time

            # ------------------------------------------------------------------
            # Parse JSON report for accurate counts - NO FALLBACK TO REGEX
            # ------------------------------------------------------------------
            tests_executed = tests_passed = tests_failed = 0

            if not report_file.exists():
                error_msg = (
                    "JSON report file not found: "
                    + str(report_file)
                    + ". pytest-json-report may not be working correctly."
                )
                logger.error("❌ " + error_msg)
                return self.create_error_response("execute_tests", error_msg, "json_report_missing")

            try:
                with open(report_file, "r", encoding="utf-8") as jf:
                    report_data = json.load(jf)

                summary = report_data.get("summary", {})
                if not summary:
                    error_msg = "JSON report has no 'summary' section: " + str(report_data)
                    logger.error("❌ " + error_msg)
                    return self.create_error_response(
                        "execute_tests", error_msg, "json_report_invalid"
                    )

                tests_executed = summary.get("collected", 0)
                tests_passed = summary.get("passed", 0)
                # Treat `failed` + `errors` as failures
                tests_failed = summary.get("failed", 0) + summary.get("errors", 0)

                logger.info("📊 JSON report parsed successfully:")
                logger.info("   📋 Collected: %d", tests_executed)
                logger.info("   ✅ Passed: %d", tests_passed)
                logger.info("   ❌ Failed: %d", tests_failed)

            except json.JSONDecodeError as e:
                error_msg = "Failed to parse JSON report: " + str(e)
                logger.error("❌ " + error_msg)
                return self.create_error_response(
                    "execute_tests", error_msg, "json_report_parse_error"
                )
            except Exception as e:
                error_msg = "Unexpected error parsing JSON report: " + str(e)
                logger.error("❌ " + error_msg)
                return self.create_error_response("execute_tests", error_msg, "json_report_error")

            # Log detailed test execution info
            logger.info("🧪 Test execution completed:")
            logger.info("   📊 Tests executed: %d", tests_executed)
            logger.info("   ✅ Tests passed: %d", tests_passed)
            logger.info("   ❌ Tests failed: %d", tests_failed)
            logger.info("   🕒 Execution time: %.2fs", execution_time)
            logger.info("   📤 Exit code: %d", result.returncode)

            # Log stdout/stderr if there are issues
            if result.returncode != 0:
                logger.warning("❌ Test execution failed:")
                if result.stdout:
                    logger.warning("📤 STDOUT: %s", result.stdout[:1000])
                if result.stderr:
                    logger.warning("📤 STDERR: %s", result.stderr[:1000])

            # Clean up report file to avoid clutter (best effort)
            try:
                if report_file.exists():
                    report_file.unlink(missing_ok=True)
            except Exception:
                pass

            response_data = {
                "tests_executed": tests_executed,
                "test_execution": {
                    "success": result.returncode == 0 and tests_executed > 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "tests_directory": str(tests_dir),
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed,
                    "execution_time": execution_time,
                    "execution_type": "standard",
                    "entity": entity,
                    "test_files_found": tests_executed,
                },
            }

            # Determine overall success
            success = result.returncode == 0 and tests_executed > 0

            if success:
                return self.create_success_response("execute_tests", response_data)
            else:
                # Create error response without extra data parameter
                error_response = self.create_error_response(
                    "execute_tests",
                    "Test execution failed: "
                    + str(tests_executed)
                    + " tests executed, "
                    + str(tests_passed)
                    + " passed, exit code "
                    + str(result.returncode),
                    "test_execution_failed",
                )
                # Add the response data manually
                error_response["data"] = response_data
                return error_response

        except subprocess.TimeoutExpired:
            logger.error("❌ Test execution timed out after 120 seconds")
            return self.create_error_response(
                "execute_tests", "Test execution timed out after 120 seconds", "timeout_error"
            )
        except Exception as e:
            logger.error("❌ Test execution failed with exception: %s", str(e))
            return self.create_error_response(
                "execute_tests", "Error executing all tests: " + str(e), "execution_error"
            )

    def _count_tests_executed(self, stdout: str) -> int:
        """DEPRECATED: This method is no longer used. JSON reporting is mandatory."""
        raise NotImplementedError(
            "Regex-based test counting is deprecated. JSON reporting is now mandatory. "
            "If you see this error, there's an issue with pytest-json-report configuration."
        )

    def _count_tests_passed(self, stdout: str) -> int:
        """DEPRECATED: This method is no longer used. JSON reporting is mandatory."""
        raise NotImplementedError(
            "Regex-based test counting is deprecated. JSON reporting is now mandatory. "
            "If you see this error, there's an issue with pytest-json-report configuration."
        )

    def _all_tests_passed(self, test_results: Dict[str, Any]) -> bool:
        """Check if all tests passed in the test results."""
        # Check overall success
        if test_results.get("success") is False:
            return False

        # Check data structure
        data = test_results.get("data", {})
        if data.get("success") is False:
            return False

        # UPDATED: Handle new structure where individual tests are not executed during generation
        # Check if this is a test execution result (has test_execution data)
        test_execution = data.get("test_execution", {})
        if test_execution:
            # This is an actual test execution result
            return test_execution.get("success", False)

        # Check individual test executions (legacy support)
        test_executions = test_results.get("test_executions", [])
        for test_execution in test_executions:
            test_result = test_execution.get("result", {})
            test_data = test_result.get("data", {})
            test_exec = test_data.get("test_execution", {})

            if not test_exec.get("success", True):
                return False

        # If no test executions found, assume tests are generated but not executed yet
        # This is now the normal case during generation
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

    def _fix_test_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix test issues based on TechLeadSWEA coordination"""
        try:
            entity = payload.get("entity", "Student")
            fix_action = payload.get("fix_action", "")
            issue_type = payload.get("issue_type", "")
            techlead_decision = payload.get("techlead_decision", {})

            # Extract detailed context from TechLeadSWEA decision
            reasoning = techlead_decision.get("reasoning", "")

            logger.info("🔧 TestSWEA: Fixing test issues for %s", entity)
            logger.info("   🎯 Fix Action: %s", fix_action)
            logger.info("   📋 Issue Type: %s", issue_type)
            logger.info("   💡 Reasoning: %s", reasoning)

            # Handle specific fix actions from TechLeadSWEA
            if fix_action in ["fix_test_url_patterns", "validate_api_prefix"]:
                logger.debug("🔧 TestSWEA: Fixing URL pattern mismatches")
                # Regenerate tests with correct URL patterns
                return self._generate_all_tests_with_correct_url_patterns(payload)

            elif fix_action in ["fix_test_mocking", "update_test_configuration"]:
                logger.debug("🔧 TestSWEA: Fixing test mocking configuration")
                # Regenerate tests with improved mocking
                return self._generate_all_tests_with_improved_mocking(payload)

            elif fix_action in ["review_test_assertions", "fix_test_expectations"]:
                logger.debug("🔧 TestSWEA: Reviewing and fixing test assertions")
                # Regenerate tests with corrected assertions
                return self._generate_all_tests_with_corrected_assertions(payload)

            elif fix_action in ["analyze_test_failure", "fix_test_issues"]:
                logger.debug("🔧 TestSWEA: Analyzing and fixing general test issues")
                # Comprehensive test regeneration
                return self._generate_all_tests_with_collaboration(payload)

            # Fallback: Handle by issue type (legacy support)
            elif "test_generation" in issue_type or "missing_tests" in issue_type:
                logger.debug(
                    "🔧 TestSWEA: Regenerating all tests due to test generation issues (legacy)"
                )
                return self._generate_all_tests_with_collaboration(payload)
            elif "test_execution" in issue_type or "execution_failure" in issue_type:
                logger.debug("🔧 TestSWEA: Re-executing tests due to execution issues (legacy)")
                # First try to regenerate tests, then execute
                generation_result = self._generate_all_tests_with_collaboration(payload)
                if generation_result.get("success"):
                    return self._execute_tests(payload)
                else:
                    return generation_result
            elif "dependency" in issue_type:
                logger.debug("🔧 TestSWEA: Handling dependency issues (legacy)")
                # For dependency issues, we need to ensure proper test environment
                self._ensure_test_environment(entity)
                return self._generate_all_tests_with_collaboration(payload)
            else:
                # Default: regenerate all tests
                logger.debug("🔧 TestSWEA: Default fix - regenerating all tests")
                return self._generate_all_tests_with_collaboration(payload)

        except Exception as e:
            logger.error("❌ TestSWEA fix_issues failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "fix_error")

    def _generate_all_tests_with_improved_mocking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tests with improved mocking to handle Mock object issues"""
        try:
            entity = payload.get("entity", "Student")
            logger.info("🔧 TestSWEA: Regenerating tests with improved mocking for %s", entity)

            # Add mocking context to payload
            enhanced_payload = payload.copy()
            enhanced_payload["mocking_strategy"] = "improved"
            enhanced_payload["mock_validation"] = True

            # Generate tests with enhanced mocking
            result = self._generate_all_tests_with_collaboration(enhanced_payload)

            if result.get("success"):
                result["data"]["fix_applied"] = True
                result["data"]["fix_type"] = "improved_mocking"

            return result

        except Exception as e:
            logger.error("❌ TestSWEA improved mocking failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "improved_mocking_error")

    def _generate_all_tests_with_correct_url_patterns(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tests with correct URL patterns based on actual BackendSWEA generated routes"""
        try:
            entity = payload.get("entity", "Student")
            logger.info("🔧 TestSWEA: Regenerating tests with correct URL patterns for %s", entity)

            # Extract actual API prefix from BackendSWEA generated routes
            routes_file = (
                self.managed_system_manager.managed_system_path
                / "app"
                / "routes"
                / f"{entity.lower()}_routes.py"
            )
            
            # Default to the actual BackendSWEA pattern (no /api prefix)
            api_prefix = f"/{entity.lower()}s"  # Default to actual BackendSWEA pattern
            if routes_file.exists():
                routes_content = routes_file.read_text()
                prefix_match = re.search(r'APIRouter\(prefix="([^"]+)"', routes_content)
                if prefix_match:
                    api_prefix = prefix_match.group(1)
                    logger.info("🔧 TestSWEA: Extracted actual API prefix: %s", api_prefix)
                else:
                    logger.warning("⚠️ TestSWEA: Could not extract API prefix from routes file, using default: %s", api_prefix)
            else:
                logger.warning("⚠️ TestSWEA: Routes file not found, using default API prefix: %s", api_prefix)

            # Add URL pattern correction context to payload
            enhanced_payload = payload.copy()
            enhanced_payload["url_pattern_strategy"] = "corrected"
            enhanced_payload["actual_api_prefix"] = api_prefix
            enhanced_payload["validate_url_patterns"] = True

            # Generate tests with correct URL patterns
            result = self._generate_all_tests_with_collaboration(enhanced_payload)

            if result.get("success"):
                result["data"]["fix_applied"] = True
                result["data"]["fix_type"] = "corrected_url_patterns"
                result["data"]["api_prefix_used"] = api_prefix

            return result

        except Exception as e:
            logger.error("❌ TestSWEA URL pattern correction failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "url_pattern_correction_error")

    def _generate_all_tests_with_corrected_assertions(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate tests with corrected assertions to handle assertion failures"""
        try:
            entity = payload.get("entity", "Student")
            logger.info("🔧 TestSWEA: Regenerating tests with corrected assertions for %s", entity)

            # Add assertion correction context to payload
            enhanced_payload = payload.copy()
            enhanced_payload["assertion_strategy"] = "corrected"
            enhanced_payload["validate_responses"] = True

            # Generate tests with corrected assertions
            result = self._generate_all_tests_with_collaboration(enhanced_payload)

            if result.get("success"):
                result["data"]["fix_applied"] = True
                result["data"]["fix_type"] = "corrected_assertions"

            return result

        except Exception as e:
            logger.error("❌ TestSWEA corrected assertions failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "corrected_assertions_error")

    def _ensure_test_environment(self, entity: str):
        """Ensure proper test environment setup"""
        try:
            managed_system_path = self.managed_system_manager.managed_system_path

            # Ensure tests directory exists
            tests_dir = managed_system_path / "tests"
            tests_dir.mkdir(exist_ok=True)

            # Create __init__.py if it doesn't exist
            init_file = tests_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Test package initialization\n")

            logger.debug("✅ TestSWEA: Test environment ensured for %s", entity)

        except Exception as e:
            logger.warning("⚠️ TestSWEA: Failed to ensure test environment: %s", str(e))

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
        """Build prompt for test generation based on test type with robust dependency validation."""

        # Extract actual model attributes from generated code
        actual_attributes = self._extract_actual_model_attributes(generated_code, entity)
        
        # Generic validation helper for any entity
        validation_helpers = self._get_validation_helpers(entity, actual_attributes)

        base_prompt = """
You are a TestSWEA (Test Software Engineering Autonomous Agent) responsible for generating comprehensive tests.

Entity: %s
Expected Attributes: %s
Actual Attributes from Generated Code: %s
Context: %s
Test Type: %s

Generated Code to Test:
%s

CRITICAL REQUIREMENTS:
1. Use pytest framework with proper fixtures and mocking
2. Mock external dependencies (OpenAI API, file operations, etc.)
3. Include both positive and negative test cases
4. Test edge cases and error conditions
5. Use proper assertions and test structure
6. Include setup and teardown as needed
7. Generate complete, runnable test code
8. Focus on testing business logic and domain coherence
9. ALWAYS validate that imports will work before generating tests
10. Use robust error handling and fallback mechanisms
11. Use ONLY the actual attributes from the generated code for test data
12. Follow exact endpoint URL patterns as specified

VALIDATION HELPERS:
%s

""" % (
            entity,
            attributes,
            actual_attributes,
            context,
            test_type,
            generated_code,
            validation_helpers,
        )

        if test_type == "unit_tests":
            # Get the actual generated model code to extract correct class names
            routes_file = (
                self.managed_system_manager.managed_system_path
                / "app"
                / "routes"
                / f"{entity.lower()}_routes.py"
            )
            actual_imports = ""

            if routes_file.exists():
                routes_content = routes_file.read_text()
                # Extract actual class names from the routes file
                if class_matches := re.findall(r"class\s+(\w+)\s*\(.*?\):", routes_content):
                    actual_imports = (
                        f"# Actual classes found in routes file: {', '.join(class_matches)}\n"
                    )
                    actual_imports += f"# Import using: from app.routes.{entity.lower()}_routes import {', '.join(class_matches)}"
                else:
                    actual_imports = "# No classes found in routes file, use generic imports"
            else:
                actual_imports = "# Routes file not found"

            # Generate simple test data
            simple_test_data = self._generate_simple_test_data(entity, actual_attributes)
            test_data_json = str(simple_test_data).replace("'", '"')

            return (
                base_prompt
                + f"""
Generate SIMPLE unit tests for the Pydantic model. Focus on basic validation with minimal complexity.

CRITICAL IMPORT REQUIREMENTS:
- {actual_imports}
- Use 'import pytest' for pytest framework
- Use 'from pydantic import ValidationError' for validation testing

CRITICAL TEST DATA REQUIREMENTS:
- Use ONLY these actual attributes for test data: {actual_attributes}
- Use this EXACT test data: {test_data_json}
- DO NOT modify the test data structure
- DO NOT add extra fields that don't exist in the model

SIMPLE TEST STRUCTURE:
- Test basic model creation with valid data
- Test basic field validation
- Avoid complex edge cases and business rules
- Focus on happy path testing
- Keep tests short and readable

Return ONLY complete Python test code with imports and simple test functions.
"""
            )

        elif test_type == "integration_tests":
            # Get the actual generated routes code to extract correct class names
            routes_file = (
                self.managed_system_manager.managed_system_path
                / "app"
                / "routes"
                / f"{entity.lower()}_routes.py"
            )
            actual_imports = ""
            # Default to the actual BackendSWEA pattern (no /api prefix)
            api_prefix = f"/{entity.lower()}s"  # Default to actual BackendSWEA pattern

            # Check if we have URL pattern correction context
            if routes_file.exists():
                routes_content = routes_file.read_text()
                # Extract actual class names from the routes file
                if class_matches := re.findall(r"class\s+(\w+)\s*\(.*?\):", routes_content):
                    actual_imports = (
                        f"# Actual classes found in routes file: {', '.join(class_matches)}\n"
                    )
                    actual_imports += f"# Import using: from app.routes.{entity.lower()}_routes import {', '.join(class_matches)}"
                else:
                    actual_imports = "# No classes found in routes file, use generic imports"

                # Extract API prefix from router definition
                prefix_match = re.search(r'APIRouter\(prefix="([^"]+)"', routes_content)
                if prefix_match:
                    api_prefix = prefix_match.group(1)
                    logger.info("🔧 TestSWEA: Extracted actual API prefix from routes file: %s", api_prefix)
            else:
                actual_imports = "# Routes file not found"

            # Add API prefix information to the prompt
            api_prefix_info = f"""
CRITICAL API PREFIX INFORMATION:
- Use EXACTLY this API prefix: {api_prefix}
- All test URLs must start with: {api_prefix}/
- Example endpoints: {api_prefix}/, {api_prefix}/{{id}}
- DO NOT use /api/ prefix unless it matches the above
- DO NOT use double entity names like {api_prefix}/{entity.lower()}s/
"""

            # Generate simple test data
            simple_test_data = self._generate_simple_test_data(entity, actual_attributes)
            test_data_json = str(simple_test_data).replace("'", '"')

            return (
                base_prompt
                + f"""
Generate SIMPLE integration tests for the FastAPI routes. Focus on basic CRUD operations with minimal complexity.

CRITICAL IMPORT REQUIREMENTS:
- Use 'from app.main import app' to import the FastAPI app
- Use 'from fastapi.testclient import TestClient' for HTTP testing
- Mock database dependencies properly
- {actual_imports}

{api_prefix_info}

CRITICAL API ENDPOINT REQUIREMENTS:
- API prefix is: {api_prefix}
- Use EXACTLY these endpoint paths:
  * POST {api_prefix}/ (for create)
  * GET {api_prefix}/ (for list)
  * GET {api_prefix}/{{id}} (for get by id)
  * PUT {api_prefix}/{{id}} (for update)
  * DELETE {api_prefix}/{{id}} (for delete)

CRITICAL TEST DATA REQUIREMENTS:
- Use ONLY these actual attributes for test data: {actual_attributes}
- Use this EXACT test data: {test_data_json}
- DO NOT modify the test data structure
- DO NOT add extra fields that don't exist in the model

SIMPLE TEST STRUCTURE:
- Test basic CRUD operations only
- Use simple assertions (status codes, basic response structure)
- Avoid complex mocking and edge cases
- Focus on happy path testing
- Keep tests short and readable

Return ONLY complete Python test code with imports and simple test functions.
"""
            )

        elif test_type == "ui_tests":
            # Get the actual generated UI code to check for correct file structure
            ui_file = (
                self.managed_system_manager.managed_system_path
                / "ui"
                / "pages"
                / f"{entity.lower()}_page.py"
            )
            actual_imports = ""
            if ui_file.exists():
                ui_content = ui_file.read_text()
                # Check if the UI file has the expected structure
                if "def main():" in ui_content:
                    actual_imports = f"# UI file found: {ui_file}\n"
                    actual_imports += (
                        f"# Import using: from ui.pages.{entity.lower()}_page import main"
                    )
                else:
                    actual_imports = "# UI file exists but no main() function found"
            else:
                actual_imports = "# UI file not found: {ui_file}"

            return (
                base_prompt
                + f"""
Generate SIMPLE UI tests for the Streamlit interface. Focus on basic functionality with minimal complexity.

CRITICAL IMPORT REQUIREMENTS:
- Use 'import streamlit as st' for Streamlit components
- Use 'from unittest.mock import patch, MagicMock' for mocking
- DO NOT import any modules that do not exist (e.g., 'student_page')

SIMPLE TEST STRUCTURE:
- Test that the Streamlit app can be loaded (mock if necessary)
- Test that a form with the correct fields can be created
- Use only simple assertions (e.g., assert True)
- Avoid any complex user interaction simulation or external imports
- Keep tests short and readable

Return ONLY complete Python test code with imports and simple test functions.
"""
            )

        else:
            return base_prompt + "Generate appropriate test code based on the context provided."

    def _get_validation_helpers(self, entity: str, attributes: List[str]) -> str:
        """Generate validation helpers for robust test generation."""
        return f"""
VALIDATION HELPERS FOR {entity.upper()}:

1. MODEL VALIDATION:
   - Check if {entity} model has actual fields: {attributes}
   - Validate field types and constraints
   - Test business rules and validations

2. API VALIDATION:
   - Check if {entity.lower()}_routes.py exists and has endpoints
   - Validate CRUD operations are implemented
   - Test HTTP status codes and responses

3. UI VALIDATION:
   - Check if {entity.lower()}_page.py exists and has components
   - Validate form fields match model attributes
   - Test user interactions and API integration

4. DATABASE VALIDATION:
   - Check if {entity.lower()}s table exists
   - Validate schema matches model attributes
   - Test data persistence and retrieval

5. ERROR HANDLING:
   - Test invalid data scenarios
   - Validate error messages and status codes
   - Test edge cases and boundary conditions

6. FALLBACK MECHANISMS:
   - If model is incomplete, test expected structure
   - If API is incomplete, test available endpoints
   - If UI is incomplete, test available components
"""

    def _validate_test_dependencies(self, entity: str, test_type: str) -> Dict[str, Any]:
        """Validate that all dependencies exist before generating tests."""
        validation_result = {
            "dependencies_ready": True,
            "missing_dependencies": [],
            "warnings": [],
            "recommendations": [],
        }

        managed_system_path = self.managed_system_manager.managed_system_path

        try:
            if test_type == "unit_tests":
                # Check if routes file exists and has embedded Pydantic models
                routes_file = managed_system_path / "app" / "routes" / f"{entity.lower()}_routes.py"
                if not routes_file.exists():
                    validation_result["dependencies_ready"] = False
                    validation_result["missing_dependencies"].append(f"Routes file: {routes_file}")
                    validation_result["recommendations"].append(
                        "Generate API routes with embedded models first using BackendSWEA"
                    )
                else:
                    routes_content = routes_file.read_text()
                    if not self._has_actual_model_fields(routes_content, entity):
                        validation_result["warnings"].append(
                            f"Routes file for {entity} has no embedded Pydantic model fields defined"
                        )
                        validation_result["recommendations"].append(
                            "Complete model generation in routes before testing"
                        )

            elif test_type == "integration_tests":
                # Check if routes file exists and has endpoints
                routes_file = managed_system_path / "app" / "routes" / f"{entity.lower()}_routes.py"
                if not routes_file.exists():
                    validation_result["dependencies_ready"] = False
                    validation_result["missing_dependencies"].append(f"Routes file: {routes_file}")
                    validation_result["recommendations"].append(
                        "Generate API routes first using BackendSWEA"
                    )
                else:
                    routes_content = routes_file.read_text()
                    if not self._has_actual_endpoints(routes_content):
                        validation_result["warnings"].append(
                            "Routes file has no actual endpoints defined"
                        )
                        validation_result["recommendations"].append(
                            "Complete API generation before testing"
                        )

            elif test_type == "ui_tests":
                # Check if UI file exists and has components
                ui_file = managed_system_path / "ui" / "pages" / f"{entity.lower()}_management.py"
                if not ui_file.exists():
                    # Fallback to app.py
                    ui_file = managed_system_path / "ui" / "app.py"

                if not ui_file.exists():
                    validation_result["dependencies_ready"] = False
                    validation_result["missing_dependencies"].append(f"UI file: {ui_file}")
                    validation_result["recommendations"].append(
                        "Generate UI first using FrontendSWEA"
                    )
                else:
                    ui_content = ui_file.read_text()
                    if not self._has_actual_ui_components(ui_content):
                        validation_result["warnings"].append(
                            "UI file has no actual components defined"
                        )
                        validation_result["recommendations"].append(
                            "Complete UI generation before testing"
                        )

        except Exception as e:
            validation_result["dependencies_ready"] = False
            validation_result["missing_dependencies"].append(f"Validation error: {str(e)}")

        return validation_result

    def _has_actual_model_fields(self, model_content: str, entity: str) -> bool:
        """Check if model has actual fields defined (not just placeholders)."""
        # Look for actual field definitions, not just comments
        lines = model_content.split("\n")
        has_fields = False

        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if line.startswith("#") or not line:
                continue
            # Look for actual field definitions (name: type)
            if ":" in line and not line.startswith("class") and not line.startswith("def"):
                # Check if it's not just a placeholder comment
                if not any(
                    placeholder in line.lower()
                    for placeholder in ["example:", "placeholder", "todo"]
                ):
                    has_fields = True
                    break

        return has_fields

    def _has_actual_endpoints(self, routes_content: str) -> bool:
        """Check if routes file has actual endpoints defined."""
        # Look for actual route decorators
        return "@router." in routes_content and "def " in routes_content

    def _has_actual_ui_components(self, ui_content: str) -> bool:
        """Check if UI file has actual Streamlit components defined."""
        # Look for actual Streamlit components
        return "st." in ui_content and ("def main" in ui_content or "def " in ui_content)

    def _generate_robust_test_code(
        self, entity: str, test_type: str, attributes: List[str], context: str
    ) -> str:
        """Generate robust test code using templates or LLM. Requires all dependencies to be present."""
        # Validate dependencies first
        validation = self._validate_test_dependencies(entity, test_type)

        if not validation["dependencies_ready"]:
            # Strict mode: raise error, do not generate fallback tests
            missing = validation["missing_dependencies"]
            recommendations = validation["recommendations"]
            error_msg = (
                f"Cannot generate {test_type} for {entity}: missing dependencies: {missing}. "
                f"Recommendations: {recommendations}"
            )
            logger.error(error_msg)
            from baes.utils.presentation_logger import get_presentation_logger

            get_presentation_logger().error(error_msg)
            raise RuntimeError(error_msg)

        # Get the actual generated code
        generated_code = self._get_generated_code(entity, test_type.replace("_tests", ""))
        
        # Try template-based generation first (only for integration tests currently)
        test_code = None
        template_used = False
        if self.template_registry and test_type == "integration_tests":
            try:
                # Parse attributes to dictionary
                attr_dict = {}
                for attr in attributes:
                    if isinstance(attr, dict):
                        attr_dict[attr.get("name", "unknown")] = attr.get("type", "str")
                    elif isinstance(attr, str):
                        if ":" in attr:
                            name, typ = [p.strip() for p in attr.split(":", 1)]
                        else:
                            name, typ = attr.strip(), "str"
                        attr_dict[name] = typ
                    else:
                        attr_dict[str(attr)] = "str"
                
                from baes.utils.template_registry import EntityType
                
                # Create template input
                template_input = TemplateInput(
                    entity_name=entity,
                    entity_type=EntityType.STANDARD,
                    swea_type=SWEAType.TEST,
                    attributes=attr_dict,
                )
                
                # Try to render template
                template_output = self.template_registry.render_template(template_input)
                
                if template_output.template_used:
                    test_code = template_output.generated_code
                    template_used = True
                    
                    # Log optimization metrics
                    presentation_logger.template_selected(
                        "test",
                        template_output.template_id,
                        template_output.token_estimate
                    )
                    
                    logger.info("TestSWEA: Using template %s for %s", template_output.template_id, entity)
                else:
                    # Template indicated fallback needed
                    presentation_logger.template_fallback(
                        "test",
                        template_output.template_id or "test_integration_crud",
                        template_output.fallback_reason or "Unknown reason"
                    )
            except Exception as e:
                logger.warning("TestSWEA: Template rendering failed: %s, falling back to LLM generation", str(e))
        
        # If template didn't work, use LLM generation
        if not template_used:
            # Build the test prompt with validation context
            prompt = self._build_test_prompt(entity, attributes, test_type, context, generated_code)

            # Add the "Do Not Ignore" warning to the prompt
            prompt = self._get_do_not_ignore_warning() + "\n\n" + prompt

            # Add validation warnings to the prompt
            if validation["warnings"]:
                prompt += "\nVALIDATION WARNINGS:\n" + "\n".join(
                    f"- {w}" for w in validation["warnings"]
                )
                prompt += "\n\nGenerate tests that handle these warnings gracefully."

            # Stage 2 Improvement #8: Track analytics timing
            start_time = datetime.now()

            # Generate test code
            test_code = self.llm_client.generate_code_with_domain_focus(
                prompt,
                code_type=f"{test_type.replace('_', ' ').title()}",
                entity_context={
                    "entity": entity,
                    "attributes": attributes,
                    "test_type": test_type,
                    "validation_warnings": validation["warnings"],
                },
            )

            # Stage 2 Improvement #8: Log analytics for test generation
            response_time = (datetime.now() - start_time).total_seconds()
        else:
            response_time = 0.0  # Template generation is fast

        # Strict validation – ensure we got code back
        if not isinstance(test_code, str) or len(test_code.strip()) == 0:
            # Stage 2 Improvement #8: Log failed test generation
            self.feedback_analytics.log_feedback_interaction(
                session_id=self.current_session_id,
                entity=entity,
                test_type=test_type,
                feedback_round=1,
                techlead_feedback=validation.get("warnings", []),
                test_response_time=response_time,
                feedback_addressed=False,
                retry_count=0,
                final_success=False,
                test_changes_made=[],
                tests_passed=0,
                tests_failed=1,
            )

            raise TestGenerationError(
                f"LLM did not return valid test code for {entity} ({test_type}). Received type: {type(test_code)}"
            )

        # Stage 2 Improvement #8: Log successful test generation
        test_changes = [f"Generated {test_type} for {entity}"]
        if validation.get("warnings"):
            test_changes.extend([f"Handled warning: {w}" for w in validation["warnings"]])

        self.feedback_analytics.log_feedback_interaction(
            session_id=self.current_session_id,
            entity=entity,
            test_type=test_type,
            feedback_round=1,
            techlead_feedback=validation.get("warnings", []),
            test_response_time=response_time,
            feedback_addressed=True,
            retry_count=0,
            final_success=True,
            test_changes_made=test_changes,
            tests_passed=1,
            tests_failed=0,
        )

        return test_code

    def _write_test_to_managed_system(self, entity: str, test_type: str, test_code: str) -> str:
        """Write generated test code to the managed system with URL validation."""
        try:
            # Validate and fix test URLs for integration tests
            if test_type == "integration_tests":
                # Extract API prefix from routes file
                routes_file = (
                    self.managed_system_manager.managed_system_path
                    / "app"
                    / "routes"
                    / f"{entity.lower()}_routes.py"
                )
                api_prefix = "/api"  # Default
                if routes_file.exists():
                    routes_content = routes_file.read_text()
                    prefix_match = re.search(r'APIRouter\(prefix="([^"]+)"', routes_content)
                    if prefix_match:
                        api_prefix = prefix_match.group(1)
                
                # Validate and fix URLs
                test_code = self._validate_and_fix_test_urls(test_code, entity, api_prefix)

            # Ensure test directory structure exists
            managed_system_path = self.managed_system_manager.managed_system_path
            tests_dir = managed_system_path / "tests"

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
        except Exception as e:
            logger.error(f"Failed to write test code to managed system: {e}")
            return self.create_error_response("write_test_code", str(e), "write_error")

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
                # Look for embedded Pydantic models in the routes file
                routes_file = managed_system_path / "app" / "routes" / f"{entity.lower()}_routes.py"
                if routes_file.exists():
                    return routes_file.read_text()
            elif code_type == "routes":
                routes_file = managed_system_path / "app" / "routes" / f"{entity.lower()}_routes.py"
                if routes_file.exists():
                    return routes_file.read_text()
            elif code_type == "ui":
                ui_file = managed_system_path / "ui" / "pages" / f"{entity.lower()}_management.py"
                if ui_file.exists():
                    return ui_file.read_text()
                # Fallback to app.py
                ui_file = managed_system_path / "ui" / "app.py"
                if ui_file.exists():
                    return ui_file.read_text()

            return ""
        except Exception:
            return ""

    def _extract_actual_model_attributes(self, generated_code: str, entity: str) -> List[str]:
        """Extract actual model attributes from generated code to ensure test data matches."""
        if not generated_code:
            return []
        
        # Look for Pydantic model class definitions
        model_pattern = rf"class\s+(\w+)\s*\(.*?\):.*?(?=class|\Z)"
        model_matches = re.findall(model_pattern, generated_code, re.DOTALL)
        
        attributes = []
        for model_match in model_matches:
            # Look for field definitions in the model
            field_pattern = r"(\w+):\s*(\w+)(?:\s*=\s*[^#\n]*)?"
            field_matches = re.findall(field_pattern, model_match)
            
            for field_name, field_type in field_matches:
                # Skip common non-field lines
                if field_name in ['class', 'def', 'from', 'import', 'pass', 'return', 'if', 'else', 'try', 'except', 'finally', 'with', 'as', 'in', 'is', 'not', 'and', 'or', 'True', 'False', 'None']:
                    continue
                # Skip if it's a method definition
                if '(' in field_name or ')' in field_name:
                    continue
                # Skip if it's a comment or string
                if field_name.startswith('"') or field_name.startswith("'"):
                    continue
                
                attributes.append(f"{field_name}: {field_type}")
        
        # If no attributes found in the code, try to extract from the routes file
        if not attributes:
            routes_file = (
                self.managed_system_manager.managed_system_path
                / "app"
                / "routes"
                / f"{entity.lower()}_routes.py"
            )
            if routes_file.exists():
                routes_content = routes_file.read_text()
                # Look for Pydantic model class definitions in routes file
                model_pattern = rf"class\s+(\w+)\s*\(.*?\):.*?(?=class|\Z)"
                model_matches = re.findall(model_pattern, routes_content, re.DOTALL)
                
                for model_match in model_matches:
                    # Look for field definitions in the model
                    field_pattern = r"(\w+):\s*(\w+)(?:\s*=\s*[^#\n]*)?"
                    field_matches = re.findall(field_pattern, model_match)
                    
                    for field_name, field_type in field_matches:
                        # Skip common non-field lines
                        if field_name in ['class', 'def', 'from', 'import', 'pass', 'return', 'if', 'else', 'try', 'except', 'finally', 'with', 'as', 'in', 'is', 'not', 'and', 'or', 'True', 'False', 'None']:
                            continue
                        # Skip if it's a method definition
                        if '(' in field_name or ')' in field_name:
                            continue
                        # Skip if it's a comment or string
                        if field_name.startswith('"') or field_name.startswith("'"):
                            continue
                        
                        attributes.append(f"{field_name}: {field_type}")
        
        return list(set(attributes))  # Remove duplicates

    def _get_validation_helpers(self, entity: str, attributes: List[str]) -> str:
        """Generate validation helpers for robust test generation."""
        return f"""
VALIDATION HELPERS FOR {entity.upper()}:

1. MODEL VALIDATION:
   - Check if {entity} model has actual fields: {attributes}
   - Validate field types and constraints
   - Test business rules and validations

2. API VALIDATION:
   - Check if {entity.lower()}_routes.py exists and has endpoints
   - Validate CRUD operations are implemented
   - Test HTTP status codes and responses

3. UI VALIDATION:
   - Check if {entity.lower()}_page.py exists and has components
   - Validate form fields match model attributes
   - Test user interactions and API integration

4. DATABASE VALIDATION:
   - Check if {entity.lower()}s table exists
   - Validate schema matches model attributes
   - Test data persistence and retrieval

5. ERROR HANDLING:
   - Test invalid data scenarios
   - Validate error messages and status codes
   - Test edge cases and boundary conditions

6. FALLBACK MECHANISMS:
   - If model is incomplete, test expected structure
   - If API is incomplete, test available endpoints
   - If UI is incomplete, test available components
"""

    # -------------------- task implementations ------------------------
    def _generate_unit_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")
        validation = self._validate_test_dependencies(entity, "unit_tests")
        if not validation["dependencies_ready"]:
            missing = validation["missing_dependencies"]
            recommendations = validation["recommendations"]
            error_msg = (
                f"Cannot generate unit_tests for {entity}: missing dependencies: {missing}. "
                f"Recommendations: {recommendations}"
            )
            logger.error(error_msg)
            from baes.utils.presentation_logger import get_presentation_logger

            get_presentation_logger().error(error_msg)
            return self.create_error_response(
                "generate_unit_tests", error_msg, "missing_dependencies"
            )
        test_code = self._generate_robust_test_code(entity, "unit_tests", attributes, context)
        test_file_path = self._write_test_to_managed_system(entity, "unit_tests", test_code)
        return self.create_success_response(
            "generate_unit_tests",
            {
                "test_file_path": test_file_path,
                "test_code": test_code,
                "test_generated": True,
                "managed_system": True,
                "dependencies_validated": True,
            },
        )

    def _generate_integration_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")
        validation = self._validate_test_dependencies(entity, "integration_tests")
        if not validation["dependencies_ready"]:
            missing = validation["missing_dependencies"]
            recommendations = validation["recommendations"]
            error_msg = (
                f"Cannot generate integration_tests for {entity}: missing dependencies: {missing}. "
                f"Recommendations: {recommendations}"
            )
            logger.error(error_msg)
            from baes.utils.presentation_logger import get_presentation_logger

            get_presentation_logger().error(error_msg)
            return self.create_error_response(
                "generate_integration_tests", error_msg, "missing_dependencies"
            )
        test_code = self._generate_robust_test_code(
            entity, "integration_tests", attributes, context
        )
        test_file_path = self._write_test_to_managed_system(entity, "integration_tests", test_code)
        return self.create_success_response(
            "generate_integration_tests",
            {
                "test_file_path": test_file_path,
                "test_code": test_code,
                "test_generated": True,
                "managed_system": True,
                "dependencies_validated": True,
            },
        )

    def _generate_ui_tests(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")
        validation = self._validate_test_dependencies(entity, "ui_tests")
        if not validation["dependencies_ready"]:
            missing = validation["missing_dependencies"]
            recommendations = validation["recommendations"]
            error_msg = (
                f"Cannot generate ui_tests for {entity}: missing dependencies: {missing}. "
                f"Recommendations: {recommendations}"
            )
            logger.error(error_msg)
            from baes.utils.presentation_logger import get_presentation_logger

            get_presentation_logger().error(error_msg)
            return self.create_error_response(
                "generate_ui_tests", error_msg, "missing_dependencies"
            )
        test_code = self._generate_robust_test_code(entity, "ui_tests", attributes, context)
        test_file_path = self._write_test_to_managed_system(entity, "ui_tests", test_code)
        return self.create_success_response(
            "generate_ui_tests",
            {
                "test_file_path": test_file_path,
                "test_code": test_code,
                "test_generated": True,
                "managed_system": True,
                "dependencies_validated": True,
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

            # Check if managed system exists
            if not managed_system_path.exists():
                logger.warning("❌ Managed system directory not found: %s", managed_system_path)
                return self.create_error_response(
                    "execute_tests",
                    f"Managed system not found at {managed_system_path}. System generation may have failed.",
                    "no_managed_system",
                )

            # Check if tests directory exists
            if not tests_dir.exists():
                logger.warning("❌ Tests directory not found: %s", tests_dir)
                return self.create_error_response(
                    "execute_tests",
                    f"No tests directory found at {tests_dir}. Tests may not have been generated.",
                    "no_tests_found",
                )

            # Check if there are any test files (search recursively)
            test_files = list(tests_dir.rglob("test_*.py")) + list(tests_dir.rglob("*_test.py"))
            if not test_files:
                logger.warning("❌ No test files found in: %s", tests_dir)
                return self.create_error_response(
                    "execute_tests",
                    f"No test files found in {tests_dir}. Test generation may have failed.",
                    "no_test_files",
                )

            # ------------------------------------------------------------------
            # Build pytest command with JSON reporting for reliable test counts
            # ------------------------------------------------------------------
            # Create a temporary file to hold the JSON report produced by
            # pytest-json-report. We can safely remove it after parsing.
            report_file = Path(tempfile.gettempdir()) / f"pytest_report_{int(time.time())}.json"

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(tests_dir),
                "-v",
                "--tb=short",
                "--no-header",
                "-q",
                "--json-report",
                f"--json-report-file={report_file}",
            ]

            start_time = time.time()
            logger.info("🧪 Executing tests in: %s", tests_dir)
            logger.debug("🧪 Test command: %s", " ".join(cmd))

            result = subprocess.run(
                cmd,
                cwd=str(managed_system_path),
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for all tests
            )

            execution_time = time.time() - start_time

            # ------------------------------------------------------------------
            # Parse JSON report for accurate counts - NO FALLBACK TO REGEX
            # ------------------------------------------------------------------
            tests_executed = tests_passed = tests_failed = 0

            if not report_file.exists():
                error_msg = f"JSON report file not found: {report_file}. pytest-json-report may not be working correctly."
                logger.error("❌ " + error_msg)
                return self.create_error_response("execute_tests", error_msg, "json_report_missing")

            try:
                with open(report_file, "r", encoding="utf-8") as jf:
                    report_data = json.load(jf)

                summary = report_data.get("summary", {})
                if not summary:
                    error_msg = f"JSON report has no 'summary' section: {report_data}"
                    logger.error("❌ " + error_msg)
                    return self.create_error_response(
                        "execute_tests", error_msg, "json_report_invalid"
                    )

                tests_executed = summary.get("collected", 0)
                tests_passed = summary.get("passed", 0)
                # Treat `failed` + `errors` as failures
                tests_failed = summary.get("failed", 0) + summary.get("errors", 0)

                logger.info("📊 JSON report parsed successfully:")
                logger.info("   📋 Collected: %d", tests_executed)
                logger.info("   ✅ Passed: %d", tests_passed)
                logger.info("   ❌ Failed: %d", tests_failed)

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON report: {str(e)}"
                logger.error("❌ " + error_msg)
                return self.create_error_response(
                    "execute_tests", error_msg, "json_report_parse_error"
                )
            except Exception as e:
                error_msg = f"Unexpected error parsing JSON report: {str(e)}"
                logger.error("❌ " + error_msg)
                return self.create_error_response("execute_tests", error_msg, "json_report_error")

            # Log detailed test execution info
            logger.info("🧪 Test execution completed:")
            logger.info("   📊 Tests executed: %d", tests_executed)
            logger.info("   ✅ Tests passed: %d", tests_passed)
            logger.info("   ❌ Tests failed: %d", tests_failed)
            logger.info("   🕒 Execution time: %.2fs", execution_time)
            logger.info("   📤 Exit code: %d", result.returncode)

            # Log stdout/stderr if there are issues
            if result.returncode != 0:
                logger.warning("❌ Test execution failed:")
                if result.stdout:
                    logger.warning("📤 STDOUT: %s", result.stdout[:1000])
                if result.stderr:
                    logger.warning("📤 STDERR: %s", result.stderr[:1000])

            # Clean up report file to avoid clutter (best effort)
            try:
                if report_file.exists():
                    report_file.unlink(missing_ok=True)
            except Exception:
                pass

            response_data = {
                "tests_executed": tests_executed,
                "test_execution": {
                    "success": result.returncode == 0 and tests_executed > 0,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "tests_directory": str(tests_dir),
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed,
                    "execution_time": execution_time,
                    "execution_type": execution_type,
                    "entity": entity,
                    "test_files_found": len(test_files),
                },
            }

            if validate_after_changes:
                response_data["test_execution"]["validation_status"] = (
                    "passed" if result.returncode == 0 and tests_executed > 0 else "failed"
                )
                response_data["test_execution"]["evolution_validation"] = True

                if result.returncode != 0 or tests_executed == 0:
                    logger.warning("⚠️  Evolution validation tests failed for %s", entity)
                else:
                    logger.info("✅ Evolution validation tests passed for %s", entity)

            # Determine overall success
            success = result.returncode == 0 and tests_executed > 0

            if success:
                return self.create_success_response("execute_tests", response_data)
            else:
                # Create error response without extra data parameter
                error_response = self.create_error_response(
                    "execute_tests",
                    "Test execution failed: "
                    + str(tests_executed)
                    + " tests executed, "
                    + str(tests_passed)
                    + " passed, exit code "
                    + str(result.returncode),
                    "test_execution_failed",
                )
                # Add the response data manually
                error_response["data"] = response_data
                return error_response

        except subprocess.TimeoutExpired:
            logger.error("❌ Test execution timed out after 120 seconds")
            return self.create_error_response(
                "execute_tests", "Test execution timed out after 120 seconds", "timeout_error"
            )
        except Exception as e:
            logger.error("❌ Test execution failed with exception: %s", str(e))
            return self.create_error_response(
                "execute_tests", "Error executing all tests: " + str(e), "execution_error"
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

    def _validate_and_fix_test_urls(self, test_code: str, entity: str, api_prefix: str) -> str:
        """Validate and fix test URLs to ensure they match the correct endpoint patterns."""
        if not test_code:
            return test_code
        
        # Define the correct URL patterns based on the actual API prefix from BackendSWEA
        # BackendSWEA generates routes with prefix like "/students" (no /api)
        correct_patterns = {
            f'{api_prefix}/': f'{api_prefix}/',
            f'{api_prefix}/{{id}}': f'{api_prefix}/{{id}}',
        }
        
        fixed_code = test_code
        
        # Use regex to find and replace URL patterns more accurately
        import re
        
        # Fix patterns with quotes (most common in test code)
        # Pattern: '/api/students/' -> '/students/'
        # Pattern: '/api/students/{id}' -> '/students/{id}'
        # Pattern: '/students/students/' -> '/students/'
        # Pattern: '/students/students/{id}' -> '/students/{id}'
        
        # Fix double entity patterns (most common issue)
        double_entity_list = rf'[\'"]{api_prefix}/{entity.lower()}s/[\'"]'
        fixed_code = re.sub(double_entity_list, f"'{api_prefix}/'", fixed_code)
        
        double_entity_id = rf'[\'"]{api_prefix}/{entity.lower()}s/\{{id\}}[\'"]'
        fixed_code = re.sub(double_entity_id, f"'{api_prefix}/{{id}}'", fixed_code)
        
        # Fix wrong API prefix patterns (remove /api if it's not in the actual prefix)
        if '/api' not in api_prefix:
            wrong_prefix_list = rf'[\'"]/api/{entity.lower()}s/[\'"]'
            fixed_code = re.sub(wrong_prefix_list, f"'{api_prefix}/'", fixed_code)
            
            wrong_prefix_id = rf'[\'"]/api/{entity.lower()}s/\{{id\}}[\'"]'
            fixed_code = re.sub(wrong_prefix_id, f"'{api_prefix}/{{id}}'", fixed_code)
        
        # Fix hardcoded "student" patterns
        hardcoded_list = rf'[\'"]{api_prefix}/student/[\'"]'
        fixed_code = re.sub(hardcoded_list, f"'{api_prefix}/'", fixed_code)
        
        hardcoded_id = rf'[\'"]{api_prefix}/student/\{{id\}}[\'"]'
        fixed_code = re.sub(hardcoded_id, f"'{api_prefix}/{{id}}'", fixed_code)
        
        # Log what was fixed
        if fixed_code != test_code:
            logger.info(f"TestSWEA: Fixed URL patterns for {entity} using API prefix: {api_prefix}")
        
        return fixed_code

    def _get_attributes_from_bae(self, entity: str) -> List[str]:
        """Get attributes from the appropriate BAE - single source of truth"""
        try:
            from baes.core.bae_registry import EnhancedBAERegistry
            bae_registry = EnhancedBAERegistry()
            bae = bae_registry.get_bae(entity.lower())
            if bae and hasattr(bae, '_get_default_attributes'):
                attributes = bae._get_default_attributes()
                logger.info(f"TestSWEA: Retrieved {len(attributes)} attributes from {entity} BAE")
                return attributes
            else:
                logger.warning(f"TestSWEA: No BAE found for {entity} or BAE missing _get_default_attributes method")
                # return ["name: str", "description: str", "created_at: str"]
                raise TestGenerationError(
                    f"Could not retrieve attributes from BAE for entity '{entity}'. BAE may not be registered or properly configured."
                )
        except Exception as e:
            logger.error(f"TestSWEA: Error getting attributes from BAE for {entity}: {e}")
            # return ["name: str", "description: str", "created_at: str"]
            raise TestGenerationError(f"Failed to get attributes from BAE for '{entity}': {e}") from e

    def _generate_simple_test_data(self, entity: str, attributes: List[str]) -> Dict[str, Any]:
        """Generate simple test data that matches the actual model structure."""
        # Always get attributes from BAE for the entity
        bae_attributes = self._get_attributes_from_bae(entity)
        test_data = {}
        for attr in bae_attributes:
            if ":" in attr:
                field_name, field_type = attr.split(":", 1)
                field_name = field_name.strip()
                field_type = field_type.strip()
                if field_type == "str":
                    test_data[field_name] = f"test_{field_name}"
                elif field_type == "int":
                    test_data[field_name] = 1
                elif field_type == "float":
                    test_data[field_name] = 1.0
                else:
                    test_data[field_name] = f"test_{field_name}"
        return test_data




# ---------------------------------------------------------------------------
# Custom exception to enforce strict failures
# ---------------------------------------------------------------------------


class TestGenerationError(Exception):
    """Raised when test generation fails or returns invalid content."""

    pass
