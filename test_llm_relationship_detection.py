#!/usr/bin/env python3
"""
Test script to demonstrate LLM-based relationship detection in the BAE system.
This script shows how the system now uses LLM instead of fixed patterns to detect relationships.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from baes.domain_entities.academic.student_bae import StudentBae
from baes.domain_entities.academic.course_bae import CourseBae


def test_llm_relationship_detection():
    """Test LLM-based relationship detection with various natural language requests"""
    
    print("🧠 Testing LLM-Based Relationship Detection")
    print("=" * 60)
    
    # Initialize BAEs
    student_bae = StudentBae()
    course_bae = CourseBae()
    
    # Test cases for relationship detection
    relationship_test_cases = [
        # Standard patterns (should work with LLM)
        "add a course to the student entity",
        "connect teacher with course",
        "enroll student in course",
        "assign teacher to course",
        "link student to course",
        "associate course with student",
        
        # Natural language variations
        "register student for course",
        "relate teacher to course",
        "connect student with course",
        "link course to student",
        "associate teacher with course",
        "enroll course to student",
        
        # Domain-specific terminology
        "assign instructor to class",
        "enroll learner in program",
        "register participant for workshop",
        "connect professor with subject",
        
        # Complex variations
        "I want to add a course relationship to the student entity",
        "Please connect the teacher entity with the course entity",
        "Can you link students to their courses?",
        "We need to associate teachers with their assigned courses",
    ]
    
    # Test cases for non-relationship requests (should NOT be detected as relationships)
    non_relationship_test_cases = [
        "add student",
        "create course",
        "add email field to student",
        "modify student name",
        "include teacher information",
        "add birth date to students",
        "students should have grade point average",
        "create a student management system",
    ]
    
    print("\n🔗 Testing Relationship Detection:")
    print("-" * 40)
    
    for i, request in enumerate(relationship_test_cases, 1):
        print(f"\n{i}. Request: '{request}'")
        
        # Test with Student BAE
        result = student_bae._detect_relationship_request(request)
        
        if result.get("is_relationship", False):
            print(f"   ✅ Detected as relationship")
            print(f"   📊 Target entity: {result.get('target_entity')}")
            print(f"   📊 Related entity: {result.get('related_entity')}")
            print(f"   📊 Type: {result.get('relationship_type')}")
            print(f"   📊 Confidence: {result.get('confidence', 0.0)}")
            print(f"   💭 Reasoning: {result.get('reasoning', 'No reasoning')}")
        else:
            print(f"   ❌ NOT detected as relationship")
            print(f"   💭 Reasoning: {result.get('reasoning', 'No reasoning')}")
    
    print("\n🔍 Testing Non-Relationship Detection:")
    print("-" * 40)
    
    for i, request in enumerate(non_relationship_test_cases, 1):
        print(f"\n{i}. Request: '{request}'")
        
        # Test with Student BAE
        result = student_bae._detect_relationship_request(request)
        
        if result.get("is_relationship", False):
            print(f"   ❌ INCORRECTLY detected as relationship")
            print(f"   💭 Reasoning: {result.get('reasoning', 'No reasoning')}")
        else:
            print(f"   ✅ Correctly NOT detected as relationship")
            print(f"   💭 Reasoning: {result.get('reasoning', 'No reasoning')}")
    
    print("\n🎯 Testing Unified LLM Interpretation:")
    print("-" * 40)
    
    # Test the unified interpretation system
    unified_test_cases = [
        "add a course to the student entity",
        "enroll student in course",
        "add email field to student",
        "create course",
    ]
    
    for i, request in enumerate(unified_test_cases, 1):
        print(f"\n{i}. Request: '{request}'")
        
        # Test with Student BAE using unified interpretation
        payload = {"request": request, "context": "academic"}
        result = student_bae._interpret_business_request(payload)
        
        if result.get("success") is False:
            print(f"   ❌ Error: {result.get('error')}")
            continue
            
        operation_type = result.get("request_type", "unknown")
        is_evolution = result.get("is_evolution", False)
        
        print(f"   📊 Operation type: {operation_type}")
        print(f"   📊 Is evolution: {is_evolution}")
        print(f"   📊 Entity: {result.get('entity')}")
        
        if operation_type == "relationship":
            print(f"   🔗 Relationship detected!")
            print(f"   📊 Target entity: {result.get('relationship_info', {}).get('target_entity')}")
            print(f"   📊 Related entity: {result.get('relationship_info', {}).get('related_entity')}")
        elif operation_type == "evolve":
            print(f"   🔄 Evolution detected!")
            new_attrs = result.get("new_attributes", [])
            print(f"   📊 New attributes: {[attr.get('name', str(attr)) for attr in new_attrs]}")
        elif operation_type == "create":
            print(f"   🆕 Creation detected!")
            attrs = result.get("attributes", [])
            print(f"   📊 Attributes: {[attr.get('name', str(attr)) for attr in attrs]}")
    
    print("\n✅ LLM-Based Relationship Detection Test Complete!")
    print("💡 The system now uses LLM instead of fixed patterns for relationship detection.")
    print("🔗 This provides much more flexible and intelligent relationship recognition.")


if __name__ == "__main__":
    test_llm_relationship_detection() 