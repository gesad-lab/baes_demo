#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Entity Evolution Scenarios
Tests addition, exclusion, and modification of attributes in BAE entities.
"""

import os
from pathlib import Path

import pytest

from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel

# Set up environment for tests
os.environ["MANAGED_SYSTEM_PATH"] = str(Path(__file__).parent.parent / ".temp")


@pytest.mark.integration
class TestEntityEvolutionScenarios:
    """Comprehensive test suite for entity evolution scenarios"""

    @pytest.fixture
    def kernel_with_temp_path(self):
        """Create kernel with temporary managed system path"""
        kernel = EnhancedRuntimeKernel()
        return kernel

    @pytest.fixture
    def student_bae_with_schema(self, kernel_with_temp_path):
        """Create StudentBAE with initial schema for evolution testing"""
        kernel = kernel_with_temp_path
        bae = kernel.bae_registry.get_bae("student")

        # Set up initial schema with common student attributes
        initial_schema = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str", "course: str", "age: int"],
            "context": "academic",
            "generated_at": "2023-01-01T00:00:00",
            "business_rules": ["Registration number must be unique"],
            "code": "class Student(BaseModel): pass",
        }
        bae.update_memory("current_schema", initial_schema)
        return bae

    # =========================
    # ATTRIBUTE ADDITION TESTS
    # =========================

    def test_add_single_attribute_email(self, student_bae_with_schema):
        """Test adding a single email attribute to existing student entity"""
        bae = student_bae_with_schema

        # Test adding email attribute
        result = bae.handle(
            "interpret_business_request",
            {"request": "add email address to student entity", "context": "academic"},
        )

        # Verify evolution was detected
        assert result.get("is_evolution") is True
        assert "Add attributes to existing Student entity" in result.get("interpreted_intent", "")

        # Verify attributes
        all_attributes = result.get("extracted_attributes", [])
        new_attributes = result.get("new_attributes", [])
        existing_attributes = result.get("existing_attributes", [])

        assert len(all_attributes) == 5  # 4 original + 1 new
        assert "email: str" in new_attributes
        assert len(existing_attributes) == 4
        assert "name: str" in existing_attributes
        assert "registration_number: str" in existing_attributes
        assert "course: str" in existing_attributes
        assert "age: int" in existing_attributes

    def test_add_multiple_attributes(self, student_bae_with_schema):
        """Test adding multiple attributes at once"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {"request": "add phone number and birth date to student entity", "context": "academic"},
        )

        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])
        new_attributes = result.get("new_attributes", [])

        assert len(all_attributes) >= 6  # 4 original + at least 2 new
        assert len(new_attributes) >= 1
        # Should contain phone or birth date related attributes
        new_attrs_str = " ".join(new_attributes)
        assert "phone" in new_attrs_str.lower() or "birth" in new_attrs_str.lower()

    def test_add_attribute_with_different_request_formats(self, student_bae_with_schema):
        """Test various ways of requesting attribute addition"""
        bae = student_bae_with_schema

        test_requests = [
            "for student entity, add the attribute email address",
            "add email field to student",
            "include email in student entity",
            "student entity needs email attribute",
            "extend student with email property",
        ]

        for request in test_requests:
            result = bae.handle(
                "interpret_business_request", {"request": request, "context": "academic"}
            )

            assert result.get("is_evolution") is True, f"Evolution not detected for: {request}"
            all_attributes = result.get("extracted_attributes", [])
            assert len(all_attributes) >= 4, f"Attributes not preserved for: {request}"

    # =========================
    # ATTRIBUTE EXCLUSION TESTS
    # =========================

    def test_remove_single_attribute(self, student_bae_with_schema):
        """Test removing a single attribute from existing entity"""
        bae = student_bae_with_schema

        # Test removing age attribute
        result = bae.handle(
            "interpret_business_request",
            {"request": "remove age attribute from student entity", "context": "academic"},
        )

        # Should detect as evolution
        assert result.get("is_evolution") is True

        # Verify age is removed but other attributes remain
        all_attributes = result.get("extracted_attributes", [])
        assert len(all_attributes) == 3  # 4 original - 1 removed
        assert "age: int" not in all_attributes
        assert "name: str" in all_attributes
        assert "registration_number: str" in all_attributes
        assert "course: str" in all_attributes

    def test_remove_multiple_attributes(self, student_bae_with_schema):
        """Test removing multiple attributes"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {
                "request": "remove age and course attributes from student entity",
                "context": "academic",
            },
        )

        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])
        assert len(all_attributes) == 2  # 4 original - 2 removed
        assert "age: int" not in all_attributes
        assert "course: str" not in all_attributes
        assert "name: str" in all_attributes
        assert "registration_number: str" in all_attributes

    def test_remove_nonexistent_attribute(self, student_bae_with_schema):
        """Test removing attribute that doesn't exist"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {"request": "remove email attribute from student entity", "context": "academic"},
        )

        # Should still be evolution but no change in attributes
        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])
        assert len(all_attributes) == 4  # Same as original

        # Verify original attributes are preserved
        assert "name: str" in all_attributes
        assert "registration_number: str" in all_attributes
        assert "course: str" in all_attributes
        assert "age: int" in all_attributes

    # =========================
    # ATTRIBUTE MODIFICATION TESTS
    # =========================

    def test_modify_attribute_type(self, student_bae_with_schema):
        """Test modifying an attribute's data type"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {
                "request": "change age attribute from int to str in student entity",
                "context": "academic",
            },
        )

        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])

        # Should still have 4 attributes but age should be str
        assert len(all_attributes) == 4
        assert "age: str" in all_attributes
        assert "age: int" not in all_attributes

    def test_rename_attribute(self, student_bae_with_schema):
        """Test renaming an attribute"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {
                "request": "rename registration_number to student_id in student entity",
                "context": "academic",
            },
        )

        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])

        # Should still have 4 attributes but with new name
        assert len(all_attributes) == 4
        assert "student_id: str" in all_attributes
        assert "registration_number: str" not in all_attributes

    def test_modify_attribute_constraints(self, student_bae_with_schema):
        """Test modifying attribute constraints or validation"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {"request": "make name attribute optional in student entity", "context": "academic"},
        )

        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])

        # Should still have 4 attributes but name should be optional
        assert len(all_attributes) == 4
        # Should contain optional name (could be Optional[str] or similar)
        name_attrs = [attr for attr in all_attributes if "name" in attr.lower()]
        assert len(name_attrs) >= 1

    # =========================
    # COMPLEX EVOLUTION TESTS
    # =========================

    def test_complex_evolution_add_remove_modify(self, student_bae_with_schema):
        """Test complex evolution with multiple operations"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {
                "request": "add email attribute, remove age attribute, and change course to program in student entity",
                "context": "academic",
            },
        )

        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])

        # Should have email, not have age, and have program instead of course
        email_present = any("email" in attr.lower() for attr in all_attributes)
        age_present = any("age" in attr.lower() for attr in all_attributes)
        program_present = any("program" in attr.lower() for attr in all_attributes)
        course_present = any("course" in attr.lower() for attr in all_attributes)

        assert email_present, "Email attribute should be added"
        assert not age_present, "Age attribute should be removed"
        assert program_present, "Program attribute should be present"
        assert not course_present, "Course attribute should be replaced"

    def test_evolution_maintains_business_rules(self, student_bae_with_schema):
        """Test that evolution maintains business rules and context"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {"request": "add email attribute to student entity", "context": "academic"},
        )

        assert result.get("is_evolution") is True
        assert result.get("entity") == "Student"
        assert result.get("business_vocabulary") is not None
        assert "student" in result.get("business_vocabulary", [])

    # =========================
    # EDGE CASES AND ERROR HANDLING
    # =========================

    def test_evolution_without_existing_schema(self, kernel_with_temp_path):
        """Test evolution request when no existing schema exists"""
        kernel = kernel_with_temp_path
        bae = kernel.bae_registry.get_bae("student")

        # No existing schema stored
        result = bae.handle(
            "interpret_business_request",
            {"request": "add email attribute to student entity", "context": "academic"},
        )

        # Should fall back to normal creation, not evolution
        assert result.get("is_evolution") is not True
        assert result.get("extracted_attributes") is not None

    def test_evolution_with_invalid_attribute_syntax(self, student_bae_with_schema):
        """Test evolution with malformed attribute requests"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {"request": "add some weird attribute thing to student entity", "context": "academic"},
        )

        # Should still detect as evolution but handle gracefully
        assert result.get("is_evolution") is True
        all_attributes = result.get("extracted_attributes", [])
        assert len(all_attributes) >= 4  # Should preserve existing attributes

    def test_evolution_request_patterns(self, student_bae_with_schema):
        """Test various evolution request patterns are recognized"""
        bae = student_bae_with_schema

        evolution_patterns = [
            "modify student entity to include email",
            "update student with phone number",
            "enhance student entity with birth date",
            "extend student to have address",
            "student entity should also have gpa",
        ]

        for pattern in evolution_patterns:
            result = bae.handle(
                "interpret_business_request", {"request": pattern, "context": "academic"}
            )

            assert (
                result.get("is_evolution") is True
            ), f"Pattern not recognized as evolution: {pattern}"
            assert (
                len(result.get("extracted_attributes", [])) > 4
            ), f"Attributes not preserved for: {pattern}"

    # =========================
    # COORDINATION PLAN TESTS
    # =========================

    def test_evolution_coordination_plan_structure(self, student_bae_with_schema):
        """Test that evolution creates proper coordination plan"""
        bae = student_bae_with_schema

        result = bae.handle(
            "interpret_business_request",
            {"request": "add email attribute to student entity", "context": "academic"},
        )

        assert result.get("is_evolution") is True
        coordination_plan = result.get("swea_coordination", [])

        # Should have coordination plan
        assert len(coordination_plan) > 0

        # All tasks should have is_evolution flag
        for task in coordination_plan:
            payload = task.get("payload", {})
            assert payload.get("is_evolution") is True, f"Task missing evolution flag: {task}"

            # All tasks should have the combined attributes
            attributes = payload.get("attributes", [])
            assert len(attributes) >= 4, f"Task missing combined attributes: {task}"

    def test_evolution_vs_creation_coordination_differences(self, kernel_with_temp_path):
        """Test differences between evolution and creation coordination plans"""
        kernel = kernel_with_temp_path
        bae = kernel.bae_registry.get_bae("student")

        # Test creation (no existing schema)
        creation_result = bae.handle(
            "interpret_business_request",
            {"request": "create student entity with email", "context": "academic"},
        )

        # Set up schema and test evolution
        initial_schema = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str"],
            "context": "academic",
            "generated_at": "2023-01-01T00:00:00",
        }
        bae.update_memory("current_schema", initial_schema)

        evolution_result = bae.handle(
            "interpret_business_request",
            {"request": "add email attribute to student entity", "context": "academic"},
        )

        # Compare results
        creation_is_evolution = creation_result.get("is_evolution", False)
        evolution_is_evolution = evolution_result.get("is_evolution", False)

        assert not creation_is_evolution, "Creation should not be flagged as evolution"
        assert evolution_is_evolution, "Evolution should be flagged as evolution"

        # Evolution should have more attributes (preserved + new)
        creation_attrs = len(creation_result.get("extracted_attributes", []))
        evolution_attrs = len(evolution_result.get("extracted_attributes", []))

        assert evolution_attrs > creation_attrs, "Evolution should preserve existing attributes"

    def test_evolution_triggers_test_execution(self, kernel_with_temp_path):
        """Test that evolution triggers automatic test execution to validate changes"""
        kernel = kernel_with_temp_path

        # Set up initial schema
        bae = kernel.bae_registry.get_bae("student")
        initial_schema = {
            "entity": "Student",
            "attributes": ["name: str", "registration_number: str"],
            "context": "academic",
            "generated_at": "2023-01-01T00:00:00",
        }
        bae.update_memory("current_schema", initial_schema)

        # Mock the test execution to avoid actual test running in unit tests
        from unittest.mock import patch

        with patch.object(kernel, "_execute_evolution_tests") as mock_execute_tests:
            mock_execute_tests.return_value = {
                "success": True,
                "tests_executed": 5,
                "tests_passed": 5,
                "tests_failed": 0,
                "entity": "Student",
                "evolution_validation": True,
            }

            # Process evolution request that should trigger test execution
            result = kernel.process_natural_language_request(
                "add email attribute to student entity", start_servers=False
            )

            # Verify evolution was successful
            assert result.get("success") is True

            # Verify evolution tests were triggered
            mock_execute_tests.assert_called_once()
            call_args = mock_execute_tests.call_args
            assert call_args[0][0] == "student"  # entity parameter

            # Verify execution results include test execution
            execution_results = result.get("execution_results", [])
            test_execution_result = None
            for task_result in execution_results:
                if "execute_evolution_tests" in task_result.get("task", ""):
                    test_execution_result = task_result
                    break

            assert test_execution_result is not None, "Test execution result should be present"
            assert (
                test_execution_result.get("success") is True
            ), "Test execution should be successful"

            # Verify test execution details
            test_details = test_execution_result.get("result", {})
            assert test_details.get("evolution_validation") is True
            assert test_details.get("tests_executed", 0) > 0

    def test_evolution_test_execution_integration(self, kernel_with_temp_path):
        """Test full integration of evolution with test execution (using actual TestSWEA)"""
        kernel = kernel_with_temp_path

        # Set up initial schema
        bae = kernel.bae_registry.get_bae("student")
        initial_schema = {
            "entity": "Student",
            "attributes": ["name: str", "age: int"],
            "context": "academic",
            "generated_at": "2023-01-01T00:00:00",
        }
        bae.update_memory("current_schema", initial_schema)

        # Test the _execute_evolution_tests method directly
        # Create mock execution results that include TestSWEA
        mock_execution_results = [
            {
                "task": "TestSWEA.generate_all_tests_with_collaboration",
                "success": True,
                "result": {"data": {"test_generation": "completed"}},
                "entity": "Student",
            }
        ]

        # Mock the TestSWEA execute_tests method to avoid actual test execution
        from unittest.mock import patch

        with patch.object(kernel.test_swea, "handle_task") as mock_handle_task:
            mock_handle_task.return_value = {
                "success": True,
                "data": {
                    "tests_executed": 3,
                    "test_execution": {
                        "success": True,
                        "tests_passed": 3,
                        "tests_failed": 0,
                        "execution_time": 2.5,
                    },
                },
            }

            # Execute evolution tests
            result = kernel._execute_evolution_tests("Student", mock_execution_results)

            # Verify test execution was called with correct parameters
            mock_handle_task.assert_called_once_with(
                "execute_tests",
                {
                    "entity": "Student",
                    "execution_type": "evolution_validation",
                    "validate_after_changes": True,
                },
            )

            # Verify result structure
            assert result.get("success") is True
            assert result.get("entity") == "Student"
            assert result.get("evolution_validation") is True
            assert result.get("tests_executed") == 3
            assert result.get("tests_passed") == 3
            assert result.get("tests_failed") == 0

    def test_evolution_test_execution_failure_handling(self, kernel_with_temp_path):
        """Test handling of test execution failures during evolution"""
        kernel = kernel_with_temp_path

        # Create mock execution results without TestSWEA
        mock_execution_results = [
            {
                "task": "BackendSWEA.generate_model",
                "success": True,
                "result": {"data": {"model_generation": "completed"}},
                "entity": "Student",
            }
        ]

        # Test when no TestSWEA execution is found
        result = kernel._execute_evolution_tests("Student", mock_execution_results)

        assert result.get("success") is False
        assert "No test generation found" in result.get("error", "")
        assert result.get("entity") == "Student"
