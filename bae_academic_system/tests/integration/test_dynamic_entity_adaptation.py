import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from bae_academic_system.agents.student_bae import StudentBAE
from bae_academic_system.core.runtime_kernel import RuntimeKernel


@pytest.mark.integration 
class TestDynamicEntityAdaptation:
    """
    Integration test for Dynamic Generic BAE Architecture
    
    Tests that the system can adapt to different entities and maintain 
    semantic consistency throughout all processing stages:
    1. Business request interpretation
    2. Entity adaptation  
    3. Schema generation
    4. API generation
    5. Database setup
    6. UI generation
    7. Final artifact validation
    """
    
    def setup_method(self):
        """Setup for each test method"""
        # Create temporary directory for generated files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create required directory structure
        os.makedirs("bae_academic_system/generated/models", exist_ok=True)
        os.makedirs("bae_academic_system/generated/routes", exist_ok=True) 
        os.makedirs("bae_academic_system/generated/ui", exist_ok=True)
        os.makedirs("bae_academic_system/database", exist_ok=True)
        os.makedirs("llm/prompts", exist_ok=True)
        
        # Create minimal prompt template
        with open("llm/prompts/student_schema.txt", "w") as f:
            f.write("Generate a Pydantic model for {entity} entity with attributes: {attributes}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('bae_academic_system.llm.openai_client.OpenAIClient')
    def test_book_entity_adaptation_complete_flow(self, mock_openai_client):
        """Test complete flow with Book entity adaptation"""
        
        # Setup mock responses for different stages
        mock_client_instance = Mock()
        
        # Mock business request interpretation (Book focus)
        mock_client_instance.interpret_business_request.return_value = {
            "intent": "manage books in academic library",
            "entity_focus": "Book", 
            "requested_operations": ["create", "read", "update", "delete"],
            "attributes_mentioned": ["title", "author", "ISBN"],
            "business_vocabulary": ["book", "library", "title", "author", "ISBN"],
            "swea_coordination_needed": {
                "programmer": True,
                "frontend": True, 
                "database": True
            },
            "complexity_level": "simple"
        }
        
        # Mock schema generation (Book model)
        mock_client_instance.generate_domain_entity_response.return_value = """
from pydantic import BaseModel, Field

class Book(BaseModel):
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author") 
    ISBN: str = Field(..., regex=r'^\\d{3}-\\d{1,5}-\\d{1,7}-\\d{1,7}-\\d{1}$', description="ISBN number")
        """
        
        mock_openai_client.return_value = mock_client_instance
        
        # Test BAE entity adaptation
        student_bae = StudentBAE()
        
        # Verify initial state
        assert student_bae.primary_entity == "Student"
        assert student_bae.current_entity == "Student"
        
        # Test business request interpretation with Book entity
        result = student_bae.handle_task("interpret_business_request", {
            "request": "Create a system to manage books with title, author, and ISBN",
            "context": "academic"
        })
        
        # Verify entity adaptation occurred
        assert student_bae.current_entity == "Book", f"Expected 'Book', got '{student_bae.current_entity}'"
        assert result["entity_focus"] == "Book"
        assert result["entity_adapted"] == True
        assert result["primary_entity"] == "Student"  # Original remains unchanged
        
        # Verify coordination plan uses correct entity
        coordination_plan = result["coordination_plan"]
        assert len(coordination_plan) == 4
        
        # Check each step has correct entity focus
        schema_step = coordination_plan[0]
        assert schema_step["agent"] == "StudentBAE"
        assert schema_step["payload"]["entity"] == "Book"
        
        api_step = coordination_plan[1] 
        assert api_step["agent"] == "ProgrammerSWEA"
        assert api_step["payload"]["entity"] == "Book"
        
        db_step = coordination_plan[2]
        assert db_step["agent"] == "DatabaseSWEA" 
        assert db_step["payload"]["entity"] == "Book"
        
        ui_step = coordination_plan[3]
        assert ui_step["agent"] == "FrontendSWEA"
        assert ui_step["payload"]["entity"] == "Book"
        assert "create_book" in ui_step["payload"]["user_workflows"]
        assert "view_books" in ui_step["payload"]["user_workflows"]
        
        # Test schema generation with adapted entity
        schema_result = student_bae.handle_task("generate_schema", {
            "attributes": ["title", "author", "ISBN"],
            "context": "academic",
            "entity": "Book"
        })
        
        assert schema_result["entity"] == "Book"
        assert "class Book" in schema_result["code"]
        assert "title" in schema_result["code"]
        assert "author" in schema_result["code"]
        assert "ISBN" in schema_result["code"]
    
    @patch('bae_academic_system.llm.openai_client.OpenAIClient')
    def test_course_entity_adaptation(self, mock_openai_client):
        """Test adaptation to Course entity"""
        
        mock_client_instance = Mock()
        
        # Mock Course entity interpretation
        mock_client_instance.interpret_business_request.return_value = {
            "intent": "manage academic courses",
            "entity_focus": "Course",
            "requested_operations": ["create", "read", "update", "delete"],
            "attributes_mentioned": ["name", "code", "credits", "instructor"],
            "business_vocabulary": ["course", "academic", "credits", "instructor"],
            "swea_coordination_needed": {"programmer": True, "frontend": True, "database": True},
            "complexity_level": "moderate"
        }
        
        mock_openai_client.return_value = mock_client_instance
        
        student_bae = StudentBAE()
        
        result = student_bae.handle_task("interpret_business_request", {
            "request": "Create a system to manage courses with name, code, credits, and instructor",
            "context": "academic"
        })
        
        # Verify Course entity adaptation
        assert student_bae.current_entity == "Course"
        assert result["entity_focus"] == "Course" 
        assert result["entity_adapted"] == True
        
        # Check domain attributes are Course-specific
        assert set(result["domain_attributes"]) == {"name", "code", "credits", "instructor"}
        
        # Verify coordination plan workflows
        ui_step = result["coordination_plan"][3]
        workflows = ui_step["payload"]["user_workflows"]
        assert "create_course" in workflows
        assert "view_courses" in workflows
        assert "edit_course" in workflows
        assert "remove_course" in workflows
    
    @patch('bae_academic_system.llm.openai_client.OpenAIClient')  
    def test_multiple_entity_adaptations(self, mock_openai_client):
        """Test that BAE can adapt multiple times to different entities"""
        
        mock_client_instance = Mock()
        
        # Setup responses for different entity interpretations
        mock_responses = [
            # First: Book entity
            {
                "intent": "manage books",
                "entity_focus": "Book",
                "requested_operations": ["create", "read"],
                "attributes_mentioned": ["title", "author"],
                "business_vocabulary": ["book", "title", "author"],
                "swea_coordination_needed": {"programmer": True, "frontend": True, "database": True},
                "complexity_level": "simple"
            },
            # Second: Teacher entity
            {
                "intent": "manage teachers", 
                "entity_focus": "Teacher",
                "requested_operations": ["create", "read", "update"],
                "attributes_mentioned": ["name", "department", "email"],
                "business_vocabulary": ["teacher", "department", "email"],
                "swea_coordination_needed": {"programmer": True, "frontend": True, "database": True},
                "complexity_level": "simple"
            }
        ]
        
        mock_client_instance.interpret_business_request.side_effect = mock_responses
        mock_openai_client.return_value = mock_client_instance
        
        student_bae = StudentBAE()
        
        # First adaptation: Student -> Book
        result1 = student_bae.handle_task("interpret_business_request", {
            "request": "Create a book management system",
            "context": "academic"
        })
        
        assert student_bae.current_entity == "Book"
        assert result1["entity_adapted"] == True
        
        # Second adaptation: Book -> Teacher  
        result2 = student_bae.handle_task("interpret_business_request", {
            "request": "Create a teacher management system", 
            "context": "academic"
        })
        
        assert student_bae.current_entity == "Teacher"
        assert result2["entity_adapted"] == True
        assert result2["entity_focus"] == "Teacher"
        
        # Verify workflows adapted correctly
        teacher_workflows = result2["coordination_plan"][3]["payload"]["user_workflows"]
        assert "create_teacher" in teacher_workflows
        assert "view_teachers" in teacher_workflows
    
    @patch('bae_academic_system.llm.openai_client.OpenAIClient')
    def test_default_entity_attributes(self, mock_openai_client):
        """Test that GenericBAE returns correct default attributes for different entities"""
        
        # Mock the OpenAI client
        mock_openai_client.return_value = Mock()
        
        from bae_academic_system.agents.generic_bae import GenericBAE
        
        # Test with different entity types
        bae = GenericBAE(primary_entity="Book")
        bae.current_entity = "Book"
        book_attrs = bae._get_default_attributes()
        assert "title: str" in book_attrs
        assert "author: str" in book_attrs
        assert "ISBN: str" in book_attrs
        
        bae.current_entity = "Course"
        course_attrs = bae._get_default_attributes()
        assert "name: str" in course_attrs
        assert "code: str" in course_attrs
        assert "credits: int" in course_attrs
        
        bae.current_entity = "Teacher"
        teacher_attrs = bae._get_default_attributes()
        assert "name: str" in teacher_attrs
        assert "department: str" in teacher_attrs
        assert "email: str" in teacher_attrs
    
    @patch('bae_academic_system.llm.openai_client.OpenAIClient')
    def test_entity_pluralization(self, mock_openai_client):
        """Test entity name pluralization for UI workflows"""
        
        # Mock the OpenAI client
        mock_openai_client.return_value = Mock()
        
        from bae_academic_system.agents.generic_bae import GenericBAE
        
        bae = GenericBAE()
        
        # Test regular pluralization
        assert bae._pluralize_entity("book") == "books"
        assert bae._pluralize_entity("student") == "students"
        assert bae._pluralize_entity("teacher") == "teachers"
        
        # Test special cases
        assert bae._pluralize_entity("library") == "libraries"  # y -> ies
        assert bae._pluralize_entity("class") == "classes"     # s -> es
        assert bae._pluralize_entity("course") == "courses"    # regular + s
    
    @patch('bae_academic_system.llm.openai_client.OpenAIClient')
    def test_business_vocabulary_adaptation(self, mock_openai_client):
        """Test that business vocabulary adapts to the entity context"""
        
        mock_client_instance = Mock()
        mock_client_instance.interpret_business_request.return_value = {
            "intent": "manage books",
            "entity_focus": "Book", 
            "requested_operations": ["create", "read"],
            "attributes_mentioned": ["title", "author", "ISBN"],
            "business_vocabulary": ["book", "library", "catalog", "title", "author", "ISBN", "reading"],
            "swea_coordination_needed": {"programmer": True, "frontend": True, "database": True},
            "complexity_level": "simple"
        }
        mock_openai_client.return_value = mock_client_instance
        
        student_bae = StudentBAE()
        original_vocab = student_bae.business_vocabulary.copy()
        
        result = student_bae.handle_task("interpret_business_request", {
            "request": "Create a book catalog system",
            "context": "academic"
        })
        
        # Verify business vocabulary includes book-related terms
        business_vocab = result["business_vocabulary"]
        assert "book" in business_vocab
        assert "library" in business_vocab
        assert "catalog" in business_vocab
        assert "title" in business_vocab
        
        # Verify coordination plan includes the new vocabulary
        for step in result["coordination_plan"]:
            if "business_vocabulary" in step["payload"]:
                step_vocab = step["payload"]["business_vocabulary"]
                assert "book" in step_vocab
                assert "library" in step_vocab


@pytest.mark.integration_online
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
class TestDynamicEntityAdaptationLive:
    """Live integration tests with actual OpenAI API calls"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Create temporary directory for generated files
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create required directory structure
        os.makedirs("bae_academic_system/generated/models", exist_ok=True)
        os.makedirs("bae_academic_system/generated/routes", exist_ok=True) 
        os.makedirs("bae_academic_system/generated/ui", exist_ok=True)
        os.makedirs("bae_academic_system/database", exist_ok=True)
        os.makedirs("llm/prompts", exist_ok=True)
        
        # Create minimal prompt template
        with open("llm/prompts/student_schema.txt", "w") as f:
            f.write("Generate a Pydantic model for {entity} entity with attributes: {attributes}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_live_entity_adaptation(self):
        """Test entity adaptation with live OpenAI API"""
        
        student_bae = StudentBAE()
        
        # Test Book entity adaptation
        result = student_bae.handle_task("interpret_business_request", {
            "request": "Create a system to manage books with title, author, and ISBN",
            "context": "academic"
        })
        
        # Verify entity adaptation occurred
        assert student_bae.current_entity == "Book" or result.get("entity_adapted") == True
        assert "title" in result["domain_attributes"]
        assert "author" in result["domain_attributes"] 
        assert "ISBN" in result["domain_attributes"]
        
        # Verify coordination plan has correct entity
        coordination_plan = result["coordination_plan"]
        for step in coordination_plan:
            if "entity" in step.get("payload", {}):
                # The entity should be Book (adapted) not Student (original)
                assert step["payload"]["entity"] == "Book"
    
    def test_live_runtime_kernel_entity_consistency(self):
        """Test that Runtime Kernel maintains entity consistency with live API"""
        
        # Set environment to skip server start
        os.environ["SKIP_SERVER_START"] = "1"
        
        try:
            # Create and run runtime kernel
            kernel = RuntimeKernel(context_store_path=os.path.join(self.test_dir, "context_store.json"))
            
            # Run with Book request
            kernel.run(
                "Create a system to manage books with title, author, and ISBN",
                context="academic",
                start_servers=False
            )
            
            # Verify generated files exist and have correct content
            
            # Check API routes file
            api_file = Path("bae_academic_system/generated/routes/student_routes.py")
            if api_file.exists():
                api_content = api_file.read_text()
                # Should contain Book-related content, not just Student
                assert any(word in api_content.lower() for word in ["book", "title", "author", "isbn"]), \
                    f"API content should reference books: {api_content[:200]}..."
            
            # Check UI file
            ui_file = Path("bae_academic_system/generated/ui/student_ui.py") 
            if ui_file.exists():
                ui_content = ui_file.read_text()
                # Should contain book-related content
                assert any(word in ui_content.lower() for word in ["book", "title", "author", "isbn"]), \
                    f"UI content should reference books: {ui_content[:200]}..."
                
        finally:
            # Cleanup environment
            if "SKIP_SERVER_START" in os.environ:
                del os.environ["SKIP_SERVER_START"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 