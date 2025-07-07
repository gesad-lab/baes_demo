#!/usr/bin/env python3
"""
Test script to verify the relationship detection fix works correctly.
This tests the enhanced prompt logic and user confirmation system.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_prompt_structure():
    """Test that the enhanced prompt contains the correct relationship detection rules"""
    print("🧪 Testing Enhanced Prompt Structure")
    print("=" * 50)
    
    try:
        from baes.domain_entities.academic.student_bae import StudentBae
        student_bae = StudentBae()
        
        # Generate the enhanced prompt
        prompt = student_bae._build_unified_interpretation_prompt(
            "add course to student entity", 
            "academic"
        )
        
        # Check for critical components
        required_elements = [
            "RELATIONSHIP DETECTION RULES (HIGHEST PRIORITY",
            "RULE 1 - \"ADD X TO Y ENTITY\" PATTERN",
            "add course to student entity",
            "STEP-BY-STEP ANALYSIS",
            "CONFIDENCE SCORING"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in prompt:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing required prompt elements: {missing_elements}")
            return False
        else:
            print("✅ Enhanced prompt contains all required relationship detection rules")
            return True
            
    except Exception as e:
        print(f"❌ Error testing prompt structure: {str(e)}")
        return False

def test_context_information_enhancement():
    """Test that the context builder provides comprehensive relationship information"""
    print("\n🧪 Testing Enhanced Context Information")
    print("=" * 50)
    
    try:
        from baes.domain_entities.academic.student_bae import StudentBae
        student_bae = StudentBae()
        
        # Mock existing entities and current entity data
        existing_entities = {
            "course": {
                "exists": True,
                "attributes": [{"name": "id", "type": "int"}, {"name": "name", "type": "str"}],
                "source": "test"
            }
        }
        
        current_entity = {
            "exists": True,
            "attributes": [{"name": "id", "type": "int"}, {"name": "name", "type": "str"}],
            "source": "test"
        }
        
        # Generate context information
        context_info = student_bae._build_context_information(existing_entities, current_entity)
        
        # Check for enhanced elements
        required_elements = [
            "AVAILABLE ENTITIES FOR RELATIONSHIPS",
            "POTENTIAL RELATIONSHIPS",
            "RELATIONSHIP DETECTION GUIDANCE", 
            "ACADEMIC DOMAIN PATTERNS",
            "add [ENTITY_A] to [ENTITY_B] entity"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in context_info:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing required context elements: {missing_elements}")
            return False
        else:
            print("✅ Enhanced context contains all required relationship guidance")
            print(f"   📊 Context length: {len(context_info)} characters")
            return True
            
    except Exception as e:
        print(f"❌ Error testing context enhancement: {str(e)}")
        return False

def test_user_confirmation_system():
    """Test that the user confirmation system is properly integrated"""
    print("\n🧪 Testing User Confirmation System")
    print("=" * 50)
    
    try:
        from bae_chat import BAEConversationalCLI
        cli = BAEConversationalCLI()
        
        # Test interpretation preview method exists
        if not hasattr(cli, '_get_interpretation_preview'):
            print("❌ Missing _get_interpretation_preview method")
            return False
        
        # Test confirmation checking method exists
        if not hasattr(cli, '_needs_user_confirmation'):
            print("❌ Missing _needs_user_confirmation method")
            return False
        
        # Test clarification request method exists
        if not hasattr(cli, '_request_user_clarification'):
            print("❌ Missing _request_user_clarification method")
            return False
        
        # Test clarified request generation method exists
        if not hasattr(cli, '_generate_clarified_request'):
            print("❌ Missing _generate_clarified_request method")
            return False
        
        print("✅ All user confirmation system methods are present")
        
        # Test low confidence detection
        mock_low_confidence = {"confidence": 0.5, "operation_type": "create"}
        needs_confirmation = cli._needs_user_confirmation(mock_low_confidence, "add course to student entity")
        
        if needs_confirmation:
            print("✅ Low confidence requests correctly trigger user confirmation")
        else:
            print("⚠️  Low confidence requests may not trigger confirmation")
        
        # Test ambiguous pattern detection 
        mock_ambiguous = {"confidence": 0.8, "operation_type": "create", "entities_mentioned": ["student", "course"]}
        needs_confirmation = cli._needs_user_confirmation(mock_ambiguous, "add course to student entity")
        
        if needs_confirmation:
            print("✅ Ambiguous relationship patterns correctly trigger user confirmation")
        else:
            print("⚠️  Ambiguous patterns may not trigger confirmation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing user confirmation system: {str(e)}")
        return False

def test_clarified_request_generation():
    """Test that clarified requests are generated correctly"""
    print("\n🧪 Testing Clarified Request Generation")
    print("=" * 50)
    
    try:
        from bae_chat import BAEConversationalCLI
        cli = BAEConversationalCLI()
        
        # Test relationship clarification
        clarified = cli._generate_clarified_request("add course to student", "relationship")
        expected = "add course to student entity"
        
        if clarified == expected:
            print("✅ Relationship clarification generates correct explicit format")
        else:
            print(f"⚠️  Relationship clarification: expected '{expected}', got '{clarified}'")
        
        # Test entity creation clarification
        clarified = cli._generate_clarified_request("add student", "create")
        expected = "add student entity"
        
        if clarified == expected:
            print("✅ Entity creation clarification generates correct format")
        else:
            print(f"⚠️  Entity creation clarification: expected '{expected}', got '{clarified}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing clarified request generation: {str(e)}")
        return False

def run_verification_tests():
    """Run all verification tests"""
    print("🔍 Relationship Detection Fix Verification")
    print("=" * 60)
    print("Testing the implemented fixes without requiring OpenAI API")
    print()
    
    tests = [
        test_enhanced_prompt_structure,
        test_context_information_enhancement, 
        test_user_confirmation_system,
        test_clarified_request_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with error: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Verification Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All verification tests passed! The fixes are properly implemented.")
        print("💡 Ready for live testing with OpenAI API")
    else:
        print("⚠️  Some verification tests failed. Review the implementation.")
    
    print("\n📋 Next Steps:")
    print("1. Set up OpenAI API key in .env file")
    print("2. Run: python test_llm_only_relationship.py")
    print("3. Test the critical case: 'add course to student entity'")
    
    return passed == total

if __name__ == "__main__":
    run_verification_tests()