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
        # CRITICAL Relationship requests (should be detected as relationships)
        {
            "request": "add course to student entity",
            "expected_type": "relationship",
            "expected_target": "student",
            "expected_related": "course",
            "description": "Critical: Primary relationship pattern"
        },
        {
            "request": "add a course to the student entity", 
            "expected_type": "relationship",
            "expected_target": "student",
            "expected_related": "course",
            "description": "Critical: Variant of primary relationship pattern"
        },
        {
            "request": "connect teacher with course",
            "expected_type": "relationship", 
            "expected_target": "course",
            "expected_related": "teacher", 
            "description": "Connect relationship pattern"
        },
        {
            "request": "link course to student",
            "expected_type": "relationship",
            "expected_target": "student",
            "expected_related": "course",
            "description": "Link relationship pattern"
        },
        {
            "request": "enroll student in course",
            "expected_type": "relationship",
            "expected_target": "student", 
            "expected_related": "course",
            "description": "Enroll relationship pattern"
        },
        {
            "request": "assign teacher to course",
            "expected_type": "relationship",
            "expected_target": "course",
            "expected_related": "teacher",
            "description": "Assign relationship pattern"
        },
        
        # Attribute requests (should NOT be detected as relationships)
        {
            "request": "add age to student entity",
            "expected_type": "evolve",
            "expected_target": None,
            "expected_related": None,
            "description": "Adding attribute to entity"
        },
        {
            "request": "add birth date to student",
            "expected_type": "evolve", 
            "expected_target": None,
            "expected_related": None,
            "description": "Adding date attribute"
        },
        {
            "request": "include grade point average in student",
            "expected_type": "evolve",
            "expected_target": None,
            "expected_related": None,
            "description": "Adding GPA attribute"
        },
        
        # Entity creation requests
        {
            "request": "create a new student entity",
            "expected_type": "create",
            "expected_target": None,
            "expected_related": None,
            "description": "Entity creation request"
        },
        {
            "request": "add student entity to system",
            "expected_type": "create",
            "expected_target": None,
            "expected_related": None,
            "description": "Another creation pattern"
        },
        {
            "request": "add student",
            "expected_type": "create",
            "expected_target": None,
            "expected_related": None,
            "description": "Simple entity creation"
        }
    ]
    
    print("\n🧪 Testing LLM interpretation for various requests:")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        request = test_case["request"]
        expected_type = test_case["expected_type"]
        expected_target = test_case.get("expected_target")
        expected_related = test_case.get("expected_related")
        description = test_case["description"]
        
        print(f"\n{i}. Testing: '{request}'")
        print(f"   Expected: {expected_type} ({description})")
        if expected_target and expected_related:
            print(f"   Expected entities: {expected_target} gets {expected_related}_id")
        
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
            target_entity = interpretation_result.get("target_entity")
            related_entity = interpretation_result.get("related_entity")
            confidence = interpretation_result.get("confidence", 0.0)
            
            print(f"   🔍 LLM detected: operation_type='{operation_type}', is_relationship={is_relationship}")
            print(f"   📊 Confidence: {confidence:.2f}")
            if is_relationship:
                print(f"   🔗 Entities: target='{target_entity}', related='{related_entity}'")
            
            # Check if the detection was correct
            test_passed = True
            
            if expected_type == "relationship":
                if is_relationship or operation_type == "relationship":
                    print(f"   ✅ CORRECT: Relationship detected as expected")
                    
                    # Verify entity assignment if specified
                    if expected_target and expected_related:
                        if (target_entity and target_entity.lower() == expected_target.lower() and
                            related_entity and related_entity.lower() == expected_related.lower()):
                            print(f"   ✅ CORRECT: Entity assignment matches expected")
                        else:
                            print(f"   ⚠️  WARNING: Entity assignment mismatch")
                            print(f"       Expected: {expected_target} gets {expected_related}_id")
                            print(f"       Got: {target_entity} gets {related_entity}_id")
                            test_passed = False
                else:
                    print(f"   ❌ INCORRECT: Expected relationship but got {operation_type}")
                    test_passed = False
                    
            elif expected_type == "evolve":
                if operation_type == "evolve" and not is_relationship:
                    print(f"   ✅ CORRECT: Evolution detected as expected")
                else:
                    print(f"   ❌ INCORRECT: Expected evolution but got {operation_type} (relationship={is_relationship})")
                    test_passed = False
                    
            elif expected_type == "create":
                if operation_type == "create" and not is_relationship:
                    print(f"   ✅ CORRECT: Creation detected as expected")
                else:
                    print(f"   ❌ INCORRECT: Expected creation but got {operation_type} (relationship={is_relationship})")
                    test_passed = False
            
            # Add to summary tracking
            if not hasattr(test_llm_only_relationship_detection, 'test_results'):
                test_llm_only_relationship_detection.test_results = []
            
            test_llm_only_relationship_detection.test_results.append({
                "test_number": i,
                "request": request,
                "expected_type": expected_type,
                "actual_type": operation_type,
                "is_relationship": is_relationship,
                "confidence": confidence,
                "passed": test_passed,
                "description": description
            })
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            if not hasattr(test_llm_only_relationship_detection, 'test_results'):
                test_llm_only_relationship_detection.test_results = []
            test_llm_only_relationship_detection.test_results.append({
                "test_number": i,
                "request": request,
                "expected_type": expected_type,
                "actual_type": "error",
                "is_relationship": False,
                "confidence": 0.0,
                "passed": False,
                "description": description,
                "error": str(e)
            })
    
    print("\n" + "=" * 60)
    print("🧠 LLM-Only Relationship Detection Test Complete")
    
    # Show test summary
    if hasattr(test_llm_only_relationship_detection, 'test_results'):
        results = test_llm_only_relationship_detection.test_results
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        relationship_tests = [r for r in results if r['expected_type'] == 'relationship']
        relationship_passed = sum(1 for r in relationship_tests if r['passed'])
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"   ❌ Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"   🔗 Relationship Detection: {relationship_passed}/{len(relationship_tests)} ({relationship_passed/len(relationship_tests)*100:.1f}%)")
        
        # Show confidence statistics
        valid_confidences = [r['confidence'] for r in results if r['confidence'] > 0]
        if valid_confidences:
            avg_confidence = sum(valid_confidences) / len(valid_confidences)
            print(f"   📈 Average Confidence: {avg_confidence:.2f}")
        
        # Show failures
        failures = [r for r in results if not r['passed']]
        if failures:
            print(f"\n❌ Failed Tests:")
            for failure in failures:
                print(f"   • Test {failure['test_number']}: '{failure['request']}'")
                print(f"     Expected: {failure['expected_type']}, Got: {failure['actual_type']}")
                if 'error' in failure:
                    print(f"     Error: {failure['error']}")
        
        # Critical test verification
        critical_test = next((r for r in results if "Critical: Primary relationship pattern" in r['description']), None)
        if critical_test:
            if critical_test['passed']:
                print(f"\n🎯 CRITICAL TEST PASSED: 'add course to student entity' correctly detected as relationship")
            else:
                print(f"\n🚨 CRITICAL TEST FAILED: 'add course to student entity' not detected as relationship")
                print(f"   This indicates the core issue is NOT resolved")
    
    print("\n💡 Enhanced LLM prompts now provide clearer relationship detection rules")
    print("💡 User confirmation dialog available for ambiguous cases")
    print("💡 Comprehensive context information helps LLM make better decisions")

if __name__ == "__main__":
    test_llm_only_relationship_detection() 