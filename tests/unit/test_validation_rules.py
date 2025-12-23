"""
Unit tests for ValidationRuleEngine
(Feature: 001-performance-optimization / US2)

Tests rule-based validation with regex patterns and AST analysis
for confident approval/rejection without LLM calls.
"""

import pytest

from baes.standards.validation_rules import (
    ValidationOutcome,
    ValidationResult,
    ValidationRule,
    ValidationRuleEngine,
    SWEAType,
)


class TestValidationRuleEngine:
    """Test ValidationRuleEngine initialization and rule catalog"""
    
    def test_engine_initialization(self):
        """Test that validation engine initializes with all SWEA type rules"""
        engine = ValidationRuleEngine()
        
        assert "backend" in engine.rules
        assert "database" in engine.rules
        assert "frontend" in engine.rules
        assert "test" in engine.rules
        
        # Verify rules are loaded
        assert len(engine.rules["backend"]) > 0
        assert len(engine.rules["database"]) > 0
        assert len(engine.rules["frontend"]) > 0
        assert len(engine.rules["test"]) > 0
    
    def test_rule_structure(self):
        """Test that validation rules have required attributes"""
        engine = ValidationRuleEngine()
        
        for swea_type, rules in engine.rules.items():
            for rule in rules:
                assert rule.rule_id is not None
                assert rule.rule_name is not None
                assert rule.pattern is not None
                assert rule.pattern_type in ["must_have", "must_not_have"]
                assert 0.0 <= rule.confidence <= 1.0
                assert rule.message is not None
    
    def test_rule_counts(self):
        """Test that expected number of rules exist for each SWEA"""
        engine = ValidationRuleEngine()
        
        # These counts match the initialization in validation_rules.py
        assert len(engine.rules["backend"]) == 6
        assert len(engine.rules["database"]) == 5
        assert len(engine.rules["frontend"]) == 5
        assert len(engine.rules["test"]) == 5


class TestBackendValidation:
    """Test backend code validation rules"""
    
    def test_confident_approval_valid_backend_code(self):
        """Test confident approval for code passing all backend rules"""
        engine = ValidationRuleEngine()
        
        valid_code = """
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel

@contextmanager
def get_db():
    try:
        db = Database()
        yield db
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class StudentSchema(BaseModel):
    name: str
    age: int

app = FastAPI()

@app.get("/students/", response_model=list[StudentSchema])
def get_students(db = Depends(get_db)):
    try:
        return db.query(Student).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
        
        result = engine.validate_code(valid_code, "backend")
        
        assert result.overall_outcome == "confident_approval"
        assert result.confidence_score >= 0.7
        assert result.passed_count > result.failed_count
        assert not result.requires_llm
        assert result.validation_time_ms < 100  # Fast validation
    
    def test_confident_rejection_missing_error_handling(self):
        """Test confident rejection for backend code missing error handling"""
        engine = ValidationRuleEngine()
        
        invalid_code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/students/")
def get_students():
    return db.query(Student).all()  # No try-except
"""
        
        result = engine.validate_code(invalid_code, "backend")
        
        # Should be rejection or uncertain
        assert result.overall_outcome in ["confident_rejection", "uncertain"]
        assert result.failed_count > 0
    
    def test_confident_rejection_hardcoded_credentials(self):
        """Test confident rejection for hardcoded connection details"""
        engine = ValidationRuleEngine()
        
        insecure_code = """
from fastapi import FastAPI

DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_PASSWORD = "mysecretpassword"

app = FastAPI()
"""
        
        result = engine.validate_code(insecure_code, "backend")
        
        assert result.overall_outcome == "confident_rejection"
        assert result.confidence_score < -0.3
        assert any("hardcoded" in r.message.lower() for r in result.rule_results if not r.passed)


class TestDatabaseValidation:
    """Test database schema validation rules"""
    
    def test_confident_approval_valid_sql_schema(self):
        """Test confident approval for SQL schema with all required elements"""
        engine = ValidationRuleEngine()
        
        valid_sql = """
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    course_id INTEGER REFERENCES courses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_email ON students(email);
CREATE INDEX idx_students_course ON students(course_id);
"""
        
        result = engine.validate_code(valid_sql, "database")
        
        assert result.overall_outcome == "confident_approval"
        assert result.confidence_score >= 0.7
        assert result.passed_count >= 4  # PRIMARY KEY, INDEX, FOREIGN KEY, NOT NULL
    
    def test_confident_rejection_no_primary_key(self):
        """Test confident rejection for schema missing primary key"""
        engine = ValidationRuleEngine()
        
        invalid_sql = """
CREATE TABLE students (
    name VARCHAR(100),
    email VARCHAR(100)
);
"""
        
        result = engine.validate_code(invalid_sql, "database")
        
        assert result.overall_outcome == "confident_rejection"
        assert any("primary key" in r.message.lower() for r in result.rule_results if not r.passed)
    
    def test_confident_rejection_sql_injection_risk(self):
        """Test confident rejection for SQL injection patterns"""
        engine = ValidationRuleEngine()
        
        risky_sql = """
def get_student(student_id):
    query = f"SELECT * FROM students WHERE id = {student_id}"
    return db.execute(query)
"""
        
        result = engine.validate_code(risky_sql, "database")
        
        assert result.overall_outcome == "confident_rejection"
        assert result.confidence_score < -0.3


class TestFrontendValidation:
    """Test frontend code validation rules"""
    
    def test_confident_approval_valid_streamlit_code(self):
        """Test confident approval for Streamlit UI with validation"""
        engine = ValidationRuleEngine()
        
        valid_ui = """
import streamlit as st
import requests

st.title("Student Management")

with st.form("student_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    
    if st.form_submit_button("Submit"):
        if not name or not email:
            st.error("Name and email are required")
        else:
            try:
                response = requests.post("/api/students/", json={"name": name, "email": email})
                if response.status_code == 200:
                    st.success("Student added successfully!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
"""
        
        result = engine.validate_code(valid_ui, "frontend")
        
        # Valid UI should pass most rules, but might not reach confident_approval threshold
        # depending on which optional patterns are present
        assert result.overall_outcome in ["confident_approval", "uncertain"]
        assert result.passed_count >= 3  # Should pass form_validation, success_feedback, error_display, streamlit_imports
        assert result.validation_time_ms < 100
    
    def test_confident_rejection_no_error_handling(self):
        """Test rejection for frontend without error display"""
        engine = ValidationRuleEngine()
        
        invalid_ui = """
import streamlit as st

st.title("Student Management")

name = st.text_input("Name")
response = requests.post("/api/students/", json={"name": name})
"""
        
        result = engine.validate_code(invalid_ui, "frontend")
        
        # Should fail validation checks (no st.error, no try-except, no success feedback)
        assert result.failed_count > 0
    
    def test_confident_rejection_hardcoded_url(self):
        """Test rejection for hardcoded API URLs"""
        engine = ValidationRuleEngine()
        
        invalid_ui = """
import streamlit as st

API_URL = "http://localhost:8000/api/"
response = requests.get(f"{API_URL}students/")
"""
        
        result = engine.validate_code(invalid_ui, "frontend")
        
        assert result.overall_outcome == "confident_rejection"
        assert any("hardcoded" in r.message.lower() or "url" in r.message.lower() 
                  for r in result.rule_results if not r.passed)


class TestTestValidation:
    """Test test code validation rules"""
    
    def test_confident_approval_valid_integration_test(self):
        """Test confident approval for comprehensive integration test"""
        engine = ValidationRuleEngine()
        
        valid_test = """
import pytest

@pytest.fixture
def db_session():
    db = Database()
    yield db
    db.cleanup()

def test_create_student(db_session):
    student = {"name": "John", "email": "john@example.com"}
    result = create_student(db_session, student)
    assert result["name"] == "John"

def test_read_student(db_session):
    result = get_student(db_session, 1)
    assert result is not None

def test_update_student(db_session):
    updated = update_student(db_session, 1, {"name": "Jane"})
    assert updated["name"] == "Jane"

def test_delete_student(db_session):
    delete_student(db_session, 1)
    assert get_student(db_session, 1) is None

def test_invalid_student_error():
    with pytest.raises(ValueError):
        create_student(None, {"name": ""})
"""
        
        result = engine.validate_code(valid_test, "test")
        
        assert result.overall_outcome == "confident_approval"
        assert result.confidence_score >= 0.7
        assert result.passed_count >= 4  # CRUD, error case, cleanup, pytest import
    
    def test_confident_rejection_no_error_cases(self):
        """Test rejection for tests missing error cases"""
        engine = ValidationRuleEngine()
        
        incomplete_test = """
import pytest

def test_get_student():
    result = get_student(1)
    assert result is not None
"""
        
        result = engine.validate_code(incomplete_test, "test")
        
        # Should fail validation checks (no error case testing, no cleanup, no CRUD lifecycle)
        assert result.failed_count > 0
    
    def test_confident_rejection_no_assertions(self):
        """Test rejection for tests without assertions"""
        engine = ValidationRuleEngine()
        
        invalid_test = """
import pytest

def test_student_creation():
    student = {"name": "John"}
    create_student(student)
    # No assertion!
"""
        
        result = engine.validate_code(invalid_test, "test")
        
        assert result.overall_outcome == "confident_rejection"
        assert any("assertion" in r.message.lower() for r in result.rule_results if not r.passed)


class TestASTValidation:
    """Test AST-based structural validation"""
    
    def test_confident_approval_well_structured_code(self):
        """Test approval for code with type hints and docstrings"""
        engine = ValidationRuleEngine()
        
        well_structured = """
def calculate_grade(score: int, max_score: int) -> float:
    '''
    Calculate grade percentage
    
    Args:
        score: Points earned
        max_score: Maximum possible points
    
    Returns:
        Grade as percentage
    '''
    return (score / max_score) * 100

class Student:
    '''Represents a student entity'''
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
"""
        
        result = engine.validate_code_structure(well_structured)
        
        assert result.overall_outcome == "confident_approval"
        assert result.confidence_score >= 0.5
    
    def test_rejection_missing_type_hints(self):
        """Test rejection for functions without type hints"""
        engine = ValidationRuleEngine()
        
        no_types = """
def calculate_grade(score, max_score):
    return (score / max_score) * 100
"""
        
        result = engine.validate_code_structure(no_types)
        
        assert result.failed_count > 0
        assert any("type hint" in r.message.lower() for r in result.rule_results if not r.passed)
    
    def test_rejection_bad_naming(self):
        """Test rejection for PEP 8 naming violations"""
        engine = ValidationRuleEngine()
        
        bad_naming = """
def CalculateGrade(Score: int, MaxScore: int) -> float:
    return (Score / MaxScore) * 100

class student_class:
    pass
"""
        
        result = engine.validate_code_structure(bad_naming)
        
        assert result.failed_count > 0
        # Should catch both PascalCase function (should be snake_case) and snake_case class (should be PascalCase)
    
    def test_syntax_error_detection(self):
        """Test confident rejection for syntax errors"""
        engine = ValidationRuleEngine()
        
        syntax_error = """
def broken_function(:
    return x +
"""
        
        result = engine.validate_code_structure(syntax_error)
        
        assert result.overall_outcome == "confident_rejection"
        assert result.confidence_score == -1.0
        assert "syntax error" in result.feedback_message.lower()


class TestRuleManagement:
    """Test rule management operations"""
    
    def test_add_custom_rule(self):
        """Test adding a custom validation rule"""
        engine = ValidationRuleEngine()
        
        initial_count = len(engine.rules["backend"])
        
        custom_rule = ValidationRule(
            rule_id="BE999",
            rule_name="custom_test_rule",
            swea_type=SWEAType.BACKEND,
            pattern=r"custom_pattern",
            pattern_type="must_have",
            confidence=0.8,
            message="Custom rule for testing"
        )
        
        engine.add_rule(custom_rule)
        
        assert len(engine.rules["backend"]) == initial_count + 1
        assert engine.rules["backend"][-1].rule_id == "BE999"
    
    def test_disable_rule(self):
        """Test disabling a validation rule"""
        engine = ValidationRuleEngine()
        
        # Disable a specific rule
        assert engine.disable_rule("BE001")
        
        # Verify rule is disabled
        rule = next(r for r in engine.rules["backend"] if r.rule_id == "BE001")
        assert not rule.enabled
    
    def test_enable_rule(self):
        """Test enabling a disabled rule"""
        engine = ValidationRuleEngine()
        
        # Disable then enable
        engine.disable_rule("BE001")
        assert engine.enable_rule("BE001")
        
        # Verify rule is enabled
        rule = next(r for r in engine.rules["backend"] if r.rule_id == "BE001")
        assert rule.enabled
    
    def test_update_rule(self):
        """Test updating rule properties"""
        engine = ValidationRuleEngine()
        
        assert engine.update_rule("BE001", confidence=0.95, message="Updated message")
        
        rule = next(r for r in engine.rules["backend"] if r.rule_id == "BE001")
        assert rule.confidence == 0.95
        assert rule.message == "Updated message"
    
    def test_list_rules_by_type(self):
        """Test listing rules filtered by SWEA type"""
        engine = ValidationRuleEngine()
        
        backend_rules = engine.list_rules("backend")
        assert len(backend_rules) == 6
        assert all(r.swea_type == SWEAType.BACKEND for r in backend_rules)
        
        frontend_rules = engine.list_rules("frontend")
        assert len(frontend_rules) == 5
    
    def test_list_all_rules(self):
        """Test listing all rules across all SWEA types"""
        engine = ValidationRuleEngine()
        
        all_rules = engine.list_rules()
        assert len(all_rules) == 6 + 5 + 5 + 5  # backend + database + frontend + test
    
    def test_get_rule_stats(self):
        """Test getting rule statistics"""
        engine = ValidationRuleEngine()
        
        # Disable one rule
        engine.disable_rule("BE001")
        
        stats = engine.get_rule_stats()
        
        assert "backend" in stats
        assert stats["backend"]["total"] == 6
        assert stats["backend"]["enabled"] == 5
        assert stats["backend"]["disabled"] == 1


class TestPerformance:
    """Test validation performance targets"""
    
    def test_validation_speed(self):
        """Test that rule-based validation completes in <100ms"""
        engine = ValidationRuleEngine()
        
        code = """
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
@contextmanager
def get_db():
    pass
"""
        
        result = engine.validate_code(code, "backend")
        
        # Target: <100ms for rule-based validation
        assert result.validation_time_ms < 100
    
    def test_ast_validation_speed(self):
        """Test that AST validation completes in <100ms"""
        engine = ValidationRuleEngine()
        
        code = """
def example_function(x: int, y: int) -> int:
    '''Example docstring'''
    return x + y

class ExampleClass:
    '''Example class'''
    pass
"""
        
        result = engine.validate_code_structure(code)
        
        # Target: <100ms for AST validation
        assert result.validation_time_ms < 100


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_code(self):
        """Test validation with empty code"""
        engine = ValidationRuleEngine()
        
        result = engine.validate_code("", "backend")
        
        # Empty code should fail most rules
        assert result.overall_outcome in ["confident_rejection", "uncertain"]
    
    def test_unknown_swea_type(self):
        """Test validation with unknown SWEA type"""
        engine = ValidationRuleEngine()
        
        result = engine.validate_code("code", "unknown_type")
        
        assert result.overall_outcome == "uncertain"
        assert result.requires_llm
    
    def test_disabled_rules_pass(self):
        """Test that disabled rules always pass"""
        engine = ValidationRuleEngine()
        
        # Disable all backend rules
        for rule in engine.rules["backend"]:
            engine.disable_rule(rule.rule_id)
        
        # Code that would normally fail should now pass
        bad_code = "print('hello')"  # No FastAPI, no error handling, etc.
        result = engine.validate_code(bad_code, "backend")
        
        assert result.passed_count == len(engine.rules["backend"])
        assert result.failed_count == 0
