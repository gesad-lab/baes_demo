"""
Shared test configuration and fixtures for BAE test suite.

This module provides common fixtures and configuration for all test modules
in the BAE (Business Autonomous Entities) test suite.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch

import pytest

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure repository root (two levels up) is in sys.path so 'bae_academic_system' package is importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture
def temp_database_path():
    """Provide a temporary database path for testing"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls"""
    with patch("baes.llm.openai_client.OpenAIClient") as mock_client:
        mock_instance = Mock()

        # Mock successful responses
        mock_instance.generate_response.return_value = "Mocked response"

        # Mock for schema generation
        def mock_generate_domain_entity_response(prompt, entity_name):
            if "validate" in prompt.lower() and "json" in prompt.lower():
                # Return JSON validation response
                return """{
                    "is_valid": true,
                    "entity_focus_correct": true,
                    "semantic_coherence_score": 95,
                    "business_vocabulary_preserved": true,
                    "domain_rules_followed": true,
                    "issues": [],
                    "recommendations": ["Excellent domain coherence maintained"],
                    "validation_summary": "Artifact maintains excellent domain coherence for Student entity"
                }"""
            else:
                # Return schema generation response
                return """
from pydantic import BaseModel
from typing import Optional

class Student(BaseModel):
    name: str
    registration_number: str
    course: str
"""

        mock_instance.generate_domain_entity_response.side_effect = (
            mock_generate_domain_entity_response
        )

        mock_instance.interpret_business_request.return_value = {
            "intent": "create_student_management_system",
            "entity_focus": "Student",
            "requested_operations": ["create", "read", "update", "delete"],
            "attributes_mentioned": ["name", "registration_number", "course"],
            "business_vocabulary": ["Student", "Academic", "Learning"],
            "swea_coordination_needed": {"programmer": True, "frontend": True, "database": True},
            "complexity_level": "simple",
        }

        mock_instance.validate_semantic_coherence.return_value = {
            "is_semantically_coherent": True,
            "coherence_score": 95,
            "business_vocabulary_preserved": True,
            "domain_rules_followed": True,
            "identified_issues": [],
            "improvement_suggestions": [],
        }

        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_all_openai_clients():
    """Mock all OpenAI clients used across BAE, SWEA agents for comprehensive testing"""
    patches = [
        patch("baes.llm.openai_client.OpenAIClient"),
        patch("baes.domain_entities.base_bae.OpenAIClient"),
        patch("baes.swea_agents.programmer_swea.OpenAIClient"),
        patch("baes.swea_agents.frontend_swea.OpenAIClient"),
    ]

    mocks = {}
    for p in patches:
        mock_client = p.start()
        mock_instance = Mock()

        # Standard responses for all clients
        mock_instance.generate_response.return_value = "# Generated code"
        mock_instance.generate_code_with_domain_focus.return_value = "# Domain-focused code"

        # Mock for schema generation and validation
        def mock_generate_domain_entity_response(prompt, entity_name):
            if "validate" in prompt.lower() and "json" in prompt.lower():
                # Return JSON validation response
                return """{
                    "is_valid": true,
                    "entity_focus_correct": true,
                    "semantic_coherence_score": 95,
                    "business_vocabulary_preserved": true,
                    "domain_rules_followed": true,
                    "issues": [],
                    "recommendations": ["Excellent domain coherence maintained"],
                    "validation_summary": "Artifact maintains excellent domain coherence for Student entity"
                }"""
            else:
                # Return schema generation response
                return """
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    email: str
        """

        mock_instance.generate_domain_entity_response.side_effect = (
            mock_generate_domain_entity_response
        )

        mock_instance.interpret_business_request.return_value = {
            "intent": "create_student_management_system",
            "entity_focus": "Student",
            "domain_operations": ["create", "read", "update", "delete"],
            "swea_coordination": [{"agent": "ProgrammerSWEA", "task": "generate_api"}],
            "business_vocabulary": ["student", "academic", "learning"],
        }

        mock_client.return_value = mock_instance
        mocks[p.attribute] = mock_instance

    yield mocks

    # Cleanup
    for p in patches:
        p.stop()


@pytest.fixture
def temp_test_directory():
    """Provide a temporary directory for test file generation with automatic cleanup"""
    test_dir = tempfile.mkdtemp(prefix="bae_test_", dir="tests")
    original_cwd = os.getcwd()
    os.chdir(test_dir)

    # Create common test directory structure
    os.makedirs("llm/prompts", exist_ok=True)
    os.makedirs("test_generated/models", exist_ok=True)
    os.makedirs("test_generated/routes", exist_ok=True)
    os.makedirs("test_generated/ui", exist_ok=True)

    # Create minimal prompt template
    with open("llm/prompts/student_schema.txt", "w") as f:
        f.write("Generate a Pydantic model for {entity} entity with attributes: {attributes}")

    yield test_dir

    # Cleanup
    os.chdir(original_cwd)
    import shutil

    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def sample_business_request():
    """Sample business request for testing"""
    return {
        "request": "Create a system to manage students with name, registration number, and course",
        "context": "academic",
    }


@pytest.fixture
def sample_student_attributes():
    """Sample student attributes for testing"""
    return ["name: str", "registration_number: str", "course: str"]


@pytest.fixture
def sample_domain_context():
    """Sample domain context for testing"""
    return {
        "entity": "Student",
        "attributes": ["name", "registration", "course"],
        "business_rules": ["Unique registration", "Required name"],
        "context": "academic",
    }


@pytest.fixture
def sample_business_vocabulary():
    """Sample business vocabulary for testing"""
    return ["Student", "Academic", "Learning", "Enrollment", "Course", "Registration"]


@pytest.fixture
def mock_context_store(temp_database_path):
    """Mock context store with temporary storage"""
    from baes.core.context_store import ContextStore

    return ContextStore(temp_database_path)


@pytest.fixture
def clean_test_environment():
    """Ensure clean test environment"""
    # Clean up any existing test files
    test_files = ["database/test_context_store.json", "database/scenario1_test.json"]

    for file_path in test_files:
        if os.path.exists(file_path):
            os.unlink(file_path)

    yield

    # Cleanup after test
    for file_path in test_files:
        if os.path.exists(file_path):
            os.unlink(file_path)


@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests"""
    import time

    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.metrics = {}

        def start(self, operation_name: str):
            self.start_time = time.time()
            self.current_operation = operation_name

        def stop(self) -> float:
            if self.start_time is None:
                return 0.0
            duration = time.time() - self.start_time
            self.metrics[self.current_operation] = duration
            self.start_time = None
            return duration

        def get_metrics(self) -> Dict[str, float]:
            return self.metrics.copy()

    return PerformanceTracker()


# Test markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for component interaction")
    config.addinivalue_line(
        "markers", "scenario: Scenario-based tests for proof of concept validation"
    )
    config.addinivalue_line("markers", "performance: Performance and timing tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
    config.addinivalue_line(
        "markers", "integration_online: Tests that hit live external services (OpenAI)"
    )


# ---------------------------------------------------------------------------
#  Optional online-integration control
# ---------------------------------------------------------------------------


def pytest_runtest_setup(item):
    if "integration_online" in item.keywords:
        if os.getenv("RUN_ONLINE", "0") != "1":
            pytest.skip("Set RUN_ONLINE=1 to run live OpenAI tests")
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set in environment")


# Scenario 1 specific fixtures
@pytest.fixture
def scenario1_success_criteria():
    """Success criteria for Scenario 1 validation"""
    return {
        "max_generation_time_seconds": 180,  # 3 minutes
        "required_success_rate": 100,  # 100% functional system
        "min_semantic_coherence_score": 80,  # 80% semantic coherence
        "required_swea_agents": ["StudentBAE", "ProgrammerSWEA", "FrontendSWEA", "DatabaseSWEA"],
        "expected_artifacts": ["models", "routes", "ui", "database"],
    }


@pytest.fixture
def scenario2_success_criteria():
    """Success criteria for Scenario 2 validation"""
    return {
        "max_evolution_time_seconds": 120,  # 2 minutes
        "zero_data_loss": True,
        "zero_downtime": True,
        "min_semantic_coherence_score": 80,
    }


@pytest.fixture
def scenario3_success_criteria():
    """Success criteria for Scenario 3 validation"""
    return {
        "max_configuration_time_seconds": 60,  # 1 minute
        "min_reuse_percentage": 80,  # 80% code reuse
        "min_semantic_coherence_score": 80,
    }


# ---------------------------------------------------------------------------
#  Test Utility Functions
# ---------------------------------------------------------------------------


def assert_bae_response_valid(result, entity="Student"):
    """Helper function to validate BAE response structure"""
    assert isinstance(result, dict), "BAE response must be a dictionary"
    assert result.get("entity") == entity, f"Expected entity {entity}, got {result.get('entity')}"

    if "error" in result:
        # Allow graceful error handling
        assert isinstance(result["error"], str), "Error message must be a string"
    else:
        # For successful responses, expect basic structure
        assert (
            "interpreted_intent" in result or "code" in result
        ), "Response must contain interpretation or code"


def assert_swea_response_valid(result):
    """Helper function to validate SWEA response structure"""
    assert isinstance(result, dict), "SWEA response must be a dictionary"
    assert "success" in result, "SWEA response must indicate success status"

    if result.get("success"):
        assert (
            "code" in result or "ui" in result or "schema" in result
        ), "Successful SWEA response must contain generated artifacts"


def assert_coordination_plan_valid(coordination_plan, min_agents=2):
    """Helper function to validate SWEA coordination plan structure"""
    assert isinstance(coordination_plan, list), "Coordination plan must be a list"
    assert (
        len(coordination_plan) >= min_agents
    ), f"Expected at least {min_agents} SWEA agents in coordination plan"

    for task in coordination_plan:
        assert "swea_agent" in task, "Each coordination task must specify SWEA agent"
        assert "task_type" in task, "Each coordination task must specify task type"
        assert "domain_context" in task, "Each coordination task must include domain context"


def assert_semantic_coherence(result, min_score=80):
    """Helper function to validate semantic coherence in responses"""
    if "semantic_coherence_score" in result:
        score = result["semantic_coherence_score"]
        assert score >= min_score, f"Semantic coherence score {score} below minimum {min_score}"

    if "business_vocabulary_preserved" in result:
        assert (
            result["business_vocabulary_preserved"] is True
        ), "Business vocabulary must be preserved"


def assert_success_metrics(metrics, criteria):
    """Helper function to validate success metrics against criteria"""
    for key, expected_value in criteria.items():
        if key.endswith("_time_seconds"):
            actual_time = metrics.get(key.replace("_seconds", ""), float("inf"))
            assert (
                actual_time < expected_value
            ), f"Time metric {key}: {actual_time:.2f}s exceeds {expected_value}s"
        elif key.startswith("min_"):
            metric_name = key.replace("min_", "")
            actual_value = metrics.get(metric_name, 0)
            assert (
                actual_value >= expected_value
            ), f"Metric {metric_name}: {actual_value} below minimum {expected_value}"
        elif isinstance(expected_value, bool):
            actual_value = metrics.get(key, False)
            assert (
                actual_value == expected_value
            ), f"Boolean metric {key}: expected {expected_value}, got {actual_value}"
