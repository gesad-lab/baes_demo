#!/usr/bin/env python3
"""
Integration test for entity attribute validation.

This test ensures that when entities are created without specific attributes mentioned,
they use their default attributes instead of being created with empty attribute lists.

This addresses the issue where "add teacher" and "add course" commands were creating
entities without any attributes.
"""

from unittest.mock import Mock, patch

import pytest

from baes.domain_entities.academic.course_bae import CourseBae
from baes.domain_entities.academic.student_bae import StudentBae
from baes.domain_entities.academic.teacher_bae import TeacherBae


class TestEntityAttributeValidation:
    """Test entity attribute validation with mocked LLM responses"""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client to return controlled responses"""
        with patch("baes.llm.openai_client.OpenAIClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client

    def test_student_bae_empty_attributes_handling(self, mock_openai_client):
        """Test that StudentBae handles empty LLM attribute responses correctly"""
        # Mock LLM returning empty attributes (simulating the bug scenario)
        mock_openai_client.generate_response.return_value = "[]"

        student_bae = StudentBae()
        result = student_bae.interpret_business_request("add student")

        # Verify that default attributes are used when LLM returns empty
        assert "extracted_attributes" in result
        extracted_attributes = result["extracted_attributes"]
        assert len(extracted_attributes) > 0
        assert any("name" in attr.lower() for attr in extracted_attributes)

        # Verify coordination plan uses the corrected attributes
        coordination_plan = result.get("swea_coordination", [])
        for task in coordination_plan:
            payload_attributes = task.get("payload", {}).get("attributes", [])
            assert len(payload_attributes) > 0, f"Task {task.get('task_type')} has empty attributes"
            assert payload_attributes == extracted_attributes

    def test_teacher_bae_empty_attributes_handling(self, mock_openai_client):
        """Test that TeacherBae handles empty LLM attribute responses correctly"""
        # Mock LLM returning empty attributes
        mock_openai_client.generate_response.return_value = "[]"

        teacher_bae = TeacherBae()
        result = teacher_bae.interpret_business_request("add teacher")

        # Verify that default attributes are used
        assert "extracted_attributes" in result
        extracted_attributes = result["extracted_attributes"]
        assert len(extracted_attributes) > 0
        assert any("name" in attr.lower() for attr in extracted_attributes)

        # Verify coordination plan uses the corrected attributes
        coordination_plan = result.get("swea_coordination", [])
        for task in coordination_plan:
            payload_attributes = task.get("payload", {}).get("attributes", [])
            assert len(payload_attributes) > 0
            assert payload_attributes == extracted_attributes

    def test_course_bae_empty_attributes_handling(self, mock_openai_client):
        """Test that CourseBae handles empty LLM attribute responses correctly"""
        # Mock LLM returning empty attributes
        mock_openai_client.generate_response.return_value = "[]"

        course_bae = CourseBae()
        result = course_bae.interpret_business_request("add course")

        # Verify that default attributes are used
        assert "extracted_attributes" in result
        extracted_attributes = result["extracted_attributes"]
        assert len(extracted_attributes) > 0
        assert any("name" in attr.lower() for attr in extracted_attributes)

        # Verify coordination plan uses the corrected attributes
        coordination_plan = result.get("swea_coordination", [])
        for task in coordination_plan:
            payload_attributes = task.get("payload", {}).get("attributes", [])
            assert len(payload_attributes) > 0
            assert payload_attributes == extracted_attributes

    def test_various_request_formats(self, mock_openai_client):
        """Test that various request formats work correctly with empty LLM responses"""
        # Mock LLM returning empty attributes for all requests
        mock_openai_client.generate_response.return_value = "[]"

        student_bae = StudentBae()
        test_requests = [
            "add student",
            "create student",
            "generate student entity",
            "I need a student management system",
        ]

        for request in test_requests:
            result = student_bae.interpret_business_request(request)
            extracted_attributes = result["extracted_attributes"]
            assert (
                len(extracted_attributes) > 0
            ), f"Request '{request}' resulted in empty attributes"

            # Verify all coordination tasks have attributes
            coordination_plan = result.get("swea_coordination", [])
            for task in coordination_plan:
                payload_attributes = task.get("payload", {}).get("attributes", [])
                assert (
                    len(payload_attributes) > 0
                ), f"Request '{request}' task {task.get('task_type')} has empty attributes"

    def test_coordination_plan_consistency(self, mock_openai_client):
        """Test that all tasks in coordination plan have consistent attributes"""
        # Mock LLM returning empty attributes
        mock_openai_client.generate_response.return_value = "[]"

        student_bae = StudentBae()
        result = student_bae.interpret_business_request("add student")

        extracted_attributes = result["extracted_attributes"]
        coordination_plan = result.get("swea_coordination", [])

        # Verify all tasks have the same attributes
        for task in coordination_plan:
            payload_attributes = task.get("payload", {}).get("attributes", [])
            assert (
                payload_attributes == extracted_attributes
            ), f"Task {task.get('task_type')} has inconsistent attributes"

    def test_non_empty_llm_response_preserved(self, mock_openai_client):
        """Test that non-empty LLM responses are preserved correctly"""
        # Mock LLM returning custom attributes
        custom_attributes = ["custom_name: str", "custom_id: int", "custom_field: str"]
        mock_openai_client.generate_response.return_value = str(custom_attributes)

        student_bae = StudentBae()
        result = student_bae.interpret_business_request("add student with custom fields")

        # Verify custom attributes are used (not defaults)
        extracted_attributes = result["extracted_attributes"]
        assert extracted_attributes == custom_attributes

        # Verify coordination plan uses custom attributes
        coordination_plan = result.get("swea_coordination", [])
        for task in coordination_plan:
            payload_attributes = task.get("payload", {}).get("attributes", [])
            assert payload_attributes == custom_attributes


if __name__ == "__main__":
    pytest.main([__file__])
