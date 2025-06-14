"""
Unit tests for Enhanced Runtime Kernel module.

Tests the enhanced runtime kernel functionality including entity recognition,
BAE coordination, SWEA agent routing, and error handling for unknown agents.
"""

from unittest.mock import Mock, patch

import pytest

from baes.core.enhanced_runtime_kernel import (
    EnhancedRuntimeKernel,
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
        # Mock a coordination plan with an unknown SWEA agent
        coordination_plan = [
            {
                "swea_agent": "UnknownSWEA",
                "task_type": "unknown_task",
                "entity": "Student",
                "payload": {},
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
                        result = kernel.process_natural_language_request(
                            "Create a student system", context="academic", start_servers=False
                        )

                        # Verify error response structure
                        assert result["success"] is False
                        assert result["error"] == "UNKNOWN_SWEA_AGENT"
                        assert "DatabaseSWEA" in result["message"]
                        assert result["details"]["requested_agent"] == "DatabaseSWEA"
                        assert "ProgrammerSWEA" in result["details"]["available_agents"]
                        assert "FrontendSWEA" in result["details"]["available_agents"]
                        assert "help" in result

    def test_valid_swea_agents_work_correctly(self, kernel):
        """Test that valid SWEA agents (BackendSWEA, FrontendSWEA) work correctly"""
        # Mock coordination plan with valid SWEA agents
        coordination_plan = [
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "entity": "Student",
                "payload": {},
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "entity": "Student",
                "payload": {},
            },
        ]

        # Mock coordinating BAE
        mock_bae = Mock()
        mock_bae.entity_name = "Student"
        mock_bae.name = "StudentBAE"

        # Mock SWEA agents to return successful results
        kernel.backend_swea.handle_task = Mock(
            return_value={"success": True, "code": "generated code"}
        )
        kernel.frontend_swea.handle_task = Mock(
            return_value={"success": True, "ui": "generated ui"}
        )

        # Execute coordination plan
        results = kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify successful execution
        assert len(results) == 2
        assert all(result["success"] for result in results)
        assert results[0]["task"] == "BackendSWEA.generate_model"
        assert results[1]["task"] == "FrontendSWEA.generate_ui"

    def test_case_insensitive_swea_agent_matching(self, kernel):
        """Test that SWEA agent matching is case insensitive"""
        # Test various case variations that should work
        valid_variations = [
            "backend",
            "BACKEND",
            "BackendSWEA",
            "backendswea",
            "frontend",
            "FRONTEND",
            "FrontendSWEA",
        ]

        for agent_name in valid_variations:
            coordination_plan = [
                {
                    "swea_agent": agent_name,
                    "task_type": "test_task",
                    "entity": "Student",
                    "payload": {},
                }
            ]

            mock_bae = Mock()
            mock_bae.entity_name = "Student"
            mock_bae.name = "StudentBAE"

            # Mock SWEA response
            if "backend" in agent_name.lower():
                kernel.backend_swea.handle_task = Mock(return_value={"success": True})
            else:
                kernel.frontend_swea.handle_task = Mock(return_value={"success": True})

            # Should not raise exception for valid variations
            try:
                results = kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")
                assert len(results) == 1
                assert results[0]["success"]
            except UnknownSWEAAgentError:
                pytest.fail(f"Should not raise exception for valid agent name: {agent_name}")

    def test_swea_agent_task_execution_failure(self, kernel):
        """Test handling of SWEA agent task execution failures"""
        coordination_plan = [
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "entity": "Student",
                "payload": {},
            }
        ]

        mock_bae = Mock()
        mock_bae.entity_name = "Student"
        mock_bae.name = "StudentBAE"

        # Mock SWEA agent to raise an exception
        kernel.backend_swea.handle_task = Mock(side_effect=Exception("Task execution failed"))

        # Execute coordination plan
        results = kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify failure is handled properly
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "SWEA task execution failed" in results[0]["error"]

    def test_multiple_unknown_agents_first_fails(self, kernel):
        """Test that execution stops at first unknown agent"""
        coordination_plan = [
            {
                "swea_agent": "BackendSWEA",  # Valid
                "task_type": "generate_model",
                "entity": "Student",
                "payload": {},
            },
            {
                "swea_agent": "UnknownSWEA1",  # Invalid - should fail here
                "task_type": "unknown_task",
                "entity": "Student",
                "payload": {},
            },
            {
                "swea_agent": "UnknownSWEA2",  # Should never reach this
                "task_type": "another_unknown_task",
                "entity": "Student",
                "payload": {},
            },
        ]

        mock_bae = Mock()
        mock_bae.entity_name = "Student"
        mock_bae.name = "StudentBAE"

        # Mock first SWEA to succeed
        kernel.backend_swea.handle_task = Mock(return_value={"success": True})

        # Should raise exception on second (unknown) agent
        with pytest.raises(UnknownSWEAAgentError) as exc_info:
            kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")

        # Verify it failed on the correct agent
        assert exc_info.value.agent_name == "UnknownSWEA1"

        # Verify first agent was called (execution started)
        kernel.backend_swea.handle_task.assert_called_once()
