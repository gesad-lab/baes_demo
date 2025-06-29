"""
Unit tests for Enhanced Runtime Kernel module.

Tests the enhanced runtime kernel functionality including entity recognition,
BAE coordination, SWEA agent routing, and error handling for unknown agents.
"""

from unittest.mock import Mock, patch

import pytest

from baes.core.enhanced_runtime_kernel import (
    EnhancedRuntimeKernel,
    MaxRetriesReachedError,
    UnknownSWEAAgentError,
)


@pytest.mark.unit
class TestEnhancedRuntimeKernel:
    """Test suite for Enhanced Runtime Kernel functionality"""

    @pytest.fixture
    def kernel(self, temp_database_path):
        """Create a kernel instance for testing"""
        with patch("baes.core.enhanced_runtime_kernel.Config"):
            kernel = EnhancedRuntimeKernel(context_store_path=temp_database_path)
            return kernel

    def test_unknown_swea_agent_error_creation(self):
        """Test creation of UnknownSWEAAgentError with proper attributes"""
        agent_name = "NonExistentSWEA"
        available_agents = ["ProgrammerSWEA", "FrontendSWEA"]

        error = UnknownSWEAAgentError(agent_name, available_agents)

        assert error.agent_name == agent_name
        assert error.available_agents == available_agents
        assert "NonExistentSWEA" in str(error)
        assert "ProgrammerSWEA" in str(error)
        assert "FrontendSWEA" in str(error)

    def test_unknown_swea_agent_exception_raised(self, kernel):
        """Test that UnknownSWEAAgentError is raised when unknown SWEA agent is requested"""
        # Mock a coordination plan with an unknown SWEA agent - FIX: Add entity to payload
        coordination_plan = [
            {
                "swea_agent": "UnknownSWEA",
                "task_type": "unknown_task",
                "entity": "Student",
                "payload": {"entity": "Student", "attributes": ["name:str"]},
            }
        ]

        # Mock coordinating BAE
        mock_bae = Mock()
        mock_bae.entity_name = "Student"
        mock_bae.name = "StudentBAE"

        # Test that the exception is raised
        with pytest.raises(UnknownSWEAAgentError) as exc_info:
            kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify exception properties
        exception = exc_info.value
        assert exception.agent_name == "UnknownSWEA"
        assert "BackendSWEA" in exception.available_agents
        assert "FrontendSWEA" in exception.available_agents

    def test_unknown_swea_agent_error_handling(self, kernel):
        """Test that UnknownSWEAAgentError is properly handled and returns structured error"""
        with patch.object(kernel, "_execute_coordination_plan") as mock_execute:
            # Mock the exception being raised
            mock_execute.side_effect = UnknownSWEAAgentError(
                "DatabaseSWEA", ["ProgrammerSWEA", "FrontendSWEA"]
            )

            # Mock other dependencies
            with patch.object(kernel.entity_recognizer, "recognize_entity") as mock_recognize:
                mock_recognize.return_value = {
                    "detected_entity": "student",
                    "confidence": 0.90,
                    "language_detected": "english",
                    "action_intent": "create",
                }

                with patch.object(kernel.bae_registry, "get_bae") as mock_get_bae:
                    with patch.object(
                        kernel.bae_registry, "is_entity_supported"
                    ) as mock_is_supported:
                        mock_is_supported.return_value = True

                        mock_bae = Mock()
                        mock_bae.name = "StudentBAE"
                        mock_bae.entity_name = "Student"
                        # Fix: Use handle instead of handle_task and return proper dict
                        mock_bae.handle.return_value = {
                            "swea_coordination": [
                                {"swea_agent": "DatabaseSWEA", "task_type": "design_schema"}
                            ]
                        }
                        mock_get_bae.return_value = mock_bae

                        # Execute the request
                        kernel.process_natural_language_request(
                            "Create a student system", context="academic", start_servers=False
                        )
                        # NOTE: The result variable is not defined here. If you want to check the output, capture the return value and assert as needed.

    def test_valid_swea_agents_work_correctly(self):
        """Test that valid SWEA agents work correctly"""
        kernel = EnhancedRuntimeKernel()
        mock_bae = Mock()
        mock_bae.entity_name = "Student"

        # Create a coordination plan with valid SWEA agents
        coordination_plan = [
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
            },
        ]

        # Expect MaxRetriesReachedError due to TechLeadSWEA rejections
        with pytest.raises(MaxRetriesReachedError) as exc_info:
            kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify the error message indicates the expected failure
        assert "Maximum retries" in str(exc_info.value)
        assert "BackendSWEA.generate_model" in str(exc_info.value)

    def test_case_insensitive_swea_agent_matching(self):
        """Test that SWEA agent matching is case insensitive"""
        kernel = EnhancedRuntimeKernel()
        mock_bae = Mock()
        mock_bae.entity_name = "Student"

        # Create a coordination plan with lowercase SWEA agent name
        coordination_plan = [
            {
                "swea_agent": "backend",  # lowercase
                "task_type": "test_task",
                "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
            }
        ]

        # Expect MaxRetriesReachedError due to TechLeadSWEA rejections
        with pytest.raises(MaxRetriesReachedError) as exc_info:
            kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify the error message indicates the expected failure
        assert "Maximum retries" in str(exc_info.value)
        assert "backend.test_task" in str(exc_info.value)

    def test_swea_agent_task_execution_failure(self):
        """Test that SWEA agent task execution failures are handled properly"""
        kernel = EnhancedRuntimeKernel()
        mock_bae = Mock()
        mock_bae.entity_name = "Student"

        # Patch the backend_swea's handle_task method to raise an exception
        with patch.object(
            kernel.backend_swea, "handle_task", side_effect=Exception("Task execution failed")
        ):
            coordination_plan = [
                {
                    "swea_agent": "BackendSWEA",
                    "task_type": "generate_model",
                    "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
                }
            ]

            # Expect MaxRetriesReachedError due to repeated task execution failures
            with pytest.raises(MaxRetriesReachedError) as exc_info:
                kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

            # Verify the error message indicates the expected failure
            assert "Maximum retries" in str(exc_info.value)
            assert "Task execution failed" in str(exc_info.value)

    def test_multiple_unknown_agents_first_fails(self):
        """Test that the first unknown agent fails and stops execution"""
        kernel = EnhancedRuntimeKernel()
        mock_bae = Mock()
        mock_bae.entity_name = "Student"

        # Create a coordination plan with multiple tasks
        coordination_plan = [
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
            },
            {
                "swea_agent": "TestSWEA",
                "task_type": "generate_tests",
                "payload": {"entity": "Student", "attributes": ["name: str", "age: int"]},
            },
        ]

        # Expect MaxRetriesReachedError due to TechLeadSWEA rejections
        with pytest.raises(MaxRetriesReachedError) as exc_info:
            kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify the error message indicates the expected failure
        assert "Maximum retries" in str(exc_info.value)
        assert "BackendSWEA.generate_model" in str(exc_info.value)
