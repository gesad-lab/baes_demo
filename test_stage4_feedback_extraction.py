#!/usr/bin/env python3
"""
Test Stage 4 Improvement #1: Structured Feedback Extraction and Prompt Injection

Tests TechLeadSWEA's ability to:
1. Extract ALL suggestions from feedback with original reasoning
2. Store feedback for reuse across retry attempts
3. Inject structured feedback into SWEA agent prompts
4. Clear feedback storage on successful approval
"""

import sys
from pathlib import Path

from baes.swea_agents.backend_swea import BackendSWEA
from baes.swea_agents.database_swea import DatabaseSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.techlead_swea import TechLeadSWEA

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))


def test_feedback_extraction():
    """Test that TechLeadSWEA extracts ALL suggestions from feedback"""
    techlead = TechLeadSWEA()

    # Create mock validation result with multiple feedback sources
    validation_result = {
        "details": "The generated code has several critical issues that need immediate attention.",
        "categorized_feedback": [
            {
                "priority": "CRITICAL",
                "issue": "Database connection not properly managed",
                "fix": "Use context manager pattern for database connections",
            },
            {
                "priority": "REQUIRED",
                "issue": "Missing error handling",
                "fix": "Add try/except blocks around database operations",
            },
        ],
        "suggestions": ["Add proper HTTP status codes", "Implement input validation"],
        "fix_instructions": ["Fix the import statements", "Add proper return types"],
        "issues": ["Empty function implementation", "Missing docstrings"],
    }

    # Extract structured feedback
    extracted = techlead._extract_structured_feedback(
        validation_result, "Student", "BackendSWEA", "generate_api"
    )

    # Verify all suggestions were extracted
    assert (
        len(extracted["all_suggestions"]) == 8
    ), f"Expected 8 suggestions, got {len(extracted['all_suggestions'])}"

    # Verify original reasoning was preserved
    assert "critical issues that need immediate attention" in extracted["original_reasoning"]

    # Verify structured instructions were created
    assert "PREVIOUS FEEDBACK TO ADDRESS:" in extracted["structured_instructions"]
    assert (
        "MANDATORY: You MUST address ALL the above feedback" in extracted["structured_instructions"]
    )

    # Verify priority emojis are present
    assert "🚨 [CRITICAL]" in extracted["structured_instructions"]
    assert "⚠️ [REQUIRED]" in extracted["structured_instructions"]

    print("✅ Feedback extraction test passed")


def test_feedback_storage_and_retrieval():
    """Test feedback storage and retrieval across retry attempts"""
    techlead = TechLeadSWEA()

    # Create mock extracted feedback
    extracted_feedback = {
        "entity": "Student",
        "swea_agent": "BackendSWEA",
        "task_type": "generate_api",
        "all_suggestions": [
            {
                "priority": "CRITICAL",
                "fix": "Fix database connections",
                "source": "categorized_feedback",
            }
        ],
        "original_reasoning": "Critical database issues found",
        "structured_instructions": "PREVIOUS FEEDBACK TO ADDRESS:\n1. 🚨 [CRITICAL] Fix database connections",
    }

    # Store feedback
    techlead._store_feedback_for_reuse(extracted_feedback)

    # Verify feedback was stored
    assert hasattr(techlead, "feedback_storage")
    assert "Student_BackendSWEA_generate_api" in techlead.feedback_storage

    # Retrieve feedback
    retrieved = techlead._retrieve_feedback_for_injection("Student", "BackendSWEA", "generate_api")

    # Verify feedback was retrieved correctly
    assert "PREVIOUS FEEDBACK TO ADDRESS:" in retrieved
    assert "🚨 [CRITICAL] Fix database connections" in retrieved

    # Test retrieval for non-existent feedback
    empty_retrieved = techlead._retrieve_feedback_for_injection(
        "Student", "FrontendSWEA", "generate_ui"
    )
    assert empty_retrieved == ""

    print("✅ Feedback storage and retrieval test passed")


def test_feedback_clearance():
    """Test feedback storage clearance on successful approval"""
    techlead = TechLeadSWEA()

    # Store some feedback
    extracted_feedback = {
        "entity": "Student",
        "swea_agent": "BackendSWEA",
        "task_type": "generate_api",
        "all_suggestions": [],
        "original_reasoning": "Test feedback",
        "structured_instructions": "Test instructions",
    }

    techlead._store_feedback_for_reuse(extracted_feedback)
    assert len(techlead.feedback_storage) == 1

    # Clear specific feedback
    techlead._clear_feedback_storage("Student", "BackendSWEA", "generate_api")
    assert len(techlead.feedback_storage) == 0

    # Test clearing all feedback
    techlead._store_feedback_for_reuse(extracted_feedback)
    techlead._clear_feedback_storage()  # Clear all
    assert len(techlead.feedback_storage) == 0

    print("✅ Feedback clearance test passed")


def test_swea_agent_integration():
    """Test that SWEA agents can retrieve structured feedback"""
    # Test BackendSWEA
    backend = BackendSWEA()
    backend_feedback = backend._get_structured_feedback_injection(
        "Student", "BackendSWEA", "generate_api"
    )
    # Should be empty initially, but method should work
    assert isinstance(backend_feedback, str)

    # Test FrontendSWEA
    frontend = FrontendSWEA()
    frontend_feedback = frontend._get_structured_feedback_injection(
        "Student", "FrontendSWEA", "generate_ui"
    )
    assert isinstance(frontend_feedback, str)

    # Test DatabaseSWEA
    database = DatabaseSWEA()
    database_feedback = database._get_structured_feedback_injection(
        "Student", "DatabaseSWEA", "setup_database"
    )
    assert isinstance(database_feedback, str)

    print("✅ SWEA agent integration test passed")


def test_feedback_injection_in_prompts():
    """Test that structured feedback is injected into SWEA prompts"""
    # Setup: Store feedback in TechLeadSWEA
    techlead = TechLeadSWEA()
    extracted_feedback = {
        "entity": "Student",
        "swea_agent": "BackendSWEA",
        "task_type": "generate_api",
        "all_suggestions": [
            {
                "priority": "CRITICAL",
                "fix": "Fix database connections",
                "source": "categorized_feedback",
            }
        ],
        "original_reasoning": "Critical database issues found",
        "structured_instructions": "PREVIOUS FEEDBACK TO ADDRESS:\n1. 🚨 [CRITICAL] Fix database connections\n\nMANDATORY: You MUST address ALL the above feedback in your response.",
    }
    techlead._store_feedback_for_reuse(extracted_feedback)

    # Test: BackendSWEA should retrieve and include feedback in prompt
    backend = BackendSWEA()
    feedback = backend._get_structured_feedback_injection("Student", "BackendSWEA", "generate_api")

    # Verify feedback was retrieved
    assert "PREVIOUS FEEDBACK TO ADDRESS:" in feedback
    assert "🚨 [CRITICAL] Fix database connections" in feedback
    assert "MANDATORY: You MUST address ALL the above feedback" in feedback

    print("✅ Feedback injection in prompts test passed")


def main():
    """Run all Stage 4 tests"""
    print("🧪 Testing Stage 4: Structured Feedback Extraction and Prompt Injection")
    print("=" * 70)

    try:
        test_feedback_extraction()
        test_feedback_storage_and_retrieval()
        test_feedback_clearance()
        test_swea_agent_integration()
        test_feedback_injection_in_prompts()

        print("\n🎉 ALL STAGE 4 TESTS PASSED!")
        print("✅ Structured feedback extraction working correctly")
        print("✅ Feedback storage and retrieval functional")
        print("✅ Feedback clearance on success working")
        print("✅ All SWEA agents integrated with feedback injection")
        print("✅ Prompt injection with structured feedback working")

    except Exception as e:
        print(f"\n❌ STAGE 4 TEST FAILED: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
