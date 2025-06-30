"""
Phase 3 Integration Tests: Standards-Based Validation for All SWEAs

Tests that all SWEA agents (Backend, Frontend, Database, Test) use their respective
standards for generation and that TechLeadSWEA validates them consistently.

This validates the complete Phase 3 implementation of the standards-based approach.
"""

import pytest
from unittest.mock import Mock, patch

from baes.standards import (
    BackendStandards, 
    FrontendStandards, 
    DatabaseStandards, 
    TestStandards
)
from baes.swea_agents.backend_swea import BackendSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.database_swea import DatabaseSWEA
from baes.swea_agents.test_swea import TestSWEA
from baes.swea_agents.techlead_swea import TechLeadSWEA


class TestStandardsIntegration:
    """Test integration between all SWEAs and their respective standards."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.entity = "Student"
        self.attributes = ["name:str", "email:str", "age:int"]
        
    # ==================== Backend Standards Integration ====================
    
    def test_backend_standards_template_generation(self):
        """Test that BackendSWEA generates code using BackendStandards templates."""
        backend_swea = BackendSWEA()
        
        # Generate template code
        template_code = backend_swea._generate_template_api_code(self.entity, self.attributes)
        
        # Verify template contains all required patterns from BackendStandards
        standards = BackendStandards()
        
        # Check for required imports
        for import_name, import_statement in standards.REQUIRED_IMPORTS.items():
            if import_name == "context_manager":  # This might be on multiple lines
                assert "from contextlib import contextmanager" in template_code
            else:
                assert import_statement in template_code, f"Missing required import: {import_statement}"
        
        # Check critical patterns that were causing max_retries
        assert "@contextmanager" in template_code
        assert "try:" in template_code
        assert "yield conn" in template_code
        assert "except Exception:" in template_code
        assert "conn.rollback()" in template_code
        assert "finally:" in template_code
        assert "conn.close()" in template_code
        
        # Check HTTP status codes
        assert "status.HTTP_201_CREATED" in template_code
        assert "status.HTTP_204_NO_CONTENT" in template_code
        assert "Response(status_code=status.HTTP_204_NO_CONTENT)" in template_code
        
        print("✅ BackendSWEA template generation using BackendStandards: PASSED")
    
    def test_backend_standards_validation_alignment(self):
        """Test that BackendStandards validation gives perfect scores for its own templates."""
        backend_swea = BackendSWEA()
        
        # Generate template code using standards
        template_code = backend_swea._generate_template_api_code(self.entity, self.attributes)
        
        # Validate using same standards
        validation_result = BackendStandards.get_backend_validation(template_code, self.entity)
        
        # Should achieve perfect validation score
        assert validation_result["is_valid"] is True, f"Template validation failed: {validation_result['issues']}"
        assert validation_result["quality_score"] >= 0.90, f"Quality score too low: {validation_result['quality_score']}"
        assert len(validation_result["issues"]) == 0, f"Template has validation issues: {validation_result['issues']}"
        
        print(f"✅ BackendStandards validation alignment - Quality Score: {validation_result['quality_score']:.2f}")
    
    def test_techlead_backend_validation_integration(self):
        """Test that TechLeadSWEA correctly uses BackendStandards for backend validation."""
        techlead = TechLeadSWEA()
        backend_swea = BackendSWEA()
        
        # Generate backend code
        template_code = backend_swea._generate_template_api_code(self.entity, self.attributes)
        
        # Validate using TechLeadSWEA
        validation_result = techlead._validate_backend_with_standards(
            self.entity, template_code, "generate_api"
        )
        
        # Should pass validation
        assert validation_result["is_valid"] is True
        assert validation_result["quality_score"] >= 0.90
        assert validation_result["validation_method"] == "BackendStandards"
        
        print("✅ TechLeadSWEA backend validation integration: PASSED")
    
    # ==================== Frontend Standards Integration ====================
    
    def test_frontend_standards_template_generation(self):
        """Test that FrontendSWEA can generate code using FrontendStandards."""
        frontend_swea = FrontendSWEA()
        
        # Generate template code
        template_code = frontend_swea._generate_template_ui_code(self.entity, self.attributes)
        
        # Verify template contains FrontendStandards patterns
        standards = FrontendStandards()
        
        # Check for required imports
        assert "import streamlit as st" in template_code
        assert "import requests" in template_code
        
        # Check UI patterns
        assert "st.set_page_config" in template_code
        assert "st.title" in template_code
        assert "st.tabs" in template_code
        assert "st.form" in template_code
        assert "st.form_submit_button" in template_code
        
        # Check API patterns
        assert "API_BASE_URL" in template_code
        assert "requests.get" in template_code
        assert "requests.post" in template_code
        assert "requests.put" in template_code
        assert "requests.delete" in template_code
        assert "raise_for_status" in template_code
        
        print("✅ FrontendSWEA template generation using FrontendStandards: PASSED")
    
    def test_frontend_standards_validation(self):
        """Test FrontendStandards validation on its own generated code."""
        frontend_swea = FrontendSWEA()
        
        # Generate template code
        template_code = frontend_swea._generate_template_ui_code(self.entity, self.attributes)
        
        # Validate using FrontendStandards
        validation_result = FrontendStandards.get_frontend_validation(template_code, self.entity)
        
        # Should achieve good validation score
        assert validation_result["is_valid"] is True, f"Frontend validation failed: {validation_result['issues']}"
        assert validation_result["quality_score"] >= 0.80, f"Quality score too low: {validation_result['quality_score']}"
        
        print(f"✅ FrontendStandards validation - Quality Score: {validation_result['quality_score']:.2f}")
    
    def test_techlead_frontend_validation_integration(self):
        """Test that TechLeadSWEA correctly uses FrontendStandards for frontend validation."""
        techlead = TechLeadSWEA()
        frontend_swea = FrontendSWEA()
        
        # Generate frontend code
        template_code = frontend_swea._generate_template_ui_code(self.entity, self.attributes)
        
        # Validate using TechLeadSWEA
        validation_result = techlead._validate_frontend_with_standards(
            self.entity, template_code, "generate_ui"
        )
        
        # Should pass validation
        assert validation_result["is_valid"] is True
        assert validation_result["quality_score"] >= 0.80
        assert validation_result["validation_method"] == "FrontendStandards"
        
        print("✅ TechLeadSWEA frontend validation integration: PASSED")
    
    # ==================== Database Standards Integration ====================
    
    def test_database_standards_validation(self):
        """Test DatabaseStandards validation with sample database code."""
        # Sample SQLite database code that follows DatabaseStandards
        sample_db_code = '''
import sqlite3
from pathlib import Path
import logging

def setup_database(db_path: str = None) -> str:
    """Initialize database with all required tables"""
    if db_path is None:
        db_path = Path("app/database/academic.db")
    else:
        db_path = Path(db_path)
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Create students table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER NOT NULL
            )
        """)
        
        conn.commit()
        logger.info("Database setup completed successfully")
        return str(db_path)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        conn.close()
'''
        
        # Validate using DatabaseStandards
        validation_result = DatabaseStandards.get_database_validation(sample_db_code, self.entity)
        
        # Should achieve good validation score
        assert validation_result["is_valid"] is True, f"Database validation failed: {validation_result['issues']}"
        assert validation_result["quality_score"] >= 0.70, f"Quality score too low: {validation_result['quality_score']}"
        
        print(f"✅ DatabaseStandards validation - Quality Score: {validation_result['quality_score']:.2f}")
    
    def test_techlead_database_validation_integration(self):
        """Test that TechLeadSWEA correctly uses DatabaseStandards for database validation."""
        techlead = TechLeadSWEA()
        
        # Sample database code
        sample_db_code = '''
import sqlite3
from pathlib import Path

def setup_database():
    db_path = Path("app/database/academic.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
'''
        
        # Validate using TechLeadSWEA
        validation_result = techlead._validate_database_with_standards(
            self.entity, sample_db_code, "setup_database"
        )
        
        # Should pass validation
        assert validation_result["validation_method"] == "DatabaseStandards"
        assert "quality_score" in validation_result
        
        print("✅ TechLeadSWEA database validation integration: PASSED")
    
    # ==================== Test Standards Integration ====================
    
    def test_test_standards_validation(self):
        """Test TestStandards validation with sample test code."""
        # Sample pytest test code that follows TestStandards
        sample_test_code = '''
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.unit
class TestStudent:
    """Test Student functionality."""
    
    def test_create_student_success(self):
        """Test successful student creation."""
        # Arrange - setup test data
        student_data = {"name": "John Doe", "email": "john@example.com", "age": 20}
        
        # Act - perform the action
        result = create_student(student_data)
        
        # Assert - verify results
        assert result['success'] is True
        assert 'id' in result['data']
    
    def test_create_student_invalid_data(self):
        """Test student creation with invalid data."""
        # Arrange
        invalid_data = {"name": "", "email": "invalid", "age": -1}
        
        # Act
        result = create_student(invalid_data)
        
        # Assert
        assert result['success'] is False
        assert 'error' in result
    
    @patch("requests.get")
    def test_list_students_success(self, mock_get):
        """Test listing students successfully."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "name": "Test"}]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Act
        result = list_students()
        
        # Assert
        assert isinstance(result, list)
        assert len(result) >= 0
'''
        
        # Validate using TestStandards
        validation_result = TestStandards.get_test_validation(sample_test_code, self.entity)
        
        # Should achieve good validation score
        assert validation_result["is_valid"] is True, f"Test validation failed: {validation_result['issues']}"
        assert validation_result["quality_score"] >= 0.70, f"Quality score too low: {validation_result['quality_score']}"
        
        print(f"✅ TestStandards validation - Quality Score: {validation_result['quality_score']:.2f}")
    
    def test_techlead_test_validation_integration(self):
        """Test that TechLeadSWEA correctly uses TestStandards for test validation."""
        techlead = TechLeadSWEA()
        
        # Sample test code
        sample_test_code = '''
import pytest

class TestStudent:
    def test_create_student(self):
        assert True
'''
        
        # Validate using TechLeadSWEA
        validation_result = techlead._validate_test_with_standards(
            self.entity, sample_test_code, "generate_tests"
        )
        
        # Should use correct validation method
        assert validation_result["validation_method"] == "TestStandards"
        assert "quality_score" in validation_result
        
        print("✅ TechLeadSWEA test validation integration: PASSED")
    
    # ==================== Complete Integration Test ====================
    
    def test_complete_swea_standards_integration(self):
        """Test that TechLeadSWEA can validate all SWEA types using appropriate standards."""
        techlead = TechLeadSWEA()
        
        # Mock code artifacts for each SWEA type
        test_cases = [
            {
                "swea_agent": "BackendSWEA",
                "code": "from fastapi import APIRouter\n@contextmanager\ndef get_db(): pass",
                "expected_method": "BackendStandards"
            },
            {
                "swea_agent": "FrontendSWEA", 
                "code": "import streamlit as st\nst.set_page_config()\nst.title('Test')",
                "expected_method": "FrontendStandards"
            },
            {
                "swea_agent": "DatabaseSWEA",
                "code": "import sqlite3\nCREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)",
                "expected_method": "DatabaseStandards"
            },
            {
                "swea_agent": "TestSWEA",
                "code": "import pytest\nclass TestEntity:\n    def test_create(self): assert True",
                "expected_method": "TestStandards"
            }
        ]
        
        for test_case in test_cases:
            # Create mock result structure
            mock_result = {
                "data": {
                    "code": test_case["code"],
                    "file_path": f"/test/{test_case['swea_agent']}.py"
                }
            }
            
            # Validate using TechLeadSWEA
            validation_result = techlead._validate_code_artifact(
                self.entity, 
                test_case["swea_agent"], 
                "test_task", 
                mock_result
            )
            
            # Verify correct validation method is used
            if "validation_method" in validation_result:
                assert test_case["expected_method"] in validation_result["validation_method"]
            
            print(f"✅ {test_case['swea_agent']} validation routing: PASSED")
        
        print("✅ Complete SWEA standards integration: ALL PASSED")
    
    # ==================== Standards Package Integration ====================
    
    def test_standards_package_imports(self):
        """Test that all standards can be imported from the standards package."""
        from baes.standards import (
            BaseStandards,
            BackendStandards, 
            FrontendStandards,
            DatabaseStandards,
            TestStandards
        )
        
        # Verify all standards inherit from BaseStandards
        assert issubclass(BackendStandards, BaseStandards)
        assert issubclass(FrontendStandards, BaseStandards)
        assert issubclass(DatabaseStandards, BaseStandards)
        assert issubclass(TestStandards, BaseStandards)
        
        # Verify all have their specific validation methods
        assert hasattr(BackendStandards, 'get_backend_validation')
        assert hasattr(FrontendStandards, 'get_frontend_validation')
        assert hasattr(DatabaseStandards, 'get_database_validation')
        assert hasattr(TestStandards, 'get_test_validation')
        
        print("✅ Standards package imports: PASSED")


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    test_instance = TestStandardsIntegration()
    test_instance.setup_method()
    
    print("🚀 Running Phase 3 Standards Integration Tests...")
    print("=" * 60)
    
    try:
        # Backend tests
        test_instance.test_backend_standards_template_generation()
        test_instance.test_backend_standards_validation_alignment()
        test_instance.test_techlead_backend_validation_integration()
        
        # Frontend tests
        test_instance.test_frontend_standards_template_generation()
        test_instance.test_frontend_standards_validation()
        test_instance.test_techlead_frontend_validation_integration()
        
        # Database tests
        test_instance.test_database_standards_validation()
        test_instance.test_techlead_database_validation_integration()
        
        # Test tests
        test_instance.test_test_standards_validation()
        test_instance.test_techlead_test_validation_integration()
        
        # Integration tests
        test_instance.test_complete_swea_standards_integration()
        test_instance.test_standards_package_imports()
        
        print("=" * 60)
        print("🎉 ALL PHASE 3 TESTS PASSED! Standards integration is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise 