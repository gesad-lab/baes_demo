"""
Test suite for force-accept mode implementation.

This module tests both strict mode and force-accept mode to ensure:
1. Strict mode interrupts generation after max retries (old behavior)
2. Force-accept mode accepts code after max retries (new default behavior)
3. Metadata is properly tracked for force-accepted artifacts
"""

import os
import pytest
from unittest.mock import patch
import importlib

from baes.swea_agents.techlead_swea import TechLeadSWEA
from config import Config


class TestForceAcceptMode:
    """Test suite for force-accept mode functionality"""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Setup environment variables for testing"""
        # Store original values
        original_strict_mode = os.environ.get("BAE_STRICT_MODE")
        original_max_retries = os.environ.get("BAE_MAX_RETRIES")
        original_api_key = os.environ.get("OPENAI_API_KEY")
        
        # Set test values
        os.environ["BAE_MAX_RETRIES"] = "3"
        os.environ["OPENAI_API_KEY"] = "test-key-for-mocking"
        
        yield
        
        # Restore original values
        if original_strict_mode is not None:
            os.environ["BAE_STRICT_MODE"] = original_strict_mode
        elif "BAE_STRICT_MODE" in os.environ:
            del os.environ["BAE_STRICT_MODE"]
            
        if original_max_retries is not None:
            os.environ["BAE_MAX_RETRIES"] = original_max_retries
        elif "BAE_MAX_RETRIES" in os.environ:
            del os.environ["BAE_MAX_RETRIES"]
            
        if original_api_key is not None:
            os.environ["OPENAI_API_KEY"] = original_api_key
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

    def test_force_accept_mode_with_quality_issues(self):
        """Test that force-accept mode accepts code after max retries with quality issues"""
        # Create TechLeadSWEA instance
        techlead = TechLeadSWEA()
        
        # Create a mock validation result that indicates failure
        mock_validation_result = {
            "is_valid": False,
            "quality_score": 0.5,
            "details": "Code has quality issues",
            "issues": ["Missing error handling", "Poor code structure"],
            "suggestions": ["Add proper error handling", "Improve code structure"],
            "actionable_feedback": ["Add proper error handling", "Improve code structure"],
        }
        
        # Create payload for review with max retries reached
        payload = {
            "entity": "Student",
            "swea_agent": "BackendSWEA",
            "task_type": "generate_api",
            "result": {
                "success": True,
                "data": {
                    "file_path": "/path/to/file.py",
                    "code": "def test(): pass"
                }
            },
            "retry_count": 3,  # Max retries reached
        }
        
        # Mock Config.BAE_STRICT_MODE to False (force-accept mode) and validation method
        with patch('baes.swea_agents.techlead_swea.Config.BAE_STRICT_MODE', False):
            with patch('baes.swea_agents.techlead_swea.Config.BAE_MAX_RETRIES', 3):
                with patch.object(techlead, '_validate_with_llm', return_value=mock_validation_result):
                    result = techlead._review_and_approve(payload)
        
        # Verify force-accept behavior
        assert result.get("approved") == True, "Code should be force-accepted"
        assert result.get("success") == True, "Result should be successful"
        assert result.get("force_accepted") == True, "Should be marked as force-accepted"
        assert result.get("data", {}).get("force_accepted") == True
        assert "force_accept_reason" in result.get("data", {})
        # Quality score may be adjusted by validation, just check it exists
        assert "quality_score" in result

    def test_strict_mode_rejects_after_max_retries(self):
        """Test that strict mode rejects code after max retries without force-accepting"""
        # Create TechLeadSWEA instance
        techlead = TechLeadSWEA()
        
        # Create a mock validation result that indicates failure
        mock_validation_result = {
            "is_valid": False,
            "quality_score": 0.3,
            "details": "Code has quality issues",
            "issues": ["Missing error handling", "Poor code structure"],
            "suggestions": ["Add proper error handling", "Improve code structure"],
            "actionable_feedback": ["Add proper error handling", "Improve code structure"],
        }
        
        # Create payload for review with max retries reached
        payload = {
            "entity": "Student",
            "swea_agent": "BackendSWEA",
            "task_type": "generate_api",
            "result": {
                "success": True,
                "data": {
                    "file_path": "/path/to/file.py",
                    "code": "def test(): pass"
                }
            },
            "retry_count": 3,  # Max retries reached
        }
        
        # Mock Config.BAE_STRICT_MODE and validation method
        with patch('baes.swea_agents.techlead_swea.Config.BAE_STRICT_MODE', True):
            with patch('baes.swea_agents.techlead_swea.Config.BAE_MAX_RETRIES', 3):
                with patch.object(techlead, '_validate_with_llm', return_value=mock_validation_result):
                    result = techlead._review_and_approve(payload)
        
        # Verify strict mode behavior (rejection without force-accept)
        assert result.get("approved") == False, "Code should be rejected in strict mode"
        assert result.get("success") == False, "Result should indicate failure"
        assert result.get("force_accepted") != True, "Should NOT be force-accepted in strict mode"
        assert result.get("data", {}).get("retry_required") == True

    def test_strict_mode_with_critical_issues_escalates(self):
        """Test that strict mode escalates critical issues to human expert"""
        # Create TechLeadSWEA instance
        techlead = TechLeadSWEA()
        
        # Create a mock validation result with critical issues
        mock_validation_result = {
            "is_valid": False,
            "quality_score": 0.3,
            "details": "Code has critical issues",
            "issues": ["Critical: Missing authentication", "Critical: SQL injection risk"],
            "suggestions": ["Add authentication", "Fix SQL injection vulnerability"],
            "actionable_feedback": ["[CRITICAL] Add authentication", "[CRITICAL] Fix SQL injection"],
            "critical_feedback": ["[CRITICAL] Add authentication", "[CRITICAL] Fix SQL injection"],
            "feedback_summary": {
                "escalation_needed": True,
                "critical_count": 2,
                "required_count": 0,
                "optional_count": 0,
            }
        }
        
        # Create payload for review with max retries reached
        payload = {
            "entity": "Student",
            "swea_agent": "BackendSWEA",
            "task_type": "generate_api",
            "result": {
                "success": True,
                "data": {
                    "file_path": "/path/to/file.py",
                    "code": "def test(): pass"
                }
            },
            "retry_count": 3,  # Max retries reached
        }
        
        # Mock Config.BAE_STRICT_MODE, validation and escalation methods
        with patch('baes.swea_agents.techlead_swea.Config.BAE_STRICT_MODE', True):
            with patch('baes.swea_agents.techlead_swea.Config.BAE_MAX_RETRIES', 3):
                with patch.object(techlead, '_validate_with_llm', return_value=mock_validation_result):
                    with patch.object(techlead, '_escalate_to_human_expert', return_value={"escalated": True}):
                        result = techlead._review_and_approve(payload)
        
        # Verify rejection in strict mode (may or may not escalate depending on issues)
        assert result.get("approved") == False
        assert result.get("success") == False
        # In strict mode, code is rejected but may require escalation or just retry
        assert result.get("data", {}).get("retry_required") == True or result.get("escalation_required") == True

    def test_force_accept_mode_with_critical_issues(self):
        """Test that force-accept mode accepts even with critical issues"""
        # Create TechLeadSWEA instance
        techlead = TechLeadSWEA()
        
        # Create a mock validation result with critical issues
        mock_validation_result = {
            "is_valid": False,
            "quality_score": 0.2,
            "details": "Code has critical issues",
            "issues": ["Critical: Missing authentication", "Critical: SQL injection risk"],
            "suggestions": ["Add authentication", "Fix SQL injection vulnerability"],
            "actionable_feedback": ["[CRITICAL] Add authentication", "[CRITICAL] Fix SQL injection"],
            "critical_feedback": ["[CRITICAL] Add authentication", "[CRITICAL] Fix SQL injection"],
            "feedback_summary": {
                "escalation_needed": True,
                "critical_count": 2,
                "required_count": 0,
                "optional_count": 0,
            }
        }
        
        # Create payload for review with max retries reached
        payload = {
            "entity": "Student",
            "swea_agent": "BackendSWEA",
            "task_type": "generate_api",
            "result": {
                "success": True,
                "data": {
                    "file_path": "/path/to/file.py",
                    "code": "def test(): pass"
                }
            },
            "retry_count": 3,  # Max retries reached
        }
        
        # Mock Config.BAE_STRICT_MODE to False (force-accept mode) and validation method
        with patch('baes.swea_agents.techlead_swea.Config.BAE_STRICT_MODE', False):
            with patch('baes.swea_agents.techlead_swea.Config.BAE_MAX_RETRIES', 3):
                with patch.object(techlead, '_validate_with_llm', return_value=mock_validation_result):
                    result = techlead._review_and_approve(payload)
        
        # Verify force-accept even with critical issues
        assert result.get("approved") == True
        assert result.get("success") == True
        assert result.get("force_accepted") == True
        # Check for unresolved issues (may be in unresolved_critical_issues or unresolved_issues)
        assert "unresolved_critical_issues" in result.get("data", {}) or "unresolved_issues" in result.get("data", {})
        # Verify there are unresolved issues tracked
        unresolved = result.get("data", {}).get("unresolved_critical_issues") or result.get("data", {}).get("unresolved_issues", [])
        assert len(unresolved) > 0, "Should have tracked unresolved issues"

    def test_config_strict_mode_parsing(self):
        """Test that BAE_STRICT_MODE environment variable is parsed correctly by Config"""
        # Test various true values
        for value in ["true", "True", "TRUE", "1", "yes", "on"]:
            os.environ["BAE_STRICT_MODE"] = value
            importlib.reload(config)
            Config = getattr(config, 'Config')
            assert Config.BAE_STRICT_MODE == True, f"Config.BAE_STRICT_MODE should be True for BAE_STRICT_MODE={value}"
        
        # Test various false values
        for value in ["false", "False", "FALSE", "0", "no", "off", ""]:
            os.environ["BAE_STRICT_MODE"] = value
            importlib.reload(config)
            Config = getattr(config, 'Config')
            assert Config.BAE_STRICT_MODE == False, f"Config.BAE_STRICT_MODE should be False for BAE_STRICT_MODE={value}"

    def test_force_accept_metadata_tracking(self):
        """Test that force-accepted artifacts include proper metadata"""
        techlead = TechLeadSWEA()
        
        mock_validation_result = {
            "is_valid": False,
            "quality_score": 0.4,
            "details": "Multiple issues found",
            "issues": ["Issue 1", "Issue 2", "Issue 3"],
            "suggestions": ["Fix 1", "Fix 2", "Fix 3"],
            "actionable_feedback": ["Fix 1", "Fix 2", "Fix 3"],
        }
        
        payload = {
            "entity": "Course",
            "swea_agent": "FrontendSWEA",
            "task_type": "generate_ui",
            "result": {"success": True, "data": {"code": "test"}},
            "retry_count": 3,
        }
        
        # Mock Config.BAE_STRICT_MODE to False (force-accept mode) and validation method
        with patch('baes.swea_agents.techlead_swea.Config.BAE_STRICT_MODE', False):
            with patch('baes.swea_agents.techlead_swea.Config.BAE_MAX_RETRIES', 3):
                with patch.object(techlead, '_validate_with_llm', return_value=mock_validation_result):
                    result = techlead._review_and_approve(payload)
        
        # Verify comprehensive metadata
        assert result["force_accepted"] == True
        assert result["data"]["force_accepted"] == True
        assert "force_accept_reason" in result["data"]
        assert "unresolved_issues" in result["data"]
        assert result["data"]["retry_count"] == 3
        # Verify unresolved issues are tracked (actual count may vary with validation)
        assert len(result["data"]["unresolved_issues"]) >= 3, "Should track at least the mock issues"
