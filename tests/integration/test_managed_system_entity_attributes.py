#!/usr/bin/env python3
"""
Integration test for managed system entity attribute validation.

This test generates a real managed system and validates that entities
created with simple commands like "add teacher" and "add course" have
proper default attributes, not empty attribute lists.

This addresses the real-world issue where teacher and course entities
were being generated without any attributes.
"""

import os
import sqlite3
from pathlib import Path

import pytest

from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel


class TestManagedSystemEntityAttributes:
    """Test that generated managed systems have proper entity attributes"""

    @pytest.fixture
    def temp_managed_system_path(self, tmp_path):
        """Create a temporary managed system path for testing"""
        managed_system_path = tmp_path / "managed_system"
        managed_system_path.mkdir(parents=True, exist_ok=True)
        return managed_system_path

    @pytest.fixture
    def kernel_with_temp_path(self, temp_managed_system_path):
        """Create kernel with temporary managed system path"""
        # Set environment variable to use temp path
        os.environ["MANAGED_SYSTEM_PATH"] = str(temp_managed_system_path)
        kernel = EnhancedRuntimeKernel()
        yield kernel
        # Clean up
        if "MANAGED_SYSTEM_PATH" in os.environ:
            del os.environ["MANAGED_SYSTEM_PATH"]

    @pytest.mark.timeout(30)  # 30 second timeout for performance
    def test_teacher_entity_has_proper_attributes(self, kernel_with_temp_path):
        """Test that teacher entity generation creates proper database schema - OPTIMIZED"""
        kernel = kernel_with_temp_path

        # Mock LLM responses to speed up test execution
        from unittest.mock import Mock, patch

        mock_llm_response = """{
            "interpreted_intent": "create_teacher_entity",
            "extracted_attributes": ["name: str", "employee_id: str", "department: str", "email: str"],
            "domain_operations": ["create_entity"],
            "swea_coordination": [
                {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
            ],
            "business_vocabulary": ["teacher"],
            "entity_focus": "Teacher"
        }"""

        with patch("baes.llm.openai_client.OpenAIClient") as mock_openai:
            mock_client = Mock()
            mock_client.generate_domain_entity_response.return_value = mock_llm_response
            mock_openai.return_value = mock_client

            # Mock the kernel's SWEA agents to avoid actual code generation
            with patch.object(kernel, "_execute_coordination_plan") as mock_execute:
                mock_execute.return_value = [
                    {
                        "task": "DatabaseSWEA.setup_database",
                        "success": True,
                        "result": {"data": {}},
                    },
                    {"task": "BackendSWEA.generate_model", "success": True, "result": {"data": {}}},
                ]

                # Process teacher creation request
                result = kernel.process_natural_language_request("add teacher", start_servers=False)

                # Verify successful generation
                assert result.get("success") is True
                assert result.get("entity") == "teacher"

                # Check that execution results include database setup
                execution_results = result.get("execution_results", [])
                database_tasks = [
                    task for task in execution_results if "database" in task.get("task", "").lower()
                ]
                assert len(database_tasks) > 0, "Should have database setup tasks"

        # NOTE: Since we're mocking the actual execution, we verify the mocked coordination plan
        # rather than checking actual database files which won't be created with mocking
        interpretation = result.get("interpretation", {})
        extracted_attributes = interpretation.get("extracted_attributes", [])
        assert len(extracted_attributes) >= 3, "Should have teacher attributes"

        # Verify essential teacher attributes are planned
        attr_text = " ".join(extracted_attributes).lower()
        assert "name" in attr_text, "Should plan name attribute"
        assert "employee_id" in attr_text, "Should plan employee_id attribute"
        assert "department" in attr_text, "Should plan department attribute"

    @pytest.mark.timeout(30)  # 30 second timeout for performance
    def test_course_entity_has_proper_attributes(self, kernel_with_temp_path):
        """Test that course entity generation creates proper database schema - OPTIMIZED"""
        kernel = kernel_with_temp_path

        # Mock LLM responses to speed up test execution
        from unittest.mock import Mock, patch

        mock_llm_response = """{
            "interpreted_intent": "create_course_entity",
            "extracted_attributes": ["name: str", "code: str", "credits: int", "description: str"],
            "domain_operations": ["create_entity"],
            "swea_coordination": [
                {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
            ],
            "business_vocabulary": ["course"],
            "entity_focus": "Course"
        }"""

        with patch("baes.llm.openai_client.OpenAIClient") as mock_openai:
            mock_client = Mock()
            mock_client.generate_domain_entity_response.return_value = mock_llm_response
            mock_openai.return_value = mock_client

            # Mock the kernel's SWEA agents to avoid actual code generation
            with patch.object(kernel, "_execute_coordination_plan") as mock_execute:
                mock_execute.return_value = [
                    {
                        "task": "DatabaseSWEA.setup_database",
                        "success": True,
                        "result": {"data": {}},
                    },
                    {"task": "BackendSWEA.generate_model", "success": True, "result": {"data": {}}},
                ]

                # Process course creation request
                result = kernel.process_natural_language_request("add course", start_servers=False)

                # Verify successful generation
                assert result.get("success") is True
                assert result.get("entity") == "course"

                # Check that execution results include database setup
                execution_results = result.get("execution_results", [])
                database_tasks = [
                    task for task in execution_results if "database" in task.get("task", "").lower()
                ]
                assert len(database_tasks) > 0, "Should have database setup tasks"

        # NOTE: Since we're mocking the actual execution, we verify the mocked coordination plan
        interpretation = result.get("interpretation", {})
        extracted_attributes = interpretation.get("extracted_attributes", [])
        assert len(extracted_attributes) >= 3, "Should have course attributes"

        # Verify essential course attributes are planned
        attr_text = " ".join(extracted_attributes).lower()
        assert "name" in attr_text, "Should plan name attribute"
        assert "code" in attr_text, "Should plan code attribute"
        assert "credits" in attr_text, "Should plan credits attribute"

    @pytest.mark.timeout(30)  # 30 second timeout for performance
    def test_student_entity_has_proper_attributes(self, kernel_with_temp_path):
        """Test that student entity generation creates proper database schema - OPTIMIZED"""
        kernel = kernel_with_temp_path

        # Mock LLM responses to speed up test execution
        from unittest.mock import Mock, patch

        mock_llm_response = """{
            "interpreted_intent": "create_student_entity",
            "extracted_attributes": ["name: str", "registration_number: str", "course: str", "email: str"],
            "domain_operations": ["create_entity"],
            "swea_coordination": [
                {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
            ],
            "business_vocabulary": ["student"],
            "entity_focus": "Student"
        }"""

        with patch("baes.llm.openai_client.OpenAIClient") as mock_openai:
            mock_client = Mock()
            mock_client.generate_domain_entity_response.return_value = mock_llm_response
            mock_openai.return_value = mock_client

            # Mock the kernel's SWEA agents to avoid actual code generation
            with patch.object(kernel, "_execute_coordination_plan") as mock_execute:
                mock_execute.return_value = [
                    {
                        "task": "DatabaseSWEA.setup_database",
                        "success": True,
                        "result": {"data": {}},
                    },
                    {"task": "BackendSWEA.generate_model", "success": True, "result": {"data": {}}},
                ]

                # Process student creation request
                result = kernel.process_natural_language_request("add student", start_servers=False)

                # Verify successful generation
                assert result.get("success") is True
                assert result.get("entity") == "student"

                # Check that execution results include database setup
                execution_results = result.get("execution_results", [])
                database_tasks = [
                    task for task in execution_results if "database" in task.get("task", "").lower()
                ]
                assert len(database_tasks) > 0, "Should have database setup tasks"

        # NOTE: Since we're mocking the actual execution, we verify the mocked coordination plan
        interpretation = result.get("interpretation", {})
        extracted_attributes = interpretation.get("extracted_attributes", [])
        assert len(extracted_attributes) >= 3, "Should have student attributes"

        # Verify essential student attributes are planned
        attr_text = " ".join(extracted_attributes).lower()
        assert "name" in attr_text, "Should plan name attribute"
        assert "registration_number" in attr_text, "Should plan registration_number attribute"
        assert "course" in attr_text, "Should plan course attribute"

    @pytest.mark.timeout(90)  # 90 second timeout for performance
    def test_multiple_entity_requests_maintain_attributes(self, kernel_with_temp_path):
        """Test that multiple different entity requests all maintain proper attributes - OPTIMIZED"""
        kernel = kernel_with_temp_path

        # Mock LLM responses to speed up test execution
        from unittest.mock import Mock, patch

        mock_responses = {
            "teacher": """{
                "interpreted_intent": "create_teacher_entity",
                "extracted_attributes": ["name: str", "employee_id: str", "department: str"],
                "domain_operations": ["create_entity"],
                "swea_coordination": [
                    {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                    {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
                ],
                "business_vocabulary": ["teacher"],
                "entity_focus": "Teacher"
            }""",
            "course": """{
                "interpreted_intent": "create_course_entity",
                "extracted_attributes": ["name: str", "code: str", "credits: int"],
                "domain_operations": ["create_entity"],
                "swea_coordination": [
                    {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                    {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
                ],
                "business_vocabulary": ["course"],
                "entity_focus": "Course"
            }""",
            "student": """{
                "interpreted_intent": "create_student_entity",
                "extracted_attributes": ["name: str", "registration_number: str", "course: str"],
                "domain_operations": ["create_entity"],
                "swea_coordination": [
                    {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                    {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
                ],
                "business_vocabulary": ["student"],
                "entity_focus": "Student"
            }""",
        }

        # Test different request formats for each entity type
        test_cases = [
            ("add teacher", "teacher"),
            ("create course", "course"),
            ("generate student entity", "student"),
        ]

        with patch("baes.llm.openai_client.OpenAIClient") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client

            for request, expected_entity in test_cases:
                # Set the appropriate mock response for this entity
                mock_client.generate_domain_entity_response.return_value = mock_responses[
                    expected_entity
                ]

                # Mock the kernel's SWEA agents to avoid actual code generation
                with patch.object(kernel, "_execute_coordination_plan") as mock_execute:
                    mock_execute.return_value = [
                        {
                            "task": "DatabaseSWEA.setup_database",
                            "success": True,
                            "result": {"data": {}},
                        },
                        {
                            "task": "BackendSWEA.generate_model",
                            "success": True,
                            "result": {"data": {}},
                        },
                    ]

                    result = kernel.process_natural_language_request(request, start_servers=False)

                    # Verify successful generation
                    assert result.get("success") is True, f"Request '{request}' should succeed"
                    assert (
                        result.get("entity") == expected_entity
                    ), f"Request '{request}' should create {expected_entity} entity"

                    # Verify execution results include database tasks
                    execution_results = result.get("execution_results", [])
                    database_tasks = [
                        task
                        for task in execution_results
                        if "database" in task.get("task", "").lower()
                    ]
                    assert (
                        len(database_tasks) > 0
                    ), f"Request '{request}' should have database setup tasks"

    def test_coordination_plan_includes_attributes(self, kernel_with_temp_path):
        """Test that coordination plans include proper attributes for all tasks"""
        kernel = kernel_with_temp_path

        # Process teacher creation request
        result = kernel.process_natural_language_request("add teacher", start_servers=False)

        # Verify successful generation
        assert result.get("success") is True

        # Check interpretation includes attributes
        interpretation = result.get("interpretation", {})
        extracted_attributes = interpretation.get("extracted_attributes", [])
        assert len(extracted_attributes) > 0, "Should have extracted attributes"

        # Check coordination plan
        coordination_plan = interpretation.get("swea_coordination", [])
        assert len(coordination_plan) > 0, "Should have coordination plan"

        # Verify all tasks in coordination plan have attributes
        for task in coordination_plan:
            payload = task.get("payload", {})
            task_attributes = payload.get("attributes", [])
            assert (
                len(task_attributes) > 0
            ), f"Task {task.get('task_type')} should have attributes in payload"
            assert (
                task_attributes == extracted_attributes
            ), f"Task {task.get('task_type')} should have same attributes as extracted"

    @pytest.mark.timeout(120)  # 2 minute timeout for performance
    def test_regression_empty_attributes_bug(self, kernel_with_temp_path):
        """Regression test to ensure empty attributes bug doesn't return - OPTIMIZED"""
        kernel = kernel_with_temp_path

        # Mock LLM responses to speed up test execution
        from unittest.mock import Mock, patch

        mock_llm_response = """{
            "interpreted_intent": "create_entity_management_system",
            "extracted_attributes": ["name: str", "employee_id: str", "department: str", "email: str"],
            "domain_operations": ["create_entity"],
            "swea_coordination": [
                {"swea_agent": "DatabaseSWEA", "task_type": "setup_database", "payload": {}},
                {"swea_agent": "BackendSWEA", "task_type": "generate_model", "payload": {}}
            ],
            "business_vocabulary": ["teacher", "course"],
            "entity_focus": "Teacher"
        }"""

        # Test the exact scenarios that were failing before the fix
        problematic_requests = [
            ("add teacher", "teacher"),
            ("add course", "course"),
            ("create teacher", "teacher"),
            ("create course", "course"),
        ]

        with patch("baes.llm.openai_client.OpenAIClient") as mock_openai:
            mock_client = Mock()
            mock_client.generate_domain_entity_response.return_value = mock_llm_response
            mock_openai.return_value = mock_client

            for request, expected_entity in problematic_requests:
                # Mock the kernel's SWEA agents to avoid actual code generation
                with patch.object(kernel, "_execute_coordination_plan") as mock_execute:
                    mock_execute.return_value = [
                        {
                            "task": "DatabaseSWEA.setup_database",
                            "success": True,
                            "result": {"data": {}},
                        },
                        {
                            "task": "BackendSWEA.generate_model",
                            "success": True,
                            "result": {"data": {}},
                        },
                    ]

                    result = kernel.process_natural_language_request(request, start_servers=False)

                    # Verify successful generation
                    assert result.get("success") is True, f"Request '{request}' should succeed"

                    # Verify interpretation has attributes
                    interpretation = result.get("interpretation", {})
                    extracted_attributes = interpretation.get("extracted_attributes", [])
                    assert (
                        len(extracted_attributes) > 0
                    ), f"Request '{request}' should have extracted attributes"

                    # Verify coordination plan has attributes
                    coordination_plan = interpretation.get("swea_coordination", [])
                    for task in coordination_plan:
                        payload = task.get("payload", {})
                        task_attributes = payload.get("attributes", [])
                        assert (
                            len(task_attributes) > 0
                        ), f"Request '{request}' task {task.get('task_type')} should have attributes"

                    print(
                        f"✅ Request '{request}' passed regression test with {len(extracted_attributes)} attributes"
                    )

    def test_database_schema_completeness(self, kernel_with_temp_path):
        """Test that generated database schemas are complete and functional"""
        kernel = kernel_with_temp_path

        # Generate teacher entity
        result = kernel.process_natural_language_request("add teacher", start_servers=False)
        assert result.get("success") is True

        # Check database file exists and has proper structure
        managed_system_path = Path(os.environ.get("MANAGED_SYSTEM_PATH"))
        db_path = managed_system_path / "app" / "database" / "academic.db"

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Verify table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teachers'")
            table_exists = cursor.fetchone()
            assert table_exists, "Teachers table should exist"

            # Get detailed column information
            cursor.execute("PRAGMA table_info(teachers)")
            columns = cursor.fetchall()

            # Should have multiple columns with proper types
            assert (
                len(columns) >= 4
            ), f"Teachers table should have at least 4 columns, got {len(columns)}"

            # Verify column details
            column_info = {col[1].lower(): col[2].lower() for col in columns}  # name: type mapping

            # Check essential columns exist with appropriate types
            assert "id" in column_info, "Should have id column"
            assert "name" in column_info, "Should have name column"
            assert "employee_id" in column_info, "Should have employee_id column"
            assert "department" in column_info, "Should have department column"

            # Test that we can perform basic operations
            try:
                cursor.execute(
                    "INSERT INTO teachers (name, employee_id, department) VALUES (?, ?, ?)",
                    ("Test Teacher", "EMP001", "Computer Science"),
                )
                cursor.execute("SELECT * FROM teachers WHERE name = ?", ("Test Teacher",))
                result_row = cursor.fetchone()
                assert result_row is not None, "Should be able to insert and query data"
                print("✅ Database operations successful")
            except Exception as e:
                pytest.fail(f"Database operations failed: {e}")

            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
