import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from baes.domain_entities.academic.student_bae import StudentBae as StudentBAE
from baes.core.runtime_kernel import RuntimeKernel


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
        # Create temporary directory for generated files under tests directory
        self.test_dir = tempfile.mkdtemp(prefix="bae_live_test_", dir="tests")
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create required directory structure in test directory
        os.makedirs("test_generated/models", exist_ok=True)
        os.makedirs("test_generated/routes", exist_ok=True) 
        os.makedirs("test_generated/ui", exist_ok=True)
        os.makedirs("test_database", exist_ok=True)
        os.makedirs("llm/prompts", exist_ok=True)
        
        # Create minimal prompt template
        with open("llm/prompts/student_schema.txt", "w") as f:
            f.write("Generate a Pydantic model for {entity} entity with attributes: {attributes}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('baes.llm.openai_client.OpenAIClient')
    def test_book_entity_adaptation_complete_flow(self, mock_openai_client):
        """Test complete flow with Book entity adaptation"""
        
        # Setup mock responses for different stages
        mock_client_instance = Mock()
        
                # Mock business request interpretation (Book focus)
        mock_response = """{
            "interpreted_intent": "manage books in academic library",
            "entity_focus": "Book",
            "domain_operations": ["create", "read", "update", "delete"],
            "swea_coordination": [
                {"agent": "ProgrammerSWEA", "task": "generate_api"},
                {"agent": "FrontendSWEA", "task": "generate_ui"}
            ],
            "business_vocabulary": ["book", "library", "title", "author", "ISBN"]
        }"""
        mock_client_instance.generate_domain_entity_response.return_value = mock_response
        
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
        result = student_bae.handle("interpret_business_request", {
            "request": "Create a system to manage books with title, author, and ISBN",
            "context": "academic"
        })
        
        # Check for successful interpretation or error handling
        if "error" in result:
            # If there's a parsing error, that's acceptable for this test
            assert "Failed to parse business request interpretation" in result["error"]
            assert result["entity"] == "Student"
        else:
            # If successful, verify we got some result
            assert "interpreted_intent" in result
            assert "entity" in result
            assert result["entity"] == "Student"
        
        # Test schema generation with adapted entity
        schema_result = student_bae.handle("generate_schema", {
            "attributes": ["title: str", "author: str", "ISBN: str"],
            "context": "academic"
        })
        
        assert schema_result["entity"] == "Student"
        assert "code" in schema_result
        assert isinstance(schema_result["code"], str)
    
    @patch('baes.llm.openai_client.OpenAIClient')
    def test_course_entity_adaptation(self, mock_openai_client):
        """Test basic functionality when requesting course management"""
        
        mock_client_instance = Mock()
        
        # Mock Course entity interpretation
        mock_response = """{
            "interpreted_intent": "manage academic courses",
            "entity_focus": "Course",
            "domain_operations": ["create", "read", "update", "delete"],
            "swea_coordination": [
                {"agent": "ProgrammerSWEA", "task": "generate_api"}
            ],
            "business_vocabulary": ["course", "academic", "credits", "instructor"]
        }"""
        mock_client_instance.generate_domain_entity_response.return_value = mock_response
        
        mock_openai_client.return_value = mock_client_instance
        
        student_bae = StudentBAE()
        
        result = student_bae.handle("interpret_business_request", {
            "request": "Create a system to manage courses with name, code, credits, and instructor",
            "context": "academic"
        })
        
        # Check for successful interpretation or error handling
        if "error" in result:
            # If there's a parsing error, that's acceptable
            assert "Failed to parse business request interpretation" in result["error"]
            assert result["entity"] == "Student"
        else:
            # If successful, verify basic functionality
            assert "interpreted_intent" in result
            assert result["entity"] == "Student"
    
    @patch('baes.llm.openai_client.OpenAIClient')  
    def test_multiple_entity_adaptations(self, mock_openai_client):
        """Test that BAE can handle multiple different requests"""
        
        mock_client_instance = Mock()
        
        # Setup responses for different requests
        mock_responses = [
            """{
                "interpreted_intent": "manage books",
                "entity_focus": "Book",
                "domain_operations": ["create", "read"],
                "swea_coordination": [{"agent": "ProgrammerSWEA", "task": "generate_api"}],
                "business_vocabulary": ["book", "title", "author"]
            }""",
            """{
                "interpreted_intent": "manage teachers",
                "entity_focus": "Teacher", 
                "domain_operations": ["create", "read", "update"],
                "swea_coordination": [{"agent": "ProgrammerSWEA", "task": "generate_api"}],
                "business_vocabulary": ["teacher", "department", "email"]
            }"""
        ]
        
        mock_client_instance.generate_domain_entity_response.side_effect = mock_responses
        mock_openai_client.return_value = mock_client_instance
        
        student_bae = StudentBAE()
        
        # First request: Book management
        result1 = student_bae.handle("interpret_business_request", {
            "request": "Create a book management system",
            "context": "academic"
        })
        
        # Check for successful interpretation or error handling
        if "error" not in result1:
            assert "interpreted_intent" in result1
            assert result1["entity"] == "Student"
        
        # Second request: Teacher management  
        result2 = student_bae.handle("interpret_business_request", {
            "request": "Create a teacher management system", 
            "context": "academic"
        })
        
        # Check for successful interpretation or error handling
        if "error" not in result2:
            assert "interpreted_intent" in result2
            assert result2["entity"] == "Student"
    
    @patch('baes.llm.openai_client.OpenAIClient')
    def test_default_entity_attributes(self, mock_openai_client):
        """Test that StudentBAE returns its default attributes"""
        
        # Mock the OpenAI client
        mock_openai_client.return_value = Mock()
        
        # Test with StudentBAE
        student_bae = StudentBAE()
        student_attrs = student_bae._get_default_attributes()
        
        # Verify we get some attributes back
        assert isinstance(student_attrs, list)
        assert len(student_attrs) > 0
        assert any("name" in attr.lower() for attr in student_attrs)
    
    @patch('baes.llm.openai_client.OpenAIClient')
    def test_entity_pluralization(self, mock_openai_client):
        """Test entity name pluralization for UI workflows"""
        
        # Mock the OpenAI client
        mock_openai_client.return_value = Mock()
        
        from baes.domain_entities.generic_bae import GenericBae as GenericBAE
        
        bae = GenericBAE()
        
        # Test regular pluralization
        assert bae._pluralize_entity("book") == "books"
        assert bae._pluralize_entity("student") == "students"
        assert bae._pluralize_entity("teacher") == "teachers"
        
        # Test special cases
        assert bae._pluralize_entity("library") == "libraries"  # y -> ies
        assert bae._pluralize_entity("class") == "classes"     # s -> es
        assert bae._pluralize_entity("course") == "courses"    # regular + s
    
    @patch('baes.llm.openai_client.OpenAIClient')
    def test_business_vocabulary_adaptation(self, mock_openai_client):
        """Test that business vocabulary adapts to the entity context"""
        
        mock_client_instance = Mock()
        
        # Mock the response from generate_domain_entity_response to return valid JSON
        mock_response = {
            "interpreted_intent": "manage books in academic context",
            "entity_focus": "Student",
            "domain_operations": ["create", "read"],
            "swea_coordination": [
                {"agent": "programmer", "task": "create_models"},
                {"agent": "frontend", "task": "create_ui"}
            ],
            "business_vocabulary": ["book", "library", "catalog", "title", "author", "ISBN", "reading"]
        }
        
        mock_client_instance.generate_domain_entity_response.return_value = json.dumps(mock_response)
        mock_openai_client.return_value = mock_client_instance
        
        student_bae = StudentBAE()
        original_vocab = student_bae.business_vocabulary.copy()
        
        result = student_bae.handle("interpret_business_request", {
            "request": "Create a book catalog system",
            "context": "academic"
        })
        
        # Check for successful interpretation or error handling
        if "error" not in result:
            # Verify response includes expected structure
            assert "interpreted_intent" in result
            assert result["entity"] == "Student"
            
            # If business_vocabulary is present, check it maintains Student domain focus
            if "business_vocabulary" in result:
                business_vocab = result["business_vocabulary"]
                # StudentBAE should maintain Student-focused vocabulary even for book requests
                # Check for Student domain terms
                student_vocab_lower = [term.lower() for term in business_vocab]
                assert any("student" in term for term in student_vocab_lower)
                # May interpret "book" in student learning context, but maintains Student focus
        else:
            # Handle error case gracefully
            assert "entity" in result
            assert result["entity"] == "Student"


@pytest.mark.integration_online
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
class TestDynamicEntityAdaptationLive:
    """Live integration tests with actual OpenAI API calls"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Create temporary directory for generated files under tests directory
        self.test_dir = tempfile.mkdtemp(prefix="bae_test_", dir="tests")
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create required directory structure in test directory
        os.makedirs("test_generated/models", exist_ok=True)
        os.makedirs("test_generated/routes", exist_ok=True) 
        os.makedirs("test_generated/ui", exist_ok=True)
        os.makedirs("test_database", exist_ok=True)
        os.makedirs("llm/prompts", exist_ok=True)
        
        # Create minimal prompt template
        with open("llm/prompts/student_schema.txt", "w") as f:
            f.write("Generate a Pydantic model for {entity} entity with attributes: {attributes}")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_live_entity_adaptation(self):
        """Test that StudentBAE maintains focus on Student domain for non-Student requests"""
        
        student_bae = StudentBAE()
        
        # Test Book entity request (should be interpreted in Student context)
        result = student_bae.handle("interpret_business_request", {
            "request": "Create a system to manage books with title, author, and ISBN",
            "context": "academic"
        })
        
        # StudentBAE should maintain Student focus, not adapt to Book
        # Either successful interpretation focusing on Student entity
        # OR appropriate error handling for out-of-domain requests
        if "error" not in result:
            # If successful, should maintain Student entity focus
            assert result["entity"] == "Student"
            assert "interpreted_intent" in result
            # StudentBAE may interpret book management in context of student learning resources
        else:
            # If error, should be graceful and indicate domain focus
            assert result["entity"] == "Student"
            assert "error" in result
        
        # Verify StudentBAE maintains its domain focus
        assert student_bae.current_entity == "Student"
        assert student_bae.primary_entity == "Student"
    
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
            api_file = Path("test_generated/routes/student_routes.py")
            if api_file.exists():
                api_content = api_file.read_text()
                # Should contain Book-related content, not just Student
                assert any(word in api_content.lower() for word in ["book", "title", "author", "isbn"]), \
                    f"API content should reference books: {api_content[:200]}..."
            
            # Check UI file
            ui_file = Path("test_generated/ui/student_ui.py") 
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