#!/usr/bin/env python3
"""
Test FrontendSWEA feedback retrieval and prompt injection
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.techlead_swea import TechLeadSWEA

def test_frontend_feedback_retrieval():
    """Test that FrontendSWEA can retrieve structured feedback from TechLeadSWEA"""
    
    # Create instances
    frontend = FrontendSWEA()
    techlead = TechLeadSWEA()
    
    # Create mock validation result with frontend-specific issues
    validation_result = {
        "details": "Frontend code failed validation due to missing critical components",
        "categorized_feedback": [
            {
                "priority": "CRITICAL",
                "issue": "Missing st.set_page_config()",
                "fix": "Add st.set_page_config() at the beginning of the file",
            },
            {
                "priority": "REQUIRED",
                "issue": "Missing API_BASE_URL",
                "fix": "Define API_BASE_URL = \"http://localhost:8000\"",
            },
            {
                "priority": "REQUIRED",
                "issue": "Missing error handling",
                "fix": "Add response.raise_for_status() after API calls",
            },
        ],
        "suggestions": [
            "Add proper error handling with try/except blocks",
            "Include form validation with st.error() messages",
        ],
        "issues": [
            "Exception handling without error logging",
            "Functions missing docstrings",
            "Functions missing return type hints",
        ],
    }
    
    # Extract and store feedback
    extracted_feedback = techlead._extract_structured_feedback(
        validation_result, "Student", "FrontendSWEA", "generate_ui"
    )
    techlead._store_feedback_for_reuse(extracted_feedback)
    
    print("📋 Extracted feedback:")
    print(f"   Total suggestions: {len(extracted_feedback['all_suggestions'])}")
    print(f"   Structured instructions length: {len(extracted_feedback['structured_instructions'])}")
    print(f"   Instructions preview: {extracted_feedback['structured_instructions'][:100]}...")
    
    # Test FrontendSWEA retrieval
    retrieved_feedback = frontend._get_structured_feedback_injection(
        "Student", "FrontendSWEA", "generate_ui"
    )
    
    print(f"\n📤 FrontendSWEA retrieved feedback:")
    print(f"   Length: {len(retrieved_feedback)}")
    print(f"   Content: {retrieved_feedback}")
    
    # Test prompt building with feedback
    prompt = frontend._build_prompt("Student", ["name:str", "email:str"], "academic")
    
    print(f"\n📝 Generated prompt length: {len(prompt)}")
    print(f"   Contains structured feedback: {'structured_feedback' in prompt}")
    print(f"   Contains feedback content: {'PREVIOUS FEEDBACK TO ADDRESS:' in prompt}")
    
    # Check if feedback is properly injected
    if "PREVIOUS FEEDBACK TO ADDRESS:" in prompt:
        print("✅ Feedback properly injected into prompt")
    else:
        print("❌ Feedback not found in prompt")
        
    return "PREVIOUS FEEDBACK TO ADDRESS:" in prompt

if __name__ == "__main__":
    print("🧪 Testing FrontendSWEA Feedback Retrieval")
    print("=" * 50)
    
    success = test_frontend_feedback_retrieval()
    
    if success:
        print("\n✅ FrontendSWEA feedback retrieval test PASSED")
    else:
        print("\n❌ FrontendSWEA feedback retrieval test FAILED") 