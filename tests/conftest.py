"""
Shared test configuration and fixtures for BAE test suite.

This module provides common fixtures and configuration for all test modules
in the BAE (Business Autonomous Entities) test suite.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch
from typing import Dict, Any

# Ensure repository root (two levels up) is in sys.path so 'bae_academic_system' package is importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

@pytest.fixture
def temp_database_path():
    """Provide a temporary database path for testing"""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls"""
    with patch('baes.llm.openai_client.OpenAIClient') as mock_client:
        mock_instance = Mock()
        
        # Mock successful responses
        mock_instance.generate_response.return_value = "Mocked response"
        mock_instance.generate_domain_entity_response.return_value = """
from pydantic import BaseModel
from typing import Optional

class Student(BaseModel):
    name: str
    registration_number: str
    course: str
"""
        mock_instance.interpret_business_request.return_value = {
            "intent": "create_student_management_system",
            "entity_focus": "Student",
            "requested_operations": ["create", "read", "update", "delete"],
            "attributes_mentioned": ["name", "registration_number", "course"],
            "business_vocabulary": ["Student", "Academic", "Learning"],
            "swea_coordination_needed": {
                "programmer": True,
                "frontend": True,
                "database": True
            },
            "complexity_level": "simple"
        }
        
        mock_instance.validate_semantic_coherence.return_value = {
            "is_semantically_coherent": True,
            "coherence_score": 95,
            "business_vocabulary_preserved": True,
            "domain_rules_followed": True,
            "identified_issues": [],
            "improvement_suggestions": []
        }
        
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_business_request():
    """Sample business request for testing"""
    return {
        "request": "Create a system to manage students with name, registration number, and course",
        "context": "academic"
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
        "context": "academic"
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
    test_files = [
        "database/test_context_store.json",
        "database/scenario1_test.json"
    ]
    
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
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line(
        "markers", "scenario: Scenario-based tests for proof of concept validation"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and timing tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
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
        "required_swea_agents": ["StudentBAE", "ProgrammerSWEA", "FrontendSWEA", "DatabaseSWEA"]
    }

@pytest.fixture
def scenario2_success_criteria():
    """Success criteria for Scenario 2 validation"""
    return {
        "max_evolution_time_seconds": 120,  # 2 minutes
        "zero_downtime_required": True,
        "data_preservation_required": True,
        "min_semantic_coherence_score": 85
    }

@pytest.fixture
def scenario3_success_criteria():
    """Success criteria for Scenario 3 validation"""
    return {
        "max_adaptation_time_seconds": 60,  # 1 minute
        "min_reuse_percentage": 80,  # 80% reuse
        "context_adaptation_required": True
    } 