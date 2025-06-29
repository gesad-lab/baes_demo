"""
Test Stage 3 Improvement #4: Feedback Categorization and Routing

Tests TechLeadSWEA's ability to:
1. Categorize feedback with priority levels (CRITICAL/REQUIRED/OPTIONAL)
2. Route actionable feedback (CRITICAL + REQUIRED) to SWEA agents
3. Ignore OPTIONAL feedback appropriately
4. Escalate unresolvable CRITICAL issues to Human Expert
"""

import json
import os
import pytest
from unittest.mock import Mock, patch

from baes.swea_agents.techlead_swea import TechLeadSWEA
from baes.swea_agents.backend_swea import BackendSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.database_swea import DatabaseSWEA


class TestFeedbackCategorization:
    """Test feedback categorization and priority-based routing"""

    def setup_method(self):
        """Setup test environment"""
        self.techlead = TechLeadSWEA()
        self.backend = BackendSWEA()
        self.frontend = FrontendSWEA()
        self.database = DatabaseSWEA()

    def test_categorized_feedback_processing(self):
        """Test that TechLeadSWEA processes categorized feedback correctly"""
        # Mock LLM response with categorized feedback
        mock_llm_response = json.dumps({
            "is_valid": False,
            "quality_score": 0.4,
            "details": "Multiple issues found requiring fixes",
            "issues": [
                "Empty class definition found",
                "Missing error handling in API routes",
                "Code style inconsistencies"
            ],
            "suggestions": [
                "Add field definitions to empty classes",
                "Implement try/catch blocks",
                "Follow PEP 8 naming conventions"
            ],
            "categorized_feedback": [
                {
                    "priority": "CRITICAL",
                    "issue": "Empty class definition prevents system from working",
                    "fix": "Add field definitions with proper types (e.g., name: str, age: int)"
                },
                {
                    "priority": "REQUIRED",
                    "issue": "Missing error handling affects functionality",
                    "fix": "Add try/except blocks with HTTPException for all database operations"
                },
                {
                    "priority": "OPTIONAL",
                    "issue": "Code style inconsistencies",
                    "fix": "Follow PEP 8 naming conventions for better readability"
                }
            ]
        })

        with patch.object(self.techlead.llm_client, 'generate_response', return_value=mock_llm_response):
            validation_result = self.techlead._validate_code_artifact(
                entity="Student",
                swea_agent="BackendSWEA",
                task_type="generate_model",
                result={"code": "class Student: pass", "file_path": "models/student.py"}
            )

        # Verify categorized feedback was processed
        assert "categorized_feedback" in validation_result
        assert "critical_feedback" in validation_result
        assert "required_feedback" in validation_result
        assert "optional_feedback" in validation_result
        assert "actionable_feedback" in validation_result

        # Verify feedback categorization
        critical_feedback = validation_result["critical_feedback"]
        required_feedback = validation_result["required_feedback"]
        optional_feedback = validation_result["optional_feedback"]
        actionable_feedback = validation_result["actionable_feedback"]

        assert len(critical_feedback) == 1
        assert len(required_feedback) == 1
        assert len(optional_feedback) == 1
        assert len(actionable_feedback) == 2  # CRITICAL + REQUIRED

        # Verify feedback summary
        feedback_summary = validation_result["feedback_summary"]
        assert feedback_summary["critical_count"] == 1
        assert feedback_summary["required_count"] == 1
        assert feedback_summary["optional_count"] == 1
        assert feedback_summary["actionable_count"] == 2
        assert feedback_summary["routing_strategy"] == "handle_critical_and_required"

    def test_escalation_detection(self):
        """Test that escalation is detected for complex CRITICAL issues"""
        critical_feedback = [
            {
                "priority": "CRITICAL",
                "issue": "Security vulnerability in database connection handling",
                "fix": "Implement proper connection security measures"
            },
            {
                "priority": "CRITICAL",
                "issue": "Memory leak detected in data processing",
                "fix": "Review memory management architecture"
            }
        ]

        escalation_needed = self.techlead._check_escalation_needed(critical_feedback)
        assert escalation_needed is True

    def test_no_escalation_for_simple_critical_issues(self):
        """Test that simple CRITICAL issues don't trigger escalation"""
        critical_feedback = [
            {
                "priority": "CRITICAL",
                "issue": "Empty class definition found",
                "fix": "Add field definitions with proper types"
            }
        ]

        escalation_needed = self.techlead._check_escalation_needed(critical_feedback)
        assert escalation_needed is False

    def test_human_expert_escalation_report(self):
        """Test Human Expert escalation report generation"""
        critical_issues = [
            {
                "priority": "CRITICAL",
                "issue": "System architecture conflict requiring manual intervention",
                "fix": "Redesign data flow architecture with expert guidance"
            }
        ]

        escalation_report = self.techlead._escalate_to_human_expert("Student", critical_issues, 3)

        # Verify escalation report structure
        assert escalation_report["escalation_type"] == "human_expert_required"
        assert escalation_report["entity"] == "Student"
        assert escalation_report["critical_issues_count"] == 1
        assert escalation_report["retry_attempts"] == 3
        assert escalation_report["max_retries_reached"] is True
        assert escalation_report["human_expert_guidance_needed"] is True
        assert escalation_report["system_generation_paused"] is True

        # Verify recommended actions
        recommended_actions = escalation_report["recommended_actions"]
        assert len(recommended_actions) == 1
        assert recommended_actions[0]["complexity"] == "high"
        assert recommended_actions[0]["requires_architecture_decision"] is True

    def test_review_with_escalation_trigger(self):
        """Test that review triggers escalation when max retries reached with CRITICAL issues"""
        # Mock validation result with CRITICAL issues and escalation needed
        mock_validation_result = {
            "is_valid": False,
            "quality_score": 0.2,
            "details": "Critical issues found",
            "issues": ["System architecture conflict"],
            "suggestions": ["Redesign architecture"],
            "critical_feedback": [
                {
                    "priority": "CRITICAL",
                    "issue": "System architecture conflict",
                    "fix": "Redesign with expert guidance"
                }
            ],
            "required_feedback": [],
            "optional_feedback": [],
            "actionable_feedback": [
                "[CRITICAL] Redesign with expert guidance"
            ],
            "feedback_summary": {
                "critical_count": 1,
                "required_count": 0,
                "optional_count": 0,
                "actionable_count": 1,
                "escalation_needed": True,
                "routing_strategy": "handle_critical_and_required"
            }
        }

        with patch.object(self.techlead, '_validate_generated_artifact', return_value=mock_validation_result):
            with patch.object(self.techlead, '_escalate_to_human_expert') as mock_escalate:
                mock_escalate.return_value = {"escalation_type": "human_expert_required"}

                # Set max retries to 3 and test with retry_count = 3
                with patch.dict(os.environ, {"BAE_MAX_RETRIES": "3"}):
                    result = self.techlead._review_and_approve({
                        "entity": "Student",
                        "swea_agent": "BackendSWEA",
                        "task_type": "generate_model",
                        "result": {"code": "class Student: pass"},
                        "retry_count": 3  # Max retries reached
                    })

                # Verify escalation was triggered
                assert result["escalation_required"] is True
                assert "escalation_report" in result
                assert result["data"]["human_expert_required"] is True
                assert result["data"]["retry_required"] is False
                mock_escalate.assert_called_once()

    def test_backend_swea_priority_feedback_handling(self):
        """Test that BackendSWEA handles priority-based feedback correctly"""
        # Mock feedback with mixed priorities
        feedback = [
            "[CRITICAL] Empty class definition prevents system from working",
            "[REQUIRED] Missing error handling affects functionality", 
            "[OPTIONAL] Code style improvements for better readability"
        ]

        # Mock LLM response that processes priorities correctly
        mock_llm_response = json.dumps({
            "attributes": ["name:str", "email:str", "age:int"],
            "additional_requirements": ["Add error handling", "Implement field validation"],
            "code_improvements": ["Add try/catch blocks", "Implement proper types"],
            "modifications": ["Fix empty class", "Add error handling"],
            "explanation": "Processed CRITICAL and REQUIRED feedback, ignored OPTIONAL"
        })

        with patch.object(self.backend.llm_client, 'generate_response', return_value=mock_llm_response):
            interpretation = self.backend._interpret_feedback_for_backend_generation(
                feedback=feedback,
                entity="Student",
                code_type="Pydantic Model",
                original_attributes=["name:str"]
            )

        # Verify interpretation focused on actionable feedback
        assert "name:str" in interpretation["attributes"]
        assert "email:str" in interpretation["attributes"] 
        assert "age:int" in interpretation["attributes"]
        assert len(interpretation["additional_requirements"]) > 0
        assert len(interpretation["code_improvements"]) > 0

    def test_frontend_swea_priority_feedback_handling(self):
        """Test that FrontendSWEA handles priority-based feedback correctly"""
        feedback = [
            "[CRITICAL] Missing main() function prevents UI from loading",
            "[REQUIRED] Add form validation for user input",
            "[OPTIONAL] Improve color scheme for better aesthetics"
        ]

        # Mock LLM response
        mock_llm_response = json.dumps({
            "attributes": ["name:str", "email:str"],
            "ui_improvements": ["Add main() function", "Implement form validation"],
            "layout_changes": ["Add proper form structure"],
            "modifications": ["Fix missing main function", "Add validation"],
            "explanation": "Focused on CRITICAL and REQUIRED issues only"
        })

        with patch.object(self.frontend.llm_client, 'generate_response', return_value=mock_llm_response):
            interpretation = self.frontend._interpret_feedback_for_ui_generation(
                feedback=feedback,
                entity="Student",
                original_attributes=["name:str"]
            )

        # Verify interpretation handled priorities
        assert len(interpretation["ui_improvements"]) > 0
        assert "main() function" in str(interpretation["ui_improvements"])
        assert "validation" in str(interpretation["ui_improvements"])

    def test_database_swea_priority_feedback_handling(self):
        """Test that DatabaseSWEA handles priority-based feedback correctly"""
        feedback = [
            "[CRITICAL] Missing primary key constraint causes data integrity issues",
            "[REQUIRED] Add NOT NULL constraints for required fields",
            "[OPTIONAL] Consider adding indexes for better performance"
        ]

        # Mock LLM response
        mock_llm_response = json.dumps({
            "attributes": ["id:int", "name:str", "email:str"],
            "additional_requirements": ["Add primary key", "Add NOT NULL constraints"],
            "constraints": ["PRIMARY KEY", "NOT NULL"],
            "modifications": ["Fix primary key", "Add constraints"],
            "explanation": "Addressed CRITICAL and REQUIRED database issues"
        })

        with patch.object(self.database.llm_client, 'generate_response', return_value=mock_llm_response):
            interpretation = self.database._interpret_feedback_for_database_setup(
                feedback=feedback,
                entity="Student",
                original_attributes=["name:str"]
            )

        # Verify interpretation prioritized correctly
        assert "id:int" in interpretation["attributes"]
        assert len(interpretation["constraints"]) > 0
        assert "PRIMARY KEY" in interpretation["constraints"]

    def test_feedback_analytics_integration(self):
        """Test that feedback categorization integrates with analytics"""
        # This test verifies that the analytics system can track categorized feedback
        mock_llm_response = json.dumps({
            "is_valid": False,
            "quality_score": 0.5,
            "details": "Issues found",
            "issues": ["Test issue"],
            "suggestions": ["Test suggestion"],
            "categorized_feedback": [
                {
                    "priority": "CRITICAL",
                    "issue": "Critical test issue",
                    "fix": "Critical fix"
                },
                {
                    "priority": "REQUIRED", 
                    "issue": "Required test issue",
                    "fix": "Required fix"
                }
            ]
        })

        with patch.object(self.techlead.llm_client, 'generate_response', return_value=mock_llm_response):
            validation_result = self.techlead._validate_code_artifact(
                entity="Student",
                swea_agent="BackendSWEA", 
                task_type="generate_model",
                result={"code": "test code", "file_path": "test.py"}
            )

        # Verify feedback summary is available for analytics
        feedback_summary = validation_result.get("feedback_summary", {})
        assert feedback_summary["critical_count"] == 1
        assert feedback_summary["required_count"] == 1
        assert feedback_summary["actionable_count"] == 2


class TestFeedbackPriorityScenarios:
    """Test various feedback priority scenarios"""

    def setup_method(self):
        self.techlead = TechLeadSWEA()

    def test_all_critical_feedback(self):
        """Test scenario with only CRITICAL feedback"""
        categorized_feedback = [
            {"priority": "CRITICAL", "issue": "Issue 1", "fix": "Fix 1"},
            {"priority": "CRITICAL", "issue": "Issue 2", "fix": "Fix 2"}
        ]

        validation_response = {"categorized_feedback": categorized_feedback}
        result = self.techlead._process_categorized_feedback(validation_response)

        assert len(result["critical_feedback"]) == 2
        assert len(result["required_feedback"]) == 0
        assert len(result["optional_feedback"]) == 0
        assert len(result["actionable_feedback"]) == 2

    def test_all_optional_feedback(self):
        """Test scenario with only OPTIONAL feedback"""
        categorized_feedback = [
            {"priority": "OPTIONAL", "issue": "Style issue", "fix": "Style fix"},
            {"priority": "OPTIONAL", "issue": "Enhancement", "fix": "Enhancement fix"}
        ]

        validation_response = {"categorized_feedback": categorized_feedback}
        result = self.techlead._process_categorized_feedback(validation_response)

        assert len(result["critical_feedback"]) == 0
        assert len(result["required_feedback"]) == 0
        assert len(result["optional_feedback"]) == 2
        assert len(result["actionable_feedback"]) == 0  # Only OPTIONAL, so no actionable items

    def test_mixed_priority_feedback(self):
        """Test scenario with mixed priority feedback"""
        categorized_feedback = [
            {"priority": "CRITICAL", "issue": "Critical issue", "fix": "Critical fix"},
            {"priority": "REQUIRED", "issue": "Required issue", "fix": "Required fix"},
            {"priority": "OPTIONAL", "issue": "Optional issue", "fix": "Optional fix"},
            {"priority": "REQUIRED", "issue": "Another required", "fix": "Another fix"}
        ]

        validation_response = {"categorized_feedback": categorized_feedback}
        result = self.techlead._process_categorized_feedback(validation_response)

        assert len(result["critical_feedback"]) == 1
        assert len(result["required_feedback"]) == 2
        assert len(result["optional_feedback"]) == 1
        assert len(result["actionable_feedback"]) == 3  # 1 CRITICAL + 2 REQUIRED

        # Verify actionable feedback includes both CRITICAL and REQUIRED
        actionable_priorities = [item.get("priority") for item in result["actionable_feedback"]]
        assert "CRITICAL" in actionable_priorities
        assert actionable_priorities.count("REQUIRED") == 2

    def test_invalid_priority_defaults_to_required(self):
        """Test that invalid priority defaults to REQUIRED"""
        categorized_feedback = [
            {"priority": "INVALID", "issue": "Issue with invalid priority", "fix": "Fix"},
            {"issue": "Issue without priority", "fix": "Fix"}  # Missing priority
        ]

        validation_response = {"categorized_feedback": categorized_feedback}
        result = self.techlead._process_categorized_feedback(validation_response)

        assert len(result["critical_feedback"]) == 0
        assert len(result["required_feedback"]) == 2  # Both defaulted to REQUIRED
        assert len(result["optional_feedback"]) == 0
        assert len(result["actionable_feedback"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 