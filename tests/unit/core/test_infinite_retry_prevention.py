"""
Comprehensive tests for infinite retry loop prevention mechanisms.
"""

import os
from unittest.mock import Mock, patch

import pytest

from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
from baes.domain_entities.academic.student_bae import StudentBae
from baes.swea_agents.techlead_swea import TechLeadSWEA


class TestInfiniteRetryPrevention:
    """Test infinite retry loop prevention mechanisms"""

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Set up test environment to use tests/.temp directory"""
        os.environ["MANAGED_SYSTEM_PATH"] = "tests/.temp"
        yield

    @pytest.fixture
    def kernel(self):
        """Create EnhancedRuntimeKernel instance for testing"""
        return EnhancedRuntimeKernel()

    def test_frontend_ui_generation_basic(self):
        """Test basic FrontendSWEA UI generation functionality"""
        from baes.swea_agents.frontend_swea import FrontendSWEA

        frontend_swea = FrontendSWEA()

        # Test basic UI generation with valid parameters
        result = frontend_swea.handle_task(
            "generate_ui",
            {
                "entity": "Student",
                "attributes": ["name:str", "email:str", "age:int"],
                "context": "academic",
            },
        )

        # Should succeed and generate UI code
        assert result["success"] is True
        assert "data" in result

        # Check that code was generated
        code = result.get("data", {}).get("code", "")
        assert len(code) > 0
        assert "streamlit" in code.lower() or "st." in code
        assert "def main" in code or "def main()" in code

    def test_techlead_simplified_validation_approval(self):
        """Test TechLeadSWEA approval mechanism with simplified validation"""
        techlead = TechLeadSWEA()

        # Create a minimal result that should pass basic validation
        minimal_result = {
            "success": True,
            "data": {
                "code": """
import streamlit as st

def main():
    st.title("Student Management")
    st.write("Basic functionality")

if __name__ == "__main__":
    main()
                """
            },
        }

        # Test with simplified validation - should pass
        review_payload = {
            "entity": "Student",
            "swea_agent": "FrontendSWEA",
            "task_type": "generate_ui",
            "result": minimal_result,
            "quality_gates": {},
            "retry_count": 0,
        }

        review = techlead._review_and_approve(review_payload)

        # Should approve with simplified, more lenient validation
        assert review["data"]["overall_approval"] is True
        assert len(review["data"]["technical_feedback"]) == 0

    def test_retry_pattern_monitoring(self, kernel):
        """Test retry pattern monitoring and analytics"""
        # Test that monitoring structures are initialized
        assert hasattr(kernel, "retry_patterns")
        assert hasattr(kernel, "failure_analytics")

        # Test pattern tracking
        task_key = "FrontendSWEA.generate_ui"
        error_msg = "Generated code doesn't appear to be valid Streamlit UI"
        retry_count = 1

        kernel._track_retry_pattern(task_key, error_msg, retry_count)

        # Verify pattern was recorded
        assert task_key in kernel.retry_patterns
        pattern_history = kernel.retry_patterns[task_key]
        assert len(pattern_history) > 0

        # Test prevention strategy generation
        strategy = kernel._get_retry_prevention_strategy(task_key)
        assert "reasoning" in strategy
        assert "additional_validation" in strategy
        assert "use_fallback" in strategy

    def test_circuit_breaker_prevents_infinite_loops_real_scenario(self, kernel):
        """Test that circuit breaker prevents infinite loops in real-world scenario"""
        # This test simulates the actual scenario that was causing infinite loops

        # Mock a coordination plan that would trigger FrontendSWEA
        coordination_plan = [
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {
                    "entity": "Student",
                    "attributes": ["name:str", "email:str"],
                    "context": "academic",
                },
            }
        ]

        # Mock a BAE for coordination
        class MockBAE:
            entity_name = "Student"

        mock_bae = MockBAE()

        # Execute with circuit breaker protection
        # Should either succeed quickly or fail gracefully without infinite loop
        import time

        start_time = time.time()

        try:
            results = kernel._execute_coordination_plan(coordination_plan, mock_bae, "academic")
            execution_time = time.time() - start_time

            # Should complete within reasonable time (not infinite loop)
            assert execution_time < 60, f"Execution took too long: {execution_time}s"

            # Should have results
            assert len(results) > 0, "Should produce results"

            # Check if circuit breaker was used or normal success
            frontend_result = next(
                (r for r in results if "FrontendSWEA" in r.get("task", "")), None
            )
            assert frontend_result is not None, "Should have FrontendSWEA result"

            # Should succeed either normally or via circuit breaker
            success_indicators = [
                frontend_result.get("success", False),
                frontend_result.get("circuit_breaker_used", False),
                frontend_result.get("emergency_fallback", False),
            ]
            assert any(success_indicators), "Should succeed through some mechanism"

            print(f"✅ Test completed in {execution_time:.2f}s")
            if frontend_result.get("circuit_breaker_used"):
                print("🛑 Circuit breaker was triggered successfully")
            if frontend_result.get("emergency_fallback"):
                print("🚨 Emergency fallback was used successfully")

        except Exception as e:
            execution_time = time.time() - start_time
            # Even if it fails, it should fail quickly (not infinite loop)
            assert execution_time < 60, f"Even failure took too long: {execution_time}s - {str(e)}"

            # Should be a controlled failure (MaxRetriesReachedError)
            from baes.core.enhanced_runtime_kernel import MaxRetriesReachedError

            if isinstance(e, MaxRetriesReachedError):
                print(
                    f"✅ Controlled failure after {e.retry_count} retries in {execution_time:.2f}s"
                )
                assert e.retry_count <= 3, "Should not exceed reasonable retry count"
            else:
                # Re-raise unexpected exceptions
                raise

    def test_proper_error_handling_without_fallback(self):
        """Test that the system handles errors properly without emergency fallbacks"""
        from baes.swea_agents.frontend_swea import FrontendSWEA

        frontend_swea = FrontendSWEA()

        # Test with completely invalid parameters - should fail cleanly
        result = frontend_swea.handle_task(
            "invalid_task", {"entity": "Student", "attributes": [], "context": "academic"}
        )

        # Should fail gracefully without emergency fallback
        assert result["success"] is False
        assert "error" in result
        assert "emergency_fallback" not in result.get("data", {})

        # Test error message is meaningful
        error_msg = result.get("error", "")
        assert len(error_msg) > 0
        assert "unknown task" in error_msg.lower() or "invalid" in error_msg.lower()

    def test_mandatory_attribute_validation(self, kernel):
        """Test that mandatory attribute validation catches missing information early"""
        # Test missing swea_agent
        invalid_plan_1 = [
            {
                "task_type": "generate_ui",
                "payload": {"entity": "Student"},
                # Missing swea_agent
            }
        ]

        # Mock BAE
        class MockBAE:
            entity_name = "Student"

        mock_bae = MockBAE()

        # Should raise ValueError for missing swea_agent
        with pytest.raises(ValueError) as exc_info:
            kernel._execute_coordination_plan(invalid_plan_1, mock_bae, "academic")

        assert "Missing mandatory attribute 'swea_agent'" in str(exc_info.value)

        # Test missing task_type
        invalid_plan_2 = [
            {
                "swea_agent": "FrontendSWEA",
                "payload": {"entity": "Student"},
                # Missing task_type
            }
        ]

        with pytest.raises(ValueError) as exc_info:
            kernel._execute_coordination_plan(invalid_plan_2, mock_bae, "academic")

        assert "Missing mandatory attribute 'task_type'" in str(exc_info.value)

        # Test missing payload
        invalid_plan_3 = [
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                # Missing payload
            }
        ]

        with pytest.raises(ValueError) as exc_info:
            kernel._execute_coordination_plan(invalid_plan_3, mock_bae, "academic")

        assert "Missing 'payload' attribute" in str(exc_info.value)

        # Test empty swea_agent
        invalid_plan_4 = [
            {
                "swea_agent": "",  # Empty string
                "task_type": "generate_ui",
                "payload": {"entity": "Student"},
            }
        ]

        with pytest.raises(ValueError) as exc_info:
            kernel._execute_coordination_plan(invalid_plan_4, mock_bae, "academic")

        assert "Missing mandatory attribute 'swea_agent'" in str(exc_info.value)

    def test_validation_error_interrupts_generation(self, kernel):
        """Test that validation errors immediately interrupt the generation process"""
        # Create a mock BAE that returns invalid coordination plan
        mock_bae = Mock(spec=StudentBae)
        mock_bae.name = "StudentBae"
        mock_bae.entity_name = "Student"

        # Mock BAE to return coordination plan with missing mandatory attributes
        invalid_coordination_plan = [
            {
                # Missing 'swea_agent' - this should trigger validation error
                "task_type": "generate_model",
                "payload": {"entity": "Student", "attributes": ["name: str"]},
            },
            {
                "swea_agent": "",  # Empty swea_agent - this should also trigger validation error
                "task_type": "generate_api",
                "payload": {"entity": "Student", "attributes": ["name: str"]},
            },
            {
                "swea_agent": "BackendSWEA",
                # Missing 'task_type' - this should trigger validation error
                "payload": {"entity": "Student", "attributes": ["name: str"]},
            },
        ]

        mock_bae.handle.return_value = {
            "entity": "Student",
            "extracted_attributes": ["name: str"],
            "swea_coordination": invalid_coordination_plan,
            "is_evolution": False,
        }

        # Access the actual bae_registry property and mock its methods
        bae_registry = kernel.bae_registry
        entity_recognizer = kernel.entity_recognizer

        # Mock the BAE registry to return our mock BAE
        with (
            patch.object(bae_registry, "get_bae", return_value=mock_bae),
            patch.object(bae_registry, "is_entity_supported", return_value=True),
            patch.object(
                entity_recognizer,
                "recognize_entity",
                return_value={"detected_entity": "student", "confidence": 0.9},
            ),
        ):
            # Process request - should fail with validation error
            result = kernel.process_natural_language_request(
                "Create a student with name", start_servers=False
            )

            # Verify that generation was interrupted due to validation error
            assert result["success"] is False
            assert result["error"] == "VALIDATION_ERROR"
            assert "validation failure" in result["message"]
            assert result["generation_interrupted"] is True
            assert result["validation_failed"] is True

            # Verify error details contain validation information
            assert "validation_error" in result["details"]
            assert "coordination_plan" in result["details"]

            # Verify helpful error message for user
            assert "agent communication protocol" in result["help"]
            assert "system configuration issue" in result["help"]

    def test_mandatory_attribute_validation_in_kernel(self, kernel):
        """Test that the kernel validates mandatory attributes before execution"""
        # Test tasks with missing mandatory attributes
        invalid_tasks = [
            {"task_type": "generate_model", "payload": {}},  # Missing swea_agent
            {"swea_agent": "BackendSWEA", "payload": {}},  # Missing task_type
            {"swea_agent": "BackendSWEA", "task_type": "generate_model"},  # Missing payload
            {"swea_agent": "", "task_type": "generate_model", "payload": {}},  # Empty swea_agent
            {"swea_agent": "BackendSWEA", "task_type": "", "payload": {}},  # Empty task_type
        ]

        for i, invalid_task in enumerate(invalid_tasks):
            with pytest.raises(ValueError) as exc_info:
                kernel._execute_coordination_plan([invalid_task], None, "academic")

            # Verify the error message is descriptive
            error_msg = str(exc_info.value)
            assert "validation failed" in error_msg.lower()
            # Check for either "mandatory attribute" or "missing" in the error message
            assert "mandatory attribute" in error_msg.lower() or "missing" in error_msg.lower()

    def test_unknown_swea_agent_validation(self, kernel):
        """Test that unknown SWEA agents trigger immediate validation failure"""
        invalid_task = {
            "swea_agent": "NonExistentSWEA",  # Unknown SWEA agent
            "task_type": "some_task",
            "payload": {"entity": "Student"},
        }

        with pytest.raises(ValueError) as exc_info:
            kernel._execute_coordination_plan([invalid_task], None, "academic")

        error_msg = str(exc_info.value)
        assert "Unknown SWEA agent" in error_msg
        assert "NonExistentSWEA" in error_msg

    def test_coordination_plan_validation_in_bae(self):
        """Test that BAE validates coordination plan before returning it"""
        # Create a real StudentBae instance
        student_bae = StudentBae()

        # Mock the LLM to return a response that would create invalid coordination plan
        with patch.object(student_bae.llm, "generate_domain_entity_response") as mock_llm:
            mock_llm.return_value = '["name: str", "email: str"]'

            # Test with valid request first
            valid_result = student_bae.handle(
                "interpret_business_request",
                {"request": "Create a student with name and email", "context": "academic"},
            )

            # Should succeed with valid coordination plan
            assert "error" not in valid_result
            assert "swea_coordination" in valid_result
            assert len(valid_result["swea_coordination"]) > 0

            # Verify all tasks have mandatory attributes
            for task in valid_result["swea_coordination"]:
                assert "swea_agent" in task
                assert "task_type" in task
                assert "payload" in task
                assert task["swea_agent"].strip()  # Not empty
                assert task["task_type"].strip()  # Not empty
                assert isinstance(task["payload"], dict)

    def test_error_propagation_to_user_interface(self, kernel):
        """Test that validation errors properly propagate to the user interface"""
        # Mock a scenario where BAE returns validation error
        mock_bae = Mock(spec=StudentBae)
        mock_bae.name = "StudentBae"
        mock_bae.entity_name = "Student"

        # Mock BAE to return validation error
        mock_bae.handle.return_value = {
            "error": "Coordination plan validation failed: ['Task 1: Missing swea_agent']",
            "entity": "Student",
            "validation_errors": ["Task 1: Missing swea_agent"],
        }

        # Access the actual properties and mock their methods
        bae_registry = kernel.bae_registry
        entity_recognizer = kernel.entity_recognizer

        # Mock the BAE registry
        with (
            patch.object(bae_registry, "get_bae", return_value=mock_bae),
            patch.object(bae_registry, "is_entity_supported", return_value=True),
            patch.object(
                entity_recognizer,
                "recognize_entity",
                return_value={"detected_entity": "student", "confidence": 0.9},
            ),
        ):
            # Process request
            result = kernel.process_natural_language_request(
                "Create a student", start_servers=False
            )

            # Verify that BAE interpretation error is properly handled
            assert result["success"] is False
            assert result["error"] == "BAE_INTERPRETATION_FAILED"
            assert "could not interpret" in result["message"]
            assert result["entity"] == "student"

    def test_fail_fast_behavior_prevents_partial_execution(self, kernel):
        """Test that validation errors prevent any partial execution of tasks"""
        execution_count = 0

        def mock_handle_task(task_type, payload):
            nonlocal execution_count
            execution_count += 1
            return {"success": True, "result": "mocked"}

        # Create coordination plan with validation error at the BEGINNING to ensure fail-fast
        coordination_plan = [
            {
                "swea_agent": "",
                "task_type": "generate_model",
                "payload": {},
            },  # Invalid - empty swea_agent - FIRST task
            {
                "swea_agent": "DatabaseSWEA",
                "task_type": "setup_database",
                "payload": {"entity": "Student"},
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {"entity": "Student"},
            },
        ]

        # Mock all SWEA agents
        with (
            patch.object(kernel.database_swea, "handle_task", side_effect=mock_handle_task),
            patch.object(kernel.backend_swea, "handle_task", side_effect=mock_handle_task),
            patch.object(kernel.frontend_swea, "handle_task", side_effect=mock_handle_task),
        ):
            # Should fail fast on validation error
            with pytest.raises(ValueError):
                kernel._execute_coordination_plan(coordination_plan, None, "academic")

            # Verify no tasks were executed due to fail-fast behavior
            assert execution_count == 0, "No tasks should be executed when validation fails"

    def test_comprehensive_validation_error_reporting(self, kernel):
        """Test comprehensive validation error reporting and recovery suggestions"""
        # Create a task with multiple validation issues
        invalid_task = {
            "swea_agent": "",  # Empty agent
            "task_type": "",  # Empty task type
            "payload": None,  # Invalid payload
        }

        with pytest.raises(ValueError) as exc_info:
            kernel._execute_coordination_plan([invalid_task], None, "academic")

        error_msg = str(exc_info.value)

        # Should catch the first validation error and report it clearly
        assert "validation failed" in error_msg.lower()
        assert "swea_agent" in error_msg.lower()

        # Should provide context about the problematic task
        assert "task:" in error_msg.lower()

    def test_complete_validation_flow_demonstration(self, kernel):
        """Comprehensive test demonstrating the complete validation error flow"""
        print("\n🔍 Testing Complete Validation Error Flow")

        # Create a mock BAE that returns an invalid coordination plan
        mock_bae = Mock(spec=StudentBae)
        mock_bae.name = "StudentBae"
        mock_bae.entity_name = "Student"

        # Create coordination plan with validation errors
        invalid_coordination_plan = [
            {
                # This task is missing swea_agent - should trigger immediate validation error
                "task_type": "generate_model",
                "payload": {"entity": "Student", "attributes": ["name: str"]},
            }
        ]

        mock_bae.handle.return_value = {
            "entity": "Student",
            "extracted_attributes": ["name: str"],
            "swea_coordination": invalid_coordination_plan,
            "is_evolution": False,
        }

        # Access the actual properties and mock their methods
        bae_registry = kernel.bae_registry
        entity_recognizer = kernel.entity_recognizer

        # Mock the BAE registry
        with (
            patch.object(bae_registry, "get_bae", return_value=mock_bae),
            patch.object(bae_registry, "is_entity_supported", return_value=True),
            patch.object(
                entity_recognizer,
                "recognize_entity",
                return_value={"detected_entity": "student", "confidence": 0.9},
            ),
        ):
            print("   📝 Processing request with invalid coordination plan...")

            # Process request - should fail with validation error
            result = kernel.process_natural_language_request(
                "Create a student with name", start_servers=False
            )

            print(f"   ✅ Request completed with result: {result['success']}")
            print(f"   🛑 Error type: {result.get('error', 'None')}")
            print(f"   📋 Message: {result.get('message', 'None')}")

            # Verify that generation was interrupted due to validation error
            assert result["success"] is False, "Request should fail due to validation error"
            assert result["error"] == "VALIDATION_ERROR", "Should be a validation error"
            assert "validation failure" in result["message"], "Should mention validation failure"
            assert result["generation_interrupted"] is True, "Generation should be interrupted"
            assert result["validation_failed"] is True, "Validation should be marked as failed"

            # Verify error details contain validation information
            assert (
                "validation_error" in result["details"]
            ), "Should contain validation error details"
            assert (
                "coordination_plan" in result["details"]
            ), "Should contain coordination plan details"

            # Verify helpful error message for user
            assert (
                "agent communication protocol" in result["help"]
            ), "Should provide help about agent communication"
            assert "system configuration issue" in result["help"], "Should indicate system issue"

            print("   ✅ All validation behaviors confirmed!")
            print("   🚫 Generation process was properly interrupted")
            print("   📊 Error details provided to user")
            print("   💡 Recovery suggestions included")

        print("\n🎯 Complete Validation Flow Test: PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
