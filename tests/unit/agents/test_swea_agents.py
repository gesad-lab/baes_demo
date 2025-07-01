"""Tests for SWEA (Software Engineering Autonomous Agents)."""

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# Use centralized temp directory from conftest
TESTS_TEMP_DIR = Path(__file__).parent.parent / ".temp"


@pytest.fixture(autouse=True)
def setup_managed_system_path():
    """Set up MANAGED_SYSTEM_PATH for all SWEA tests to use tests/.temp"""
    # Ensure tests/.temp exists
    TESTS_TEMP_DIR.mkdir(exist_ok=True)
    # Create unique temp directory for this test session
    temp_dir = TESTS_TEMP_DIR / f"swea_test_{os.getpid()}"
    temp_dir.mkdir(exist_ok=True)
    # Set environment variable before any SWEA imports
    original_env = os.environ.get("MANAGED_SYSTEM_PATH")
    os.environ["MANAGED_SYSTEM_PATH"] = str(temp_dir / "managed_system")
    yield temp_dir
    # Restore environment
    if original_env:
        os.environ["MANAGED_SYSTEM_PATH"] = original_env
    else:
        os.environ.pop("MANAGED_SYSTEM_PATH", None)
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestBackendSWEA:
    """Test BackendSWEA functionality."""

    @patch("baes.swea_agents.backend_swea.OpenAIClient")
    def test_generate_model(self, mock_client_cls):
        """Test model generation."""
        from baes.swea_agents.backend_swea import BackendSWEA

        mock_client = mock_client_cls.return_value
        # Mock the LLM interpretation response to return valid JSON
        mock_client.generate_response.return_value = '{"attributes": ["name: str", "email: str"], "additional_requirements": [], "code_improvements": [], "modifications": [], "explanation": ""}'
        # Mock the code generation to return complete FastAPI code
        mock_client.generate_code_with_domain_focus.return_value = """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import sqlite3
class StudentBase(BaseModel):
    name: str
    email: str
class StudentCreate(StudentBase):
    pass
class StudentResponse(StudentBase):
    id: int
    class Config:
        from_attributes = True
router = APIRouter(prefix="/api", tags=["students"])
@router.post("/students/", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate):
    return {"id": 1, "name": student.name, "email": student.email}
@router.get("/students/", response_model=List[StudentResponse])
def list_students():
    return [{"id": 1, "name": "Test", "email": "test@example.com"}]
@router.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int):
    return {"id": id, "name": "Test", "email": "test@example.com"}
@router.put("/students/{id}", response_model=StudentResponse)
def update_student(id: int, student: StudentCreate):
    return {"id": id, "name": student.name, "email": student.email}
@router.delete("/students/{id}", status_code=204)
def delete_student(id: int):
    return None
"""
        swea = BackendSWEA()
        payload = {"entity": "Student", "attributes": ["name", "email"]}
        result = swea.handle_task("generate_model", payload)
        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]

    @patch("baes.swea_agents.backend_swea.OpenAIClient")
    def test_generate_api(self, mock_client_cls):
        """Test API generation."""
        from baes.swea_agents.backend_swea import BackendSWEA

        mock_client = mock_client_cls.return_value
        # Mock the LLM interpretation response to return valid JSON
        mock_client.generate_response.return_value = '{"attributes": ["name: str", "email: str"], "additional_requirements": [], "code_improvements": [], "modifications": [], "explanation": ""}'
        # Mock the code generation to return complete FastAPI code
        mock_client.generate_code_with_domain_focus.return_value = """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import sqlite3
class StudentBase(BaseModel):
    name: str
    email: str
class StudentCreate(StudentBase):
    pass
class StudentResponse(StudentBase):
    id: int
    class Config:
        from_attributes = True
router = APIRouter(prefix="/api", tags=["students"])
@router.post("/students/", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate):
    return {"id": 1, "name": student.name, "email": student.email}
@router.get("/students/", response_model=List[StudentResponse])
def list_students():
    return [{"id": 1, "name": "Test", "email": "test@example.com"}]
@router.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int):
    return {"id": id, "name": "Test", "email": "test@example.com"}
@router.put("/students/{id}", response_model=StudentResponse)
def update_student(id: int, student: StudentCreate):
    return {"id": id, "name": student.name, "email": student.email}
@router.delete("/students/{id}", status_code=204)
def delete_student(id: int):
    return None
"""
        swea = BackendSWEA()
        payload = {"entity": "Student", "attributes": ["name", "email"]}
        result = swea.handle_task("generate_api", payload)
        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]

    @patch("baes.swea_agents.backend_swea.OpenAIClient")
    def test_generate_api_with_invalid_entity(self, mock_client_cls):
        """Test that BackendSWEA properly handles invalid entity parameters."""
        from baes.swea_agents.backend_swea import BackendSWEA

        mock_client = mock_client_cls.return_value
        # Mock the LLM interpretation response to return valid JSON
        mock_client.generate_response.return_value = '{"attributes": ["name: str", "email: str"], "additional_requirements": [], "code_improvements": [], "modifications": [], "explanation": ""}'
        # Mock the code generation to return complete FastAPI code
        mock_client.generate_code_with_domain_focus.return_value = """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import sqlite3
class StudentBase(BaseModel):
    name: str
    email: str
class StudentCreate(StudentBase):
    pass
class StudentResponse(StudentBase):
    id: int
    class Config:
        from_attributes = True
router = APIRouter(prefix="/api", tags=["students"])
@router.post("/students/", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate):
    return {"id": 1, "name": student.name, "email": student.email}
@router.get("/students/", response_model=List[StudentResponse])
def list_students():
    return [{"id": 1, "name": "Test", "email": "test@example.com"}]
@router.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int):
    return {"id": id, "name": "Test", "email": "test@example.com"}
@router.put("/students/{id}", response_model=StudentResponse)
def update_student(id: int, student: StudentCreate):
    return {"id": id, "name": student.name, "email": student.email}
@router.delete("/students/{id}", status_code=204)
def delete_student(id: int):
    return None
"""
        swea = BackendSWEA()
        # Test with None entity
        payload = {"entity": None, "attributes": ["name", "email"]}
        result = swea.handle_task("generate_api", payload)
        assert result["success"] is False
        assert "Entity parameter cannot be None" in result["error"]
        # Test with non-string entity
        payload = {"entity": 123, "attributes": ["name", "email"]}
        result = swea.handle_task("generate_api", payload)
        assert result["success"] is False
        assert "Entity parameter must be a string" in result["error"]
        # Test with empty string entity
        payload = {"entity": "", "attributes": ["name", "email"]}
        result = swea.handle_task("generate_api", payload)
        assert result["success"] is False
        assert "Entity parameter cannot be empty" in result["error"]
        # Test with whitespace-only entity
        payload = {"entity": "   ", "attributes": ["name", "email"]}
        result = swea.handle_task("generate_api", payload)
        assert result["success"] is False
        assert "Entity parameter cannot be empty" in result["error"]
        # Test with valid entity (should work)
        payload = {"entity": "Student", "attributes": ["name", "email"]}
        result = swea.handle_task("generate_api", payload)
        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]

    def test_standards_based_generation_and_validation(self):
        """
        Test that BackendSWEA generates standards-compliant code that passes TechLeadSWEA validation.

        This test demonstrates the new standards-based approach that addresses the max_retries issue
        by ensuring perfect alignment between code generation and validation.
        """
        from baes.standards.backend_standards import BackendStandards
        from baes.swea_agents.backend_swea import BackendSWEA
        from baes.swea_agents.techlead_swea import TechLeadSWEA

        # Test direct template generation (no mocking issues)
        backend_swea = BackendSWEA()
        entity = "Student"
        attributes = ["name: str", "email: str", "age: int"]

        # Generate standards-compliant template code
        generated_code = backend_swea._generate_template_api_code(entity, attributes)

        # Verify template contains all required patterns
        standards = BackendStandards()

        # Check for required imports
        for import_name, import_statement in standards.REQUIRED_IMPORTS.items():
            if import_name == "context_manager":  # This might be on multiple lines
                assert "from contextlib import contextmanager" in generated_code
            else:
                assert (
                    import_statement in generated_code
                ), f"Missing required import: {import_statement}"

        # Check for database patterns (addressing main max_retries cause)
        db_patterns = standards.DATABASE_PATTERNS["required_patterns"]
        for pattern in db_patterns:
            assert pattern in generated_code, f"Missing required database pattern: {pattern}"

        # Check for proper HTTP status codes (critical TechLeadSWEA requirement)
        assert "status.HTTP_201_CREATED" in generated_code, "Missing 201 status code for POST"
        assert "status.HTTP_204_NO_CONTENT" in generated_code, "Missing 204 status code for DELETE"
        assert (
            "return Response(status_code=status.HTTP_204_NO_CONTENT)" in generated_code
        ), "Missing proper DELETE response"

        # Test direct standards validation
        validation_result = BackendStandards.get_backend_validation(generated_code, entity)

        # This should pass with the new standards-based approach
        assert (
            validation_result["is_valid"] is True
        ), f"Standards validation failed: {validation_result['issues']}"
        assert (
            validation_result["quality_score"] > 0.9
        ), f"Quality score should be high: {validation_result['quality_score']}"
        assert (
            len(validation_result["issues"]) == 0
        ), f"Should have no validation issues: {validation_result['issues']}"

        # Test TechLeadSWEA standards-based validation directly
        techlead_swea = TechLeadSWEA()
        techlead_validation = techlead_swea._validate_backend_with_standards(
            entity, generated_code, "generate_api"
        )

        # Verify TechLeadSWEA uses same standards and gets same result
        assert (
            techlead_validation["is_valid"] is True
        ), f"TechLeadSWEA validation failed: {techlead_validation['issues']}"
        assert (
            techlead_validation["quality_score"] > 0.9
        ), f"TechLeadSWEA quality score should be high: {techlead_validation['quality_score']}"

        # Verify both validation methods give consistent results (perfect alignment)
        assert (
            validation_result["is_valid"] == techlead_validation["is_valid"]
        ), "Validation results should be consistent"
        assert (
            abs(validation_result["quality_score"] - techlead_validation["quality_score"]) < 0.01
        ), "Quality scores should be very similar"

        # Verify critical patterns that were causing max_retries are present
        critical_patterns = [
            "@contextmanager",  # Database connection management
            "finally:",  # Resource cleanup
            "conn.close()",  # Connection closing
            "db.rollback()",  # Transaction rollback
            "status.HTTP_204_NO_CONTENT",  # Correct DELETE status
            "-> StudentResponse:",  # Return type hints
            "-> Response:",  # DELETE return type
        ]

        for pattern in critical_patterns:
            assert (
                pattern in generated_code
            ), f"Missing critical pattern that was causing max_retries: {pattern}"

        print("✅ Standards-based approach test passed:")
        print(f"  - Generated code length: {len(generated_code)} characters")
        print(f"  - Direct validation score: {validation_result['quality_score']:.2f}")
        print(f"  - TechLeadSWEA validation score: {techlead_validation['quality_score']:.2f}")
        print("  - Perfect alignment between BackendSWEA generation and TechLeadSWEA validation")
        print("  - All critical patterns present - max_retries issue should be resolved")

    def test_template_generation_fallback_without_llm(self):
        """
        Test that template generation works independently of LLM failures.

        This test verifies that when LLM fails, the standards-based template
        still produces valid, standards-compliant code.
        """
        from baes.standards.backend_standards import BackendStandards
        from baes.swea_agents.backend_swea import BackendSWEA

        # Don't mock OpenAI client - let it fail naturally to trigger template fallback
        backend_swea = BackendSWEA()

        # Test template generation directly (simulates LLM failure fallback)
        entity = "Student"
        attributes = ["name: str", "email: str", "age: int"]

        # Generate template code
        template_code = backend_swea._generate_template_api_code(entity, attributes)

        # Verify template code is standards-compliant
        validation_result = BackendStandards.get_backend_validation(template_code, entity)

        assert (
            validation_result["is_valid"] is True
        ), f"Template code should be standards-compliant. Issues: {validation_result['issues']}"
        assert validation_result["quality_score"] > 0.8, "Template quality should be high"
        assert (
            len(validation_result["issues"]) == 0
        ), f"Template should have no validation issues: {validation_result['issues']}"

        # Verify template contains all required patterns
        standards = BackendStandards()

        # Check for required imports
        for import_name, import_statement in standards.REQUIRED_IMPORTS.items():
            if import_name == "context_manager":  # This might be on multiple lines
                assert "from contextlib import contextmanager" in template_code
            else:
                assert (
                    import_statement in template_code
                ), f"Missing required import: {import_statement}"

        # Check critical patterns that were causing max_retries
        assert "@contextmanager" in template_code, "Template missing context manager decorator"
        assert "finally:" in template_code, "Template missing finally block"
        assert "conn.close()" in template_code, "Template missing connection closing"
        assert "db.rollback()" in template_code, "Template missing rollback in error handling"
        assert "status.HTTP_204_NO_CONTENT" in template_code, "Template missing 204 status code"
        assert (
            "return Response(status_code=status.HTTP_204_NO_CONTENT)" in template_code
        ), "Template missing proper DELETE response"

        print("✅ Template fallback test passed:")
        print(f"  - Template quality score: {validation_result['quality_score']:.2f}")
        print("  - All critical patterns present")
        print("  - Standards-compliant without LLM dependency")


@pytest.mark.unit
class TestDatabaseSWEA:
    """Test DatabaseSWEA functionality."""

    def test_setup_database(self):
        """Test database setup creates proper files under tests/.temp"""
        # Ensure tests/.temp exists
        TESTS_TEMP_DIR.mkdir(exist_ok=True)
        # Create unique temp directory for this test
        temp_dir = TESTS_TEMP_DIR / f"database_test_{os.getpid()}_{id(self)}"
        temp_dir.mkdir(exist_ok=True)
        try:
            from baes.swea_agents.database_swea import DatabaseSWEA

            swea = DatabaseSWEA()
            db_path = temp_dir / "baes_system.db"
            payload = {"database_path": str(db_path), "entity": "Student"}
            result = swea.handle_task("setup_database", payload)
            assert result["success"] is True
            # Note: actual file creation depends on implementation
        finally:
            # Cleanup
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestFrontendSWEA:
    """Test FrontendSWEA functionality."""

    @patch("baes.swea_agents.frontend_swea.OpenAIClient")
    def test_generate_ui(self, mock_client_cls):
        """Test UI generation."""
        from baes.swea_agents.frontend_swea import FrontendSWEA

        mock_client = mock_client_cls.return_value
        mock_client.generate_code_with_domain_focus.return_value = "import streamlit as st"
        swea = FrontendSWEA()
        payload = {"entity": "Student", "model_code": "class Student: pass"}
        result = swea.handle_task("generate_ui", payload)
        assert result["success"] is True
        # Check for code in the nested data structure
        assert "data" in result
        assert "code" in result["data"]
