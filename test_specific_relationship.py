#!/usr/bin/env python3
"""
Test script to verify that the specific relationship command that was failing now works correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from baes.domain_entities.academic.student_bae import StudentBae
from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel

def test_specific_relationship_command():
    """Test the specific command that was failing: 'add course to student entity'"""
    
    print("🧠 Testing Specific Relationship Command")
    print("=" * 60)
    
    # First, create a student entity
    print("\n1️⃣ Creating student entity first...")
    kernel = EnhancedRuntimeKernel()
    
    # Create student
    result1 = kernel.process_natural_language_request("create a student entity with name and email")
    if result1.get("success"):
        print("✅ Student entity created successfully")
    else:
        print(f"❌ Failed to create student: {result1.get('error', 'Unknown error')}")
        return
    
    # Create course entity
    print("\n2️⃣ Creating course entity...")
    result2 = kernel.process_natural_language_request("create a course entity with name")
    if result2.get("success"):
        print("✅ Course entity created successfully")
    else:
        print(f"❌ Failed to create course: {result2.get('error', 'Unknown error')}")
        return
    
    # Now test the relationship command that was failing
    print("\n3️⃣ Testing the relationship command that was failing...")
    print("   Command: 'add course to student entity'")
    
    try:
        result3 = kernel.process_natural_language_request("add course to student entity")
        
        if result3.get("success"):
            print("✅ Relationship command executed successfully!")
            print(f"   Entity processed: {result3.get('entity', 'Unknown')}")
            
            # Check if it was detected as a relationship
            execution_results = result3.get("execution_results", [])
            for task_result in execution_results:
                task_name = task_result.get("task", "")
                if "create_relationships" in task_name:
                    print("   🔗 Relationship creation task found!")
                    break
            else:
                print("   ⚠️  No relationship creation task found in results")
                
        else:
            print(f"❌ Relationship command failed: {result3.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during relationship command: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_relationship_command() 