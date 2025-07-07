"""
Unit tests for OpenAI Client module.

Tests the OpenAI client wrapper functionality including domain entity operations,
business request interpretation, and semantic coherence validation.
"""

import json
import pytest
from unittest.mock import Mock, patch

from baes.llm.openai_client import OpenAIClient


class TestOpenAIClient:
    @pytest.fixture
    def client(self):
        return OpenAIClient()

    @pytest.fixture
    def mock_openai(self):
        with patch('baes.llm.openai_client.openai') as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client
            yield mock_client

    def test_generate_response_success(self, mock_openai):
        """Test basic generate_response functionality"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_openai.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        result = client.generate_response("Test prompt")

        assert result == "Test response"
        mock_openai.chat.completions.create.assert_called_once()

    def test_generate_response_with_system_prompt(self, mock_openai):
        """Test generate_response with system prompt"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_openai.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        result = client.generate_response("Test prompt", system_prompt="You are a test assistant")

        assert result == "Test response"
        call_args = mock_openai.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'

    def test_generate_response_api_error(self, mock_openai):
        """Test generate_response handles API errors"""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        client = OpenAIClient()
        result = client.generate_response("Test prompt")

        assert "Error generating response" in result

    def test_generate_response_with_json_enforcement(self, mock_openai):
        """Test generate_response with JSON enforcement"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"test": "value"}'
        mock_openai.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        result = client.generate_response("Test prompt", ensure_json=True)

        assert result == '{"test": "value"}'
        call_args = mock_openai.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        assert "CRITICAL: You MUST respond with valid JSON only" in user_message

    def test_generate_response_with_json_schema(self, mock_openai):
        """Test generate_response with JSON schema"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"name": "test", "value": 42}'
        mock_openai.chat.completions.create.return_value = mock_response

        json_schema = {
            "name": "string",
            "value": "number"
        }

        client = OpenAIClient()
        result = client.generate_response("Test prompt", ensure_json=True, json_schema=json_schema)

        assert result == '{"name": "test", "value": 42}'
        call_args = mock_openai.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        assert "EXPECTED JSON STRUCTURE" in user_message
        assert '"name": "string"' in user_message

    def test_generate_json_response_success(self, mock_openai):
        """Test generate_json_response with valid JSON"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"test": "value", "number": 42}'
        mock_openai.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        result = client.generate_json_response("Test prompt")

        assert result == {"test": "value", "number": 42}

    def test_generate_json_response_with_malformed_json(self, mock_openai):
        """Test generate_json_response with malformed JSON that gets fixed"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        # Return malformed JSON with single quotes and trailing comma
        mock_response.choices[0].message.content = "{'test': 'value', 'number': 42,}"
        mock_openai.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        result = client.generate_json_response("Test prompt")

        # Should return a fallback response since the JSON is too malformed
        assert "error" in result
        assert result["fallback_response"] is True

    def test_generate_json_response_with_json_in_markdown(self, mock_openai):
        """Test generate_json_response with JSON wrapped in markdown"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Here is the response:\n```json\n{\"test\": \"value\"}\n```"
        mock_openai.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        result = client.generate_json_response("Test prompt")

        assert result == {"test": "value"}

    def test_generate_json_response_with_fallback_schema(self, mock_openai):
        """Test generate_json_response with fallback schema"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid response"
        mock_openai.chat.completions.create.return_value = mock_response

        fallback_schema = {
            "default_field": "default_value",
            "status": "error"
        }

        client = OpenAIClient()
        result = client.generate_json_response("Test prompt", fallback_schema=fallback_schema)

        assert result["error"] is True
        assert result["fallback_response"] is True
        assert result["default_field"] == "default_value"
        assert result["status"] == "error"

    def test_fix_common_json_issues(self, client):
        """Test the JSON fixing functionality"""
        malformed_json = "Here's the response: {'test': 'value', 'number': 42, 'boolean': True, 'null_value': None,}"
        fixed = client._fix_common_json_issues(malformed_json)
        
        # Should extract and fix the JSON
        assert fixed.startswith('{')
        assert fixed.endswith('}')
        assert '"test": "value"' in fixed
        assert '"number": 42' in fixed
        assert '"boolean": true' in fixed
        assert '"null_value": null' in fixed
        # Should not have trailing comma
        assert not fixed.endswith(',}')

    def test_enhance_prompt_for_json(self, client):
        """Test prompt enhancement for JSON enforcement"""
        original_prompt = "Analyze this data"
        enhanced = client._enhance_prompt_for_json(original_prompt)
        
        assert "CRITICAL: You MUST respond with valid JSON only" in enhanced
        assert "JSON REQUIREMENTS" in enhanced
        assert original_prompt in enhanced

    def test_enhance_prompt_for_json_with_schema(self, client):
        """Test prompt enhancement with JSON schema"""
        original_prompt = "Analyze this data"
        schema = {"name": "string", "age": "number"}
        enhanced = client._enhance_prompt_for_json(original_prompt, schema)
        
        assert "EXPECTED JSON STRUCTURE" in enhanced
        assert '"name": "string"' in enhanced
        assert '"age": "number"' in enhanced
