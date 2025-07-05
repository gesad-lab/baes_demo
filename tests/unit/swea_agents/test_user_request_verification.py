"""
Tests for TechLeadSWEA User Request Compliance Verification

Tests the new verification functionality that ensures extracted attributes
match the user's original request.
"""

import pytest
from unittest.mock import Mock, patch
from baes.swea_agents.techlead_swea import TechLeadSWEA


class TestUserRequestVerification:
    """Test user request compliance verification functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.techlead = TechLeadSWEA()

    def test_verify_user_request_compliance_success(self):
        """Test successful user request compliance verification."""
        payload = {
            "entity": "Student",
            "user_request": "Create a student with name and email",
            "extracted_attributes": [
                {"name": "name", "type": "str"},
                {"name": "email", "type": "str"}
            ],
            "context": "academic"
        }

        with patch.object(self.techlead, '_analyze_user_request_for_attributes') as mock_analyze:
            mock_analyze.return_value = [
                {"name": "name", "type": "str", "source": "explicit"},
                {"name": "email", "type": "str", "source": "explicit"}
            ]

            result = self.techlead._verify_user_request_compliance(payload)

            assert result["success"] is True
            assert result["compliance_score"] == 1.0
            assert result["verification_type"] == "user_request_compliance"
            assert len(result["issues"]) == 0
            assert "User request compliance verified successfully" in result["suggestions"]

    def test_verify_user_request_compliance_missing_attributes(self):
        """Test user request compliance verification with missing attributes."""
        payload = {
            "entity": "Student",
            "user_request": "Create a student with name, email, and age",
            "extracted_attributes": [
                {"name": "name", "type": "str"},
                {"name": "email", "type": "str"}
            ],
            "context": "academic"
        }

        with patch.object(self.techlead, '_analyze_user_request_for_attributes') as mock_analyze:
            mock_analyze.return_value = [
                {"name": "name", "type": "str", "source": "explicit"},
                {"name": "email", "type": "str", "source": "explicit"},
                {"name": "age", "type": "int", "source": "explicit"}
            ]

            result = self.techlead._verify_user_request_compliance(payload)

            assert result["success"] is False
            assert result["compliance_score"] < 1.0
            assert "age" in result["missing_attributes"]
            assert "Missing attributes requested by user" in result["issues"][0]

    def test_verify_user_request_compliance_extra_attributes(self):
        """Test user request compliance verification with extra attributes."""
        payload = {
            "entity": "Student",
            "user_request": "Create a student with name and email",
            "extracted_attributes": [
                {"name": "name", "type": "str"},
                {"name": "email", "type": "str"},
                {"name": "age", "type": "int"}
            ],
            "context": "academic"
        }

        with patch.object(self.techlead, '_analyze_user_request_for_attributes') as mock_analyze:
            mock_analyze.return_value = [
                {"name": "name", "type": "str", "source": "explicit"},
                {"name": "email", "type": "str", "source": "explicit"}
            ]

            result = self.techlead._verify_user_request_compliance(payload)

            assert result["success"] is False
            assert result["compliance_score"] == 1.0  # All expected attributes present
            assert "age" in result["extra_attributes"]
            assert "Extra attributes not requested by user" in result["issues"][0]

    def test_verify_user_request_compliance_no_user_request(self):
        """Test user request compliance verification with no user request."""
        payload = {
            "entity": "Student",
            "extracted_attributes": [{"name": "name", "type": "str"}],
            "context": "academic"
        }

        result = self.techlead._verify_user_request_compliance(payload)

        assert result["success"] is False
        assert result["compliance_score"] == 0.0
        assert "No user request provided for verification" in result["issues"]

    def test_verify_user_request_compliance_no_attributes(self):
        """Test user request compliance verification with no extracted attributes."""
        payload = {
            "entity": "Student",
            "user_request": "Create a student with name and email",
            "extracted_attributes": [],
            "context": "academic"
        }

        result = self.techlead._verify_user_request_compliance(payload)

        assert result["success"] is False
        assert result["compliance_score"] == 0.0
        assert "No attributes extracted from user request" in result["issues"]

    def test_analyze_user_request_for_attributes(self):
        """Test user request analysis for attribute extraction."""
        user_request = "Create a student with name and email"
        entity = "Student"
        context = "academic"

        with patch.object(self.techlead.llm_client, 'generate_response') as mock_llm:
            mock_llm.return_value = '''
            [
                {"name": "name", "type": "str", "source": "explicit"},
                {"name": "email", "type": "str", "source": "explicit"}
            ]
            '''

            result = self.techlead._analyze_user_request_for_attributes(user_request, entity, context)

            assert len(result) == 2
            assert result[0]["name"] == "name"
            assert result[0]["type"] == "str"
            assert result[0]["source"] == "explicit"
            assert result[1]["name"] == "email"
            assert result[1]["type"] == "str"
            assert result[1]["source"] == "explicit"

    def test_fallback_attribute_extraction(self):
        """Test fallback attribute extraction using pattern matching."""
        user_request = "Create a student with name and email"
        entity = "Student"

        result = self.techlead._fallback_attribute_extraction(user_request, entity)

        assert len(result) == 2
        assert result[0]["name"] == "name"
        assert result[0]["type"] == "str"
        assert result[0]["source"] == "pattern_match"
        assert result[1]["name"] == "email"
        assert result[1]["type"] == "str"
        assert result[1]["source"] == "pattern_match"

    def test_compare_attributes_compliance_perfect_match(self):
        """Test attribute comparison with perfect match."""
        expected = [
            {"name": "name", "type": "str", "source": "explicit"},
            {"name": "email", "type": "str", "source": "explicit"}
        ]
        extracted = [
            {"name": "name", "type": "str"},
            {"name": "email", "type": "str"}
        ]
        user_request = "Create a student with name and email"

        result = self.techlead._compare_attributes_compliance(expected, extracted, user_request)

        assert result["is_compliant"] is True
        assert result["compliance_score"] == 1.0
        assert len(result["missing_attributes"]) == 0
        assert len(result["extra_attributes"]) == 0
        assert result["matched_attributes"] == 2

    def test_compare_attributes_compliance_partial_match(self):
        """Test attribute comparison with partial match."""
        expected = [
            {"name": "name", "type": "str", "source": "explicit"},
            {"name": "email", "type": "str", "source": "explicit"},
            {"name": "age", "type": "int", "source": "explicit"}
        ]
        extracted = [
            {"name": "name", "type": "str"},
            {"name": "email", "type": "str"}
        ]
        user_request = "Create a student with name, email, and age"

        result = self.techlead._compare_attributes_compliance(expected, extracted, user_request)

        assert result["is_compliant"] is False
        assert result["compliance_score"] == 2/3  # 2 out of 3 attributes matched
        assert "age" in result["missing_attributes"]
        assert len(result["extra_attributes"]) == 0
        assert result["matched_attributes"] == 2

    def test_coordinate_system_generation_with_verification(self):
        """Test that coordination includes user request verification."""
        payload = {
            "entity": "Student",
            "attributes": [{"name": "name", "type": "str"}, {"name": "email", "type": "str"}],
            "context": "academic",
            "user_request": "Create a student with name and email",
            "is_evolution": False,
            "business_requirements": {}
        }

        with patch.object(self.techlead, '_analyze_user_request_for_attributes') as mock_analyze:
            mock_analyze.return_value = [
                {"name": "name", "type": "str", "source": "explicit"},
                {"name": "email", "type": "str", "source": "explicit"}
            ]

            result = self.techlead._coordinate_system_generation(payload)

            assert result["success"] is True
            assert result["data"]["user_request_verified"] is True

    def test_coordinate_system_generation_verification_failure(self):
        """Test that coordination fails when verification fails."""
        payload = {
            "entity": "Student",
            "attributes": [{"name": "name", "type": "str"}],
            "context": "academic",
            "user_request": "Create a student with name and email",
            "is_evolution": False,
            "business_requirements": {}
        }

        with patch.object(self.techlead, '_analyze_user_request_for_attributes') as mock_analyze:
            mock_analyze.return_value = [
                {"name": "name", "type": "str", "source": "explicit"},
                {"name": "email", "type": "str", "source": "explicit"}
            ]

            result = self.techlead._coordinate_system_generation(payload)

            assert result["success"] is False
            assert "User request compliance verification failed" in result["error"]
            assert "email" in result["compliance_issues"][0]

    def test_clean_json_response(self):
        """Test JSON response cleaning functionality."""
        response = '''
        Here is the JSON response:
        ```json
        [
            {"name": "name", "type": "str", "source": "explicit"},
            {"name": "email", "type": "str", "source": "explicit"}
        ]
        ```
        '''

        cleaned = self.techlead._clean_json_response(response)

        assert cleaned.startswith('[')
        assert cleaned.endswith(']')
        assert '"name": "name"' in cleaned
        assert '"name": "email"' in cleaned 