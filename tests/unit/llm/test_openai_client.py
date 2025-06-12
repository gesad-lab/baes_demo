"""
Unit tests for OpenAI Client module.

Tests the OpenAI client wrapper functionality including domain entity operations,
business request interpretation, and semantic coherence validation.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from baes.llm.openai_client import OpenAIClient


@pytest.mark.unit
class TestOpenAIClient:
    """Test suite for OpenAI Client functionality"""

    def test_client_initialization(self):
        """Test OpenAI client initialization"""
        with patch("openai.OpenAI") as mock_openai:
            client = OpenAIClient()

            assert client.model == "gpt-4o-mini"
            mock_openai.assert_called_once()

    @patch("openai.OpenAI")
    def test_generate_response_success(self, mock_openai):
        """Test successful response generation"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        result = client.generate_response("Test prompt")

        assert result == "Test response"
        mock_client_instance.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_generate_response_with_system_prompt(self, mock_openai):
        """Test response generation with system prompt"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "System response"

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        result = client.generate_response("Test prompt", system_prompt="You are a test assistant")

        assert result == "System response"

        # Verify system prompt was included
        call_args = mock_client_instance.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch("openai.OpenAI")
    def test_generate_response_api_error(self, mock_openai):
        """Test API error handling"""
        # Setup mock to raise exception
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        result = client.generate_response("Test prompt")

        assert "Error generating response" in result
        assert "API Error" in result

    @patch("openai.OpenAI")
    def test_generate_domain_entity_response(self, mock_openai):
        """Test domain entity focused response generation"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Domain entity response"

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        result = client.generate_domain_entity_response(
            "Generate Student schema", entity_type="Student", context="academic"
        )

        assert result == "Domain entity response"

        # Verify domain-focused system prompt was used
        call_args = mock_client_instance.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_message = messages[0]["content"]
        assert "Student entity" in system_message
        assert "academic context" in system_message
        assert "semantic coherence" in system_message

    @patch("openai.OpenAI")
    def test_generate_code_with_domain_focus(self, mock_openai):
        """Test domain-focused code generation"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "class Student(BaseModel): pass"

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        entity_context = {
            "entity": "Student",
            "attributes": ["name", "registration"],
            "business_rules": ["Unique registration"],
        }

        result = client.generate_code_with_domain_focus(
            "Generate Pydantic model", "Pydantic", entity_context
        )

        assert result == "class Student(BaseModel): pass"

        # Verify entity context was included in system prompt
        call_args = mock_client_instance.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_message = messages[0]["content"]
        assert "Student domain entity" in system_message
        assert "Unique registration" in system_message

    @patch("openai.OpenAI")
    def test_validate_semantic_coherence_success(self, mock_openai):
        """Test successful semantic coherence validation"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = """
        {
            "is_semantically_coherent": true,
            "coherence_score": 95,
            "business_vocabulary_preserved": true,
            "domain_rules_followed": true,
            "identified_issues": [],
            "improvement_suggestions": []
        }
        """

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        domain_context = {"entity": "Student", "business_vocabulary": ["Student", "Academic"]}

        result = client.validate_semantic_coherence(
            "class Student(BaseModel): pass", "Pydantic", domain_context
        )

        assert result["is_semantically_coherent"] is True
        assert result["coherence_score"] == 95
        assert result["business_vocabulary_preserved"] is True

    @patch("openai.OpenAI")
    def test_validate_semantic_coherence_json_error(self, mock_openai):
        """Test semantic coherence validation with JSON parsing error"""
        # Setup mock to return invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        domain_context = {"entity": "Student", "business_vocabulary": ["Student", "Academic"]}

        result = client.validate_semantic_coherence("code", "type", domain_context)

        assert result["is_semantically_coherent"] is False
        assert result["coherence_score"] == 0
        assert "error" in result

    @patch("openai.OpenAI")
    def test_interpret_business_request_success(self, mock_openai):
        """Test successful business request interpretation"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = """
        {
            "intent": "create_student_system",
            "entity_focus": "Student",
            "requested_operations": ["create", "read"],
            "attributes_mentioned": ["name", "registration"],
            "business_vocabulary": ["Student", "Academic"],
            "swea_coordination_needed": {
                "programmer": true,
                "frontend": true,
                "database": true
            },
            "complexity_level": "simple"
        }
        """

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        result = client.interpret_business_request("Create a student management system", "academic")

        assert result["intent"] == "create_student_system"
        assert result["entity_focus"] == "Student"
        assert "create" in result["requested_operations"]
        assert result["complexity_level"] == "simple"

    @patch("openai.OpenAI")
    def test_interpret_business_request_json_error(self, mock_openai):
        """Test business request interpretation with JSON parsing error"""
        # Setup mock to return invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"

        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance

        # Test
        client = OpenAIClient()
        result = client.interpret_business_request("Create system", "academic")

        assert result["intent"] == "parse_error"
        assert "error" in result
