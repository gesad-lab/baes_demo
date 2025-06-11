"""
Unit tests for Student BAE module.

Tests the Student BAE functionality including domain entity representation,
business request interpretation, schema generation, and SWEA coordination.
"""

import pytest
from unittest.mock import Mock, patch
from agents.student_bae import StudentBAE


@pytest.mark.unit
class TestStudentBAE:
    """Test suite for Student BAE functionality"""
    
    def test_initialization(self):
        """Test Student BAE initialization"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            assert student_bae.name == "StudentBAE"
            assert student_bae.role == "Domain Entity Representative"
            assert student_bae.domain_knowledge == {}
            assert student_bae.current_schema == {}
            assert student_bae.context_configurations == {}
    
    @patch('agents.student_bae.OpenAIClient')
    def test_interpret_business_request_success(self, mock_openai_client):
        """Test successful business request interpretation"""
        # Setup mock response
        mock_client_instance = Mock()
        mock_client_instance.interpret_business_request.return_value = {
            "intent": "create_student_management_system",
            "attributes_mentioned": ["name", "registration", "course"],
            "business_vocabulary": ["Student", "Academic", "Registration"]
        }
        mock_openai_client.return_value = mock_client_instance
        
        # Test
        student_bae = StudentBAE()
        payload = {
            "request": "Create a system to manage students",
            "context": "academic"
        }
        
        result = student_bae.handle_task("interpret_business_request", payload)
        
        assert result["interpreted_intent"] == "create_student_management_system"
        assert "name" in result["domain_attributes"]
        assert len(result["coordination_plan"]) > 0
        assert "Student" in result["business_vocabulary"]
    
    @patch('agents.student_bae.OpenAIClient')
    def test_generate_schema_success(self, mock_openai_client):
        """Test successful schema generation"""
        # Setup mock response
        mock_client_instance = Mock()
        mock_client_instance.generate_domain_entity_response.return_value = """
from pydantic import BaseModel
from typing import Optional

class Student(BaseModel):
    name: str
    registration_number: str
    course: str
"""
        mock_openai_client.return_value = mock_client_instance
        
        # Test
        student_bae = StudentBAE()
        payload = {
            "attributes": ["name: str", "registration_number: str", "course: str"],
            "context": "academic"
        }
        
        result = student_bae.handle_task("generate_schema", payload)
        
        assert result["entity"] == "Student"
        assert "class Student(BaseModel)" in result["code"]
        assert result["context"] == "academic"
        assert len(result["attributes"]) == 3
        assert "business_rules" in result
    
    @patch('agents.student_bae.OpenAIClient')
    @patch('builtins.open', create=True)
    def test_generate_schema_with_prompt_template(self, mock_open, mock_openai_client):
        """Test schema generation using prompt template"""
        # Setup file reading mock
        mock_file = Mock()
        mock_file.read.return_value = "Template with {attributes} and {context}"
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Setup OpenAI mock
        mock_client_instance = Mock()
        mock_client_instance.generate_domain_entity_response.return_value = "Generated schema"
        mock_openai_client.return_value = mock_client_instance
        
        # Test
        student_bae = StudentBAE()
        payload = {
            "attributes": ["name: str"],
            "context": "academic"
        }
        
        result = student_bae.handle_task("generate_schema", payload)
        
        # Verify template was used
        mock_open.assert_called_once()
        assert result["entity"] == "Student"
        assert result["code"] == "Generated schema"
    
    @patch('agents.student_bae.OpenAIClient')
    def test_evolve_schema_success(self, mock_openai_client):
        """Test successful schema evolution"""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.generate_domain_entity_response.return_value = """
class Student(BaseModel):
    name: str
    registration_number: str
    course: str
    birth_date: date
    gpa: float
"""
        mock_openai_client.return_value = mock_client_instance
        
        # Test
        student_bae = StudentBAE()
        
        # Set initial schema
        initial_schema = {
            "entity": "Student",
            "code": "class Student(BaseModel): pass",
            "attributes": ["name", "registration"],
            "context": "academic"
        }
        student_bae.update_memory("current_schema", initial_schema)
        
        payload = {
            "evolution_request": "Add birth date and GPA",
            "new_attributes": ["birth_date: date", "gpa: float"]
        }
        
        result = student_bae.handle_task("evolve_schema", payload)
        
        assert result["entity"] == "Student"
        assert "birth_date: date" in str(result["attributes"])
        assert "gpa: float" in str(result["attributes"])
        assert "evolution_history" in result
    
    @patch('agents.student_bae.OpenAIClient')
    def test_evolve_schema_no_current_schema(self, mock_openai_client):
        """Test schema evolution without current schema"""
        mock_openai_client.return_value = Mock()
        
        student_bae = StudentBAE()
        payload = {
            "evolution_request": "Add field",
            "new_attributes": ["new_field: str"]
        }
        
        result = student_bae.handle_task("evolve_schema", payload)
        
        assert "error" in result
        assert "No current schema to evolve" in result["error"]
    
    def test_configure_context_success(self):
        """Test successful context configuration"""
        with patch('agents.student_bae.OpenAIClient'):
            student_bae = StudentBAE()
            
            payload = {
                "target_context": "open_courses",
                "modifications": ["remove_registration", "add_modality"],
                "base_context": "academic"
            }
            
            result = student_bae.handle_task("configure_context", payload)
            
            assert result["configured_context"] == "open_courses"
            assert result["base_context"] == "academic"
            assert result["modifications"] == ["remove_registration", "add_modality"]
            assert "reuse_percentage" in result
    
    def test_coordinate_swea_success(self):
        """Test successful SWEA coordination"""
        with patch('agents.student_bae.OpenAIClient'):
            student_bae = StudentBAE()
            
            payload = {
                "swea_tasks": [
                    {"agent": "ProgrammerSWEA", "task": "generate_api"},
                    {"agent": "FrontendSWEA", "task": "generate_ui"}
                ],
                "domain_context": {"entity": "Student", "context": "academic"}
            }
            
            result = student_bae.handle_task("coordinate_swea", payload)
            
            coordination_plan = result["coordination_plan"]
            assert len(coordination_plan) == 2
            
            # Check first task
            first_task = coordination_plan[0]
            assert first_task["swea_agent"] == "ProgrammerSWEA"
            assert first_task["task_type"] == "generate_api"
            assert "domain_context" in first_task
            assert "semantic_requirements" in first_task
            assert first_task["semantic_requirements"]["maintain_domain_coherence"] is True
    
    @patch('agents.student_bae.OpenAIClient')
    def test_validate_domain_rules_success(self, mock_openai_client):
        """Test successful domain rules validation"""
        # Setup mock response
        mock_client_instance = Mock()
        mock_client_instance.validate_semantic_coherence.return_value = {
            "is_coherent": True,
            "semantic_coherence_score": 95,
            "business_vocabulary_preserved": True,
            "domain_rules_followed": True,
            "issues": [],
            "recommendations": ["Consider adding validation"]
        }
        mock_openai_client.return_value = mock_client_instance
        
        # Test
        student_bae = StudentBAE()
        payload = {
            "artifact_code": "class Student(BaseModel): pass",
            "artifact_type": "Pydantic Model"
        }
        
        result = student_bae.handle_task("validate_domain_rules", payload)
        
        assert result["is_valid"] is True
        assert result["semantic_coherence_score"] == 95
        assert result["business_vocabulary_preserved"] is True
        assert result["domain_rules_followed"] is True
    
    @patch('agents.student_bae.OpenAIClient')
    def test_validate_domain_rules_json_error(self, mock_openai_client):
        """Test domain rules validation with JSON error"""
        # Setup mock to return invalid JSON
        mock_client_instance = Mock()
        mock_client_instance.validate_semantic_coherence.return_value = {
            "is_coherent": False,
            "error": "Invalid validation result"
        }
        mock_openai_client.return_value = mock_client_instance
        
        # Test
        student_bae = StudentBAE()
        payload = {
            "artifact_code": "code",
            "artifact_type": "type"
        }
        
        result = student_bae.handle_task("validate_domain_rules", payload)
        
        assert result["is_valid"] is False
        assert "error" in result
    
    def test_unknown_task_handling(self):
        """Test handling of unknown tasks"""
        with patch('agents.student_bae.OpenAIClient'):
            student_bae = StudentBAE()
            
            result = student_bae.handle_task("unknown_task", {})
            
            assert "error" in result
            assert "Unknown task" in result["error"]
            assert "supported_tasks" in result
    
    def test_extract_business_rules(self):
        """Test business rules extraction"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            attributes = ["name: str", "email: str", "age: int", "registration: str"]
            context = "academic"
            
            rules = student_bae._extract_business_rules(attributes, context)
            
            assert isinstance(rules, list)
            assert any("email" in rule.lower() for rule in rules)
            assert any("age" in rule.lower() for rule in rules)
            assert any("registration" in rule.lower() for rule in rules)
    
    def test_update_domain_knowledge(self):
        """Test domain knowledge update"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            context = "academic"
            attributes = ["name", "registration"]
            
            student_bae._update_domain_knowledge(context, attributes)
            
            assert context in student_bae.domain_knowledge
            knowledge = student_bae.domain_knowledge[context]
            assert knowledge["core_attributes"] == attributes
            assert "last_updated" in knowledge
            assert "usage_count" in knowledge
    
    def test_generate_context_rules(self):
        """Test context-specific rules generation"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            # Test open courses context
            open_course_rules = student_bae._generate_context_rules("open_courses", [])
            assert any("optional" in rule.lower() for rule in open_course_rules)
            assert any("modality" in rule.lower() for rule in open_course_rules)
            
            # Test corporate training context
            corporate_rules = student_bae._generate_context_rules("corporate_training", [])
            assert any("employee" in rule.lower() for rule in corporate_rules)
            assert any("department" in rule.lower() for rule in corporate_rules)
    
    def test_extract_business_vocabulary(self):
        """Test business vocabulary extraction"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            # Set up schema
            schema = {
                "attributes": ["name: str", "registration: str", "course: str"]
            }
            student_bae.update_memory("current_schema", schema)
            
            vocabulary = student_bae._extract_business_vocabulary()
            
            assert "Student" in vocabulary
            assert "Academic" in vocabulary
            assert "Learning" in vocabulary
            # Attribute-derived vocabulary
            assert "Name" in vocabulary
            assert "Registration" in vocabulary
            assert "Course" in vocabulary
    
    def test_calculate_reuse_percentage(self):
        """Test reuse percentage calculation"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            # Test with base knowledge
            base_knowledge = {
                "core_attributes": ["name", "registration", "course", "email"]
            }
            
            # No modifications - 100% reuse
            reuse_100 = student_bae._calculate_reuse_percentage(base_knowledge, [])
            assert reuse_100 == 100.0
            
            # Some modifications - partial reuse
            modifications = ["remove_registration", "add_modality"]
            reuse_partial = student_bae._calculate_reuse_percentage(base_knowledge, modifications)
            assert 0 <= reuse_partial <= 100
            
            # Empty base knowledge - 0% reuse
            reuse_0 = student_bae._calculate_reuse_percentage({}, modifications)
            assert reuse_0 == 0.0
    
    def test_domain_knowledge_persistence(self):
        """Test that domain knowledge persists across operations"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            # Store domain knowledge
            knowledge = {
                "entity": "Student",
                "core_attributes": ["name", "registration"],
                "business_rules": ["Unique registration"]
            }
            student_bae.preserve_domain_knowledge("Student", knowledge)
            
            # Perform other operations
            student_bae.handle_task("configure_context", {
                "target_context": "open_courses",
                "modifications": []
            })
            
            # Verify knowledge is still there
            assert "Student" in student_bae.domain_knowledge
    
    def test_context_configuration_preservation(self):
        """Test that context configurations are preserved"""
        with patch('llm.openai_client.OpenAIClient'):
            student_bae = StudentBAE()
            
            # Configure for different contexts
            payload1 = {
                "target_context": "university",
                "modifications": ["strict_registration"]
            }
            
            payload2 = {
                "target_context": "open_courses",
                "modifications": ["flexible_registration"]
            }
            
            student_bae.handle_task("configure_context", payload1)
            student_bae.handle_task("configure_context", payload2)
            
            # Verify both configurations are preserved
            assert "university" in student_bae.context_configurations
            assert "open_courses" in student_bae.context_configurations
            
            university_config = student_bae.context_configurations["university"]
            assert "strict_registration" in university_config["context_modifications"] 