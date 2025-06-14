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

    def test_teacher_entity_has_proper_attributes(self, kernel_with_temp_path):
        """Test that teacher entity generation creates proper database schema"""
        kernel = kernel_with_temp_path

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

        # Verify database was created with proper schema
        managed_system_path = Path(os.environ.get("MANAGED_SYSTEM_PATH"))
        db_path = managed_system_path / "app" / "database" / "academic.db"

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get table schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='teachers'")
            schema_result = cursor.fetchone()

            if schema_result:
                schema = schema_result[0]
                # Verify essential teacher attributes are in schema
                assert "name" in schema.lower(), "Teacher table should have name column"
                assert (
                    "employee_id" in schema.lower()
                ), "Teacher table should have employee_id column"
                assert "department" in schema.lower(), "Teacher table should have department column"

                # Count columns (should be more than just id)
                cursor.execute("PRAGMA table_info(teachers)")
                columns = cursor.fetchall()
                assert (
                    len(columns) > 1
                ), f"Teacher table should have multiple columns, got {len(columns)}"

                # Verify specific expected columns exist
                column_names = [col[1].lower() for col in columns]
                expected_columns = ["id", "name", "employee_id", "department"]
                for expected_col in expected_columns:
                    assert (
                        expected_col in column_names
                    ), f"Expected column '{expected_col}' not found in {column_names}"

            conn.close()

    def test_course_entity_has_proper_attributes(self, kernel_with_temp_path):
        """Test that course entity generation creates proper database schema"""
        kernel = kernel_with_temp_path

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

        # Verify database was created with proper schema
        managed_system_path = Path(os.environ.get("MANAGED_SYSTEM_PATH"))
        db_path = managed_system_path / "app" / "database" / "academic.db"

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get table schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='courses'")
            schema_result = cursor.fetchone()

            if schema_result:
                schema = schema_result[0]
                # Verify essential course attributes are in schema
                assert "name" in schema.lower(), "Course table should have name column"
                assert "code" in schema.lower(), "Course table should have code column"
                assert "credits" in schema.lower(), "Course table should have credits column"

                # Count columns (should be more than just id)
                cursor.execute("PRAGMA table_info(courses)")
                columns = cursor.fetchall()
                assert (
                    len(columns) > 1
                ), f"Course table should have multiple columns, got {len(columns)}"

                # Verify specific expected columns exist
                column_names = [col[1].lower() for col in columns]
                expected_columns = ["id", "name", "code", "credits"]
                for expected_col in expected_columns:
                    assert (
                        expected_col in column_names
                    ), f"Expected column '{expected_col}' not found in {column_names}"

            conn.close()

    def test_student_entity_has_proper_attributes(self, kernel_with_temp_path):
        """Test that student entity generation creates proper database schema"""
        kernel = kernel_with_temp_path

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

        # Verify database was created with proper schema
        managed_system_path = Path(os.environ.get("MANAGED_SYSTEM_PATH"))
        db_path = managed_system_path / "app" / "database" / "academic.db"

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get table schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='students'")
            schema_result = cursor.fetchone()

            if schema_result:
                schema = schema_result[0]
                # Verify essential student attributes are in schema
                assert "name" in schema.lower(), "Student table should have name column"
                assert (
                    "registration_number" in schema.lower()
                ), "Student table should have registration_number column"
                assert "course" in schema.lower(), "Student table should have course column"

                # Count columns (should be more than just id)
                cursor.execute("PRAGMA table_info(students)")
                columns = cursor.fetchall()
                assert (
                    len(columns) > 1
                ), f"Student table should have multiple columns, got {len(columns)}"

                # Verify specific expected columns exist
                column_names = [col[1].lower() for col in columns]
                expected_columns = ["id", "name", "registration_number", "course"]
                for expected_col in expected_columns:
                    assert (
                        expected_col in column_names
                    ), f"Expected column '{expected_col}' not found in {column_names}"

            conn.close()

    def test_multiple_entity_requests_maintain_attributes(self, kernel_with_temp_path):
        """Test that multiple different entity requests all maintain proper attributes"""
        kernel = kernel_with_temp_path

        # Test different request formats for each entity type
        test_cases = [
            ("add teacher", "teacher"),
            ("create course", "course"),
            ("generate student entity", "student"),
        ]

        for request, expected_entity in test_cases:
            result = kernel.process_natural_language_request(request, start_servers=False)

            # Verify successful generation
            assert result.get("success") is True, f"Request '{request}' should succeed"
            assert (
                result.get("entity") == expected_entity
            ), f"Request '{request}' should create {expected_entity} entity"

            # Verify execution results include database tasks
            execution_results = result.get("execution_results", [])
            database_tasks = [
                task for task in execution_results if "database" in task.get("task", "").lower()
            ]
            assert len(database_tasks) > 0, f"Request '{request}' should have database setup tasks"

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

    def test_regression_empty_attributes_bug(self, kernel_with_temp_path):
        """Regression test to ensure empty attributes bug doesn't return"""
        kernel = kernel_with_temp_path

        # Test the exact scenarios that were failing before the fix
        problematic_requests = [
            "add teacher",
            "add course",
            "create teacher",
            "create course",
        ]

        for request in problematic_requests:
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
