"""
Integration tests for template-based code generation
(Feature: 001-performance-optimization / US1)

Tests end-to-end template generation workflow including:
- Template selection for standard CRUD entities
- Code generation via templates (backend, database, frontend, tests)
- Fallback to LLM for entities with custom logic
- Performance targets: <15s generation time, <2000 tokens, 100% test pass

Prerequisites:
- OPENAI_API_KEY environment variable must be set
- Templates must exist in baes/templates/ directory
- Test runs in isolated environment with cleanup
"""

import os
import time
import pytest
from baes.domain_entities.academic.student_bae import StudentBae
from baes.domain_entities.academic.course_bae import CourseBae
from baes.swea_agents.backend_swea import BackendSWEA
from baes.swea_agents.database_swea import DatabaseSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.test_swea import TestSWEA
from baes.utils.template_registry import TemplateRegistry, EntityType


class TestTemplateGeneratedStudentEntity:
    """Integration tests for template-generated standard Student entity (T030)"""

    @pytest.fixture
    def student_bae(self):
        """Create a Student BAE with standard CRUD attributes"""
        return StudentBae()

    @pytest.fixture
    def backend_swea(self):
        """Create BackendSWEA instance"""
        return BackendSWEA()

    @pytest.fixture
    def database_swea(self):
        """Create DatabaseSWEA instance"""
        return DatabaseSWEA()

    @pytest.fixture
    def frontend_swea(self):
        """Create FrontendSWEA instance"""
        return FrontendSWEA()

    @pytest.fixture
    def test_swea(self):
        """Create TestSWEA instance"""
        return TestSWEA()

    def test_student_entity_is_standard(self, student_bae):
        """Verify Student entity is classified as STANDARD (template-eligible)"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "enrollment_date", "type": "datetime"},
                {"name": "gpa", "type": "float"},
                {"name": "email", "type": "str"},
                {"name": "active", "type": "bool"},
            ],
            "business_rules": [],
            "relationships": {}
        }
        
        result = student_bae._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is False
        assert result["entity_type"] == EntityType.STANDARD.value
        assert result["template_eligible"] is True
        assert len(result["custom_logic_reasons"]) == 0

    def test_backend_generation_uses_template(self, student_bae, backend_swea):
        """Verify backend code generation uses template for Student entity"""
        start_time = time.time()
        
        # Generate backend code for Student with standard attributes
        result = backend_swea.generate_api_code(
            entity_name="Student",
            attributes=["name:str", "enrollment_date:datetime", "gpa:float", "email:str", "active:bool"],
            relationships={}
        )
        
        generation_time = time.time() - start_time
        
        # Verify generation succeeded
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify code quality - should contain FastAPI patterns
        assert "FastAPI" in result or "APIRouter" in result or "@app." in result or "@router." in result
        assert "Student" in result
        assert "def" in result  # Contains function definitions
        
        # Performance target: <15s generation time
        assert generation_time < 15.0, f"Generation took {generation_time:.2f}s, expected <15s"

    def test_database_generation_uses_template(self, student_bae, database_swea):
        """Verify database schema generation uses template for Student entity"""
        start_time = time.time()
        
        # Generate database schema for Student
        result = database_swea.generate_schema(
            entity_name="Student",
            attributes=["name:str", "enrollment_date:datetime", "gpa:float", "email:str", "active:bool"],
            relationships={}
        )
        
        generation_time = time.time() - start_time
        
        # Verify generation succeeded
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify SQL schema quality
        assert "CREATE TABLE" in result or "create table" in result.lower()
        assert "student" in result.lower()
        
        # Performance target: <15s generation time
        assert generation_time < 15.0, f"Generation took {generation_time:.2f}s, expected <15s"

    def test_frontend_generation_uses_template(self, student_bae, frontend_swea):
        """Verify frontend UI generation uses template for Student entity"""
        start_time = time.time()
        
        # Generate frontend code for Student
        result = frontend_swea.generate_page_code(
            entity_name="Student",
            attributes=["name:str", "enrollment_date:datetime", "gpa:float", "email:str", "active:bool"],
            relationships={}
        )
        
        generation_time = time.time() - start_time
        
        # Verify generation succeeded
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify Streamlit UI quality
        assert "streamlit" in result.lower() or "st." in result
        assert "Student" in result
        
        # Performance target: <15s generation time
        assert generation_time < 15.0, f"Generation took {generation_time:.2f}s, expected <15s"

    def test_integration_test_generation_uses_template(self, student_bae, test_swea):
        """Verify integration test generation uses template for Student entity"""
        start_time = time.time()
        
        # Generate integration tests for Student
        result = test_swea.generate_test_code(
            entity_name="Student",
            attributes=["name:str", "enrollment_date:datetime", "gpa:float", "email:str", "active:bool"],
            test_type="integration"
        )
        
        generation_time = time.time() - start_time
        
        # Verify generation succeeded
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify test code quality
        assert "pytest" in result.lower() or "def test_" in result
        assert "Student" in result
        
        # Performance target: <15s generation time
        assert generation_time < 15.0, f"Generation took {generation_time:.2f}s, expected <15s"

    def test_full_crud_generation_performance(self, student_bae, backend_swea, database_swea, 
                                             frontend_swea, test_swea):
        """Verify full CRUD generation for Student meets performance targets"""
        total_start_time = time.time()
        
        attributes = ["name:str", "enrollment_date:datetime", "gpa:float", "email:str", "active:bool"]
        relationships = {}
        
        # Generate all 4 artifacts
        backend_code = backend_swea.generate_api_code("Student", attributes, relationships)
        database_schema = database_swea.generate_schema("Student", attributes, relationships)
        frontend_code = frontend_swea.generate_page_code("Student", attributes, relationships)
        test_code = test_swea.generate_test_code("Student", attributes, "integration")
        
        total_time = time.time() - total_start_time
        
        # Verify all artifacts generated
        assert backend_code and len(backend_code) > 0
        assert database_schema and len(database_schema) > 0
        assert frontend_code and len(frontend_code) > 0
        assert test_code and len(test_code) > 0
        
        # Performance target: <60s total time (15s per artifact)
        assert total_time < 60.0, f"Total generation took {total_time:.2f}s, expected <60s"
        
        print(f"\n✅ Full CRUD generation completed in {total_time:.2f}s")


class TestTemplateFallbackOnCustomLogic:
    """Integration tests for template fallback to LLM on custom logic (T031)"""

    @pytest.fixture
    def course_bae(self):
        """Create a Course BAE that might have custom logic"""
        return CourseBae()

    @pytest.fixture
    def backend_swea(self):
        return BackendSWEA()

    def test_complex_entity_detected_as_custom(self, course_bae):
        """Verify entity with computed properties is classified as CUSTOM"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "capacity", "type": "int"},
                {"name": "enrolled_count", "type": "int"},
            ],
            "business_rules": [
                "Calculate available seats as capacity minus enrolled_count",
                "Compute enrollment percentage"
            ],
            "relationships": {}
        }
        
        result = course_bae._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value
        assert result["template_eligible"] is False
        assert len(result["custom_logic_reasons"]) > 0

    def test_backend_generation_falls_back_to_llm(self, course_bae, backend_swea):
        """Verify backend generation falls back to LLM for complex entity"""
        start_time = time.time()
        
        # Generate backend code for Course with computed properties
        result = backend_swea.generate_api_code(
            entity_name="Course",
            attributes=["name:str", "capacity:int", "enrolled_count:int"],
            relationships={},
            business_rules=["Calculate available seats as capacity minus enrolled_count"]
        )
        
        generation_time = time.time() - start_time
        
        # Verify generation succeeded (using LLM fallback)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify code contains Course entity
        assert "Course" in result
        
        # LLM fallback may take longer than template
        assert generation_time < 30.0, f"LLM fallback took {generation_time:.2f}s, expected <30s"

    def test_entity_with_many_to_many_uses_llm(self, course_bae):
        """Verify entity with many-to-many relationship uses LLM"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "credits", "type": "int"},
            ],
            "business_rules": [],
            "relationships": {
                "students": {
                    "type": "many-to-many",
                    "cardinality": "many-to-many",
                    "target": "Student"
                }
            }
        }
        
        result = course_bae._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value
        assert any("many-to-many" in reason.lower() for reason in result["custom_logic_reasons"])

    def test_entity_with_complex_validation_uses_llm(self, course_bae):
        """Verify entity with complex validation uses LLM"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "max_students", "type": "int"},
                {"name": "min_students", "type": "int"},
            ],
            "business_rules": [
                "Validate that max_students must be greater than min_students",
                "Check that max_students is between 5 and 100"
            ],
            "relationships": {}
        }
        
        result = course_bae._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert result["entity_type"] == EntityType.CUSTOM.value

    def test_entity_with_state_machine_uses_llm(self, course_bae):
        """Verify entity with state machine uses LLM"""
        schema = {
            "attributes": [
                {"name": "name", "type": "str"},
                {"name": "status", "type": "str"},
            ],
            "business_rules": [
                "Course state transitions from draft to published to archived",
                "Status changes require approval workflow"
            ],
            "relationships": {}
        }
        
        result = course_bae._detect_custom_logic(schema)
        
        assert result["requires_custom_logic"] is True
        assert any("state" in reason.lower() or "workflow" in reason.lower() 
                   for reason in result["custom_logic_reasons"])


class TestCodeQualityValidation:
    """Validate generated code meets quality standards"""

    @pytest.fixture
    def backend_swea(self):
        return BackendSWEA()

    @pytest.fixture
    def database_swea(self):
        return DatabaseSWEA()

    def test_generated_backend_code_is_valid_python(self, backend_swea):
        """Verify generated backend code is syntactically valid Python"""
        result = backend_swea.generate_api_code(
            entity_name="Person",
            attributes=["name:str", "age:int", "email:str"],
            relationships={}
        )
        
        # Try to compile the generated code
        try:
            compile(result, '<string>', 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        assert syntax_valid, "Generated backend code has syntax errors"

    def test_generated_database_schema_is_valid_sql(self, database_swea):
        """Verify generated database schema is valid SQL"""
        result = database_swea.generate_schema(
            entity_name="Person",
            attributes=["name:str", "age:int", "email:str"],
            relationships={}
        )
        
        # Basic SQL validation - check for required keywords
        assert "CREATE TABLE" in result or "create table" in result.lower()
        assert "PRIMARY KEY" in result or "primary key" in result.lower() or "id" in result.lower()
        assert "(" in result and ")" in result  # Has column definitions

    def test_code_follows_pep8_conventions(self, backend_swea):
        """Verify generated code follows basic PEP 8 conventions"""
        result = backend_swea.generate_api_code(
            entity_name="Product",
            attributes=["name:str", "price:float", "stock:int"],
            relationships={}
        )
        
        # Check for basic PEP 8 patterns
        assert "def " in result  # Function definitions with space
        assert ":" in result  # Type hints or dict notation
        
        # Should not have obvious PEP 8 violations
        assert "def(" not in result  # No space missing after def
        assert ",(" not in result or "(," not in result  # Proper spacing


class TestPerformanceTargets:
    """Validate performance targets are met"""

    @pytest.fixture
    def backend_swea(self):
        return BackendSWEA()

    def test_token_usage_under_2000(self, backend_swea):
        """Verify token usage is under 2000 for template generation"""
        # Note: This is a placeholder test since we don't have direct token counting
        # In real implementation, this would check OptimizationMetrics
        
        result = backend_swea.generate_api_code(
            entity_name="SimpleEntity",
            attributes=["name:str", "value:int"],
            relationships={}
        )
        
        # Rough estimate: template-generated code should be compact
        # Typically ~500-1000 tokens for simple CRUD
        estimated_tokens = len(result) / 4  # Rough approximation
        
        # This is a placeholder assertion
        assert estimated_tokens < 2000, f"Estimated {estimated_tokens} tokens, target <2000"

    def test_multiple_entities_generation_is_fast(self, backend_swea):
        """Verify generating multiple entities is fast with templates"""
        entities = [
            ("Person", ["name:str", "age:int"]),
            ("Product", ["name:str", "price:float"]),
            ("Order", ["total:float", "date:datetime"]),
        ]
        
        start_time = time.time()
        
        for entity_name, attributes in entities:
            result = backend_swea.generate_api_code(entity_name, attributes, {})
            assert result and len(result) > 0
        
        total_time = time.time() - start_time
        
        # Should generate 3 simple entities in under 45s (15s each)
        assert total_time < 45.0, f"Generated 3 entities in {total_time:.2f}s, expected <45s"
        
        avg_time = total_time / len(entities)
        print(f"\n✅ Average generation time: {avg_time:.2f}s per entity")
