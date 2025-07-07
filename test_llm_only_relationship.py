#!/usr/bin/env python3
"""
Test script to verify LLM-only relationship detection without fixed patterns.
This tests that the system correctly distinguishes between attributes and entities.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from baes.domain_entities.academic.student_bae import StudentBae
from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel

def test_llm_only_relationship_detection():
    """Test LLM-only relationship detection with various requests"""
    
    print("🧠 Testing LLM-Only Relationship Detection")
    print("=" * 60)
    
    # Initialize BAE
    student_bae = StudentBae()
    
    # Test cases that should be correctly classified
    test_cases = [
        # Relationship requests (should be detected as relationships)
        {
            "request": "add course to student entity",
            "expected_type": "relationship",
            "description": "Clear relationship request"
        },
        {
            "request": "connect teacher with student",
            "expected_type": "relationship", 
            "description": "Relationship between entities"
        },
        {
            "request": "link course to student",
            "expected_type": "relationship",
            "description": "Another relationship pattern"
        },
        
        # Attribute requests (should NOT be detected as relationships)
        {
            "request": "add age to student entity",
            "expected_type": "evolve",
            "description": "Adding attribute to entity"
        },
        {
            "request": "add birth date to student",
            "expected_type": "evolve", 
            "description": "Adding date attribute"
        },
        {
            "request": "include grade point average in student",
            "expected_type": "evolve",
            "description": "Adding GPA attribute"
        },
        
        # Entity creation requests
        {
            "request": "create a new student entity",
            "expected_type": "create",
            "description": "Entity creation request"
        },
        {
            "request": "add student entity to system",
            "expected_type": "create",
            "description": "Another creation pattern"
        }
    ]
    
    print("\n🧪 Testing LLM interpretation for various requests:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        request = test_case["request"]
        expected_type = test_case["expected_type"]
        description = test_case["description"]
        
        print(f"\n{i}. Testing: '{request}'")
        print(f"   Expected: {expected_type} ({description})")
        
        try:
            # Test the LLM interpretation directly
            interpretation_result = student_bae.handle(
                "interpret_business_request",
                {
                    "request": request,
                    "context": "academic"
                }
            )
            
            if "error" in interpretation_result:
                print(f"   ❌ Error: {interpretation_result['error']}")
                continue
                
            # Extract the operation type from the result
            operation_type = interpretation_result.get("request_type", "unknown")
            is_relationship = interpretation_result.get("is_relationship", False)
            
            print(f"   🔍 LLM detected: operation_type='{operation_type}', is_relationship={is_relationship}")
            
            # Check if the detection was correct
            if expected_type == "relationship":
                if is_relationship or operation_type == "relationship":
                    print(f"   ✅ CORRECT: Relationship detected as expected")
                else:
                    print(f"   ❌ INCORRECT: Expected relationship but got {operation_type}")
            elif expected_type == "evolve":
                if operation_type == "evolve" and not is_relationship:
                    print(f"   ✅ CORRECT: Evolution detected as expected")
                else:
                    print(f"   ❌ INCORRECT: Expected evolution but got {operation_type} (relationship={is_relationship})")
            elif expected_type == "create":
                if operation_type == "create" and not is_relationship:
                    print(f"   ✅ CORRECT: Creation detected as expected")
                else:
                    print(f"   ❌ INCORRECT: Expected creation but got {operation_type} (relationship={is_relationship})")
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🧠 LLM-Only Relationship Detection Test Complete")
    print("💡 The system now relies entirely on LLM intelligence for relationship detection")
    print("💡 No fixed patterns are used - this provides maximum flexibility")

if __name__ == "__main__":
    test_llm_only_relationship_detection() 