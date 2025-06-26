"""
Unit tests for DatabaseSWEA feedback processing edge cases.
Tests the fixes for 'dict' object has no attribute 'strip' error.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from baes.swea_agents.database_swea import DatabaseSWEA


class TestDatabaseSWEAFeedbackProcessing:
    """Test edge cases in DatabaseSWEA feedback processing"""

    def setup_method(self):
        """Set up test fixtures"""
        self.database_swea = DatabaseSWEA()
        self.test_entity = "Student"
        self.original_attributes = ["name:str", "email:str", "age:int"]

    def test_dict_attributes_validation(self):
        """Test that dict attributes are properly converted to strings"""
        # Simulate LLM returning dict attributes (the original bug)
        malformed_interpretation = {
            "attributes": [
                {"name": "student_name", "type": "str"},  # Dict format
                {"name": "student_email", "type": "str"},  # Dict format
                "age:int"  # String format (expected)
            ],
            "additional_requirements": [],
            "constraints": [],
            "modifications": [],
            "explanation": "Test with mixed attribute formats"
        }

        # This should not raise "'dict' object has no attribute 'strip'" error
        validated = self.database_swea._validate_interpretation_structure(malformed_interpretation)

        # Verify all attributes are converted to string format
        assert all(isinstance(attr, str) for attr in validated["attributes"])
        assert "student_name:str" in validated["attributes"]
        assert "student_email:str" in validated["attributes"]
        assert "age:int" in validated["attributes"]

    def test_unexpected_attribute_types(self):
        """Test handling of completely unexpected attribute types"""
        malformed_interpretation = {
            "attributes": [
                123,  # Integer (unexpected)
                ["name", "str"],  # List (unexpected)
                {"name": "email", "type": "str"},  # Dict (fixed in Phase 1)
                "age:int",  # String (expected)
                None  # None (unexpected)
            ],
            "additional_requirements": [],
            "constraints": [],
            "modifications": [],
            "explanation": "Test with various unexpected types"
        }

        # Should handle all types gracefully
        validated = self.database_swea._validate_interpretation_structure(malformed_interpretation)

        # Verify all are converted to strings
        assert all(isinstance(attr, str) for attr in validated["attributes"])
        assert len(validated["attributes"]) == 4  # None should be filtered out

    def test_fallback_database_creation(self):
        """Test fallback database creation when interpretation fails"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = os.path.join(temp_dir, "test_academic.db")
            
            result = self.database_swea._create_fallback_database(self.test_entity, db_file)
            
            # Verify fallback database is created
            assert os.path.exists(db_file)
            assert result["database_path"] == db_file
            assert result["table"] == "students"
            assert result["fallback_used"] is True
            assert "name" in str(result["columns"])

    @patch('baes.swea_agents.database_swea.OpenAIClient')
    def test_llm_response_json_parsing_error(self, mock_openai):
        """Test handling of invalid JSON from LLM"""
        # Mock LLM to return invalid JSON
        mock_client = Mock()
        mock_client.generate_response.return_value = "Invalid JSON response { broken"
        mock_openai.return_value = mock_client
        
        self.database_swea.llm_client = mock_client
        
        feedback = ["No database tables were created"]
        result = self.database_swea._interpret_feedback_for_database_setup(
            feedback, self.test_entity, self.original_attributes
        )
        
        # Should fallback gracefully
        assert "attributes" in result
        assert result["explanation"] == "Extracted information from text response (JSON parsing failed)"

    def test_apply_improvements_with_validation(self):
        """Test _apply_database_improvements with pre-validation"""
        interpretation = {
            "attributes": [
                {"name": "student_name", "type": "str"},  # Dict format that caused original error
                "email:str"  # String format
            ],
            "additional_requirements": ["Add index on email"],
            "constraints": ["UNIQUE(email)"],
            "modifications": ["Updated schema based on feedback"],
            "explanation": "Test mixed attribute format handling"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = os.path.join(temp_dir, "test_academic.db")
            
            # This should not raise any errors
            result = self.database_swea._apply_database_improvements(
                interpretation, self.test_entity, db_file
            )
            
            # Verify database is created successfully
            assert os.path.exists(db_file)
            assert result["tables_created"] == ["students"]
            assert "student_name" in str(result["columns"])

    def test_empty_feedback_handling(self):
        """Test that empty feedback is handled gracefully"""
        result = self.database_swea._interpret_feedback_for_database_setup(
            [], self.test_entity, self.original_attributes
        )
        
        assert result["attributes"] == self.original_attributes
        assert result["additional_requirements"] == []
        assert result["constraints"] == []
        assert result["modifications"] == []

    def test_techlead_feedback_integration(self):
        """Test integration with TechLeadSWEA feedback format"""
        # Simulate the exact payload that caused the original error
        payload = {
            "entity": "Student",
            "attributes": ["name:str", "email:str"],
            "techlead_feedback": ["No database tables were created"],
            "previous_errors": ["Missing database creation confirmation"],
            "expected_output": "Database with students table"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock managed system path
            with patch.object(self.database_swea, 'managed_system_manager') as mock_manager:
                mock_manager.managed_system_path = temp_dir
                mock_manager.ensure_managed_system_structure.return_value = None
                
                # Mock LLM response that might return dict attributes
                with patch.object(self.database_swea, '_interpret_feedback_for_database_setup') as mock_interpret:
                    mock_interpret.return_value = {
                        "attributes": [
                            {"name": "name", "type": "str"},  # Dict format (original bug trigger)
                            {"name": "email", "type": "str"}
                        ],
                        "additional_requirements": [],
                        "constraints": [],
                        "modifications": [],
                        "explanation": "Test database setup"
                    }
                    
                    # This should not raise "'dict' object has no attribute 'strip'" error
                    result = self.database_swea._setup_database(payload)
                    
                    assert result["success"] is True
                    assert "database_path" in result["data"]

    def test_attribute_sanitization(self):
        """Test that attribute names are properly sanitized"""
        interpretation = {
            "attributes": [
                {"name": "Student Name", "type": "str"},  # Spaces should be converted to underscores
                {"name": "EMAIL ADDRESS", "type": "str"},  # Should be lowercased
                "Age In Years:int"  # Already string format
            ],
            "additional_requirements": [],
            "constraints": [],
            "modifications": [],
            "explanation": "Test attribute sanitization"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = os.path.join(temp_dir, "test_academic.db")
            
            result = self.database_swea._apply_database_improvements(
                interpretation, self.test_entity, db_file
            )
            
            # Check that column names are properly sanitized
            columns_str = str(result["columns"])
            assert "student_name" in columns_str.lower()
            assert "email_address" in columns_str.lower()

    def test_error_recovery_chain(self):
        """Test complete error recovery chain: LLM failure → fallback → database creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock LLM to raise an exception
            with patch.object(self.database_swea, 'llm_client') as mock_client:
                mock_client.generate_response.side_effect = Exception("LLM API error")
                
                # Mock managed system path
                with patch.object(self.database_swea, 'managed_system_manager') as mock_manager:
                    mock_manager.managed_system_path = temp_dir
                    
                    db_file = os.path.join(temp_dir, "test_academic.db")
                    
                    # Should recover gracefully with fallback database
                    interpretation = self.database_swea._interpret_feedback_for_database_setup(
                        ["No database tables were created"], self.test_entity, self.original_attributes
                    )
                    
                    result = self.database_swea._apply_database_improvements(
                        interpretation, self.test_entity, db_file
                    )
                    
                    # Verify fallback worked
                    assert os.path.exists(db_file)
                    assert result["fallback_used"] is True


if __name__ == "__main__":
    pytest.main([__file__]) 