#!/usr/bin/env python3
"""
Demonstration of the new JSON enforcement functionality in OpenAIClient.

This script shows how to use the enhanced generate_response method with JSON enforcement
to ensure reliable JSON parsing throughout the BAE system.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from baes.llm.openai_client import OpenAIClient


def demo_basic_json_enforcement():
    """Demonstrate basic JSON enforcement"""
    print("🔧 Demo 1: Basic JSON Enforcement")
    print("=" * 50)
    
    client = OpenAIClient()
    
    # Example 1: Simple JSON response
    prompt = "Return a JSON object with name and age fields"
    
    # Use the new JSON enforcement functionality
    json_schema = {
        "name": "string",
        "age": 0
    }
    
    fallback_schema = {
        "name": "Unknown",
        "age": 0,
        "error": True
    }
    
    response = client.generate_json_response(
        prompt=prompt,
        json_schema=json_schema,
        fallback_schema=fallback_schema
    )
    
    print(f"✅ Response: {response}")
    print(f"   Type: {type(response)}")
    print(f"   Name: {response.get('name')}")
    print(f"   Age: {response.get('age')}")
    print()

def demo_complex_json_enforcement():
    """Demonstrate complex JSON enforcement with nested structures"""
    print("🔧 Demo 2: Complex JSON Enforcement")
    print("=" * 50)
    
    client = OpenAIClient()
    
    # Example 2: Complex nested JSON
    prompt = "Return a JSON object representing a student with courses"
    
    json_schema = {
        "student": {
            "name": "string",
            "email": "string",
            "courses": [
                {
                    "name": "string",
                    "code": "string",
                    "credits": 0
                }
            ]
        }
    }
    
    fallback_schema = {
        "student": {
            "name": "Unknown Student",
            "email": "unknown@example.com",
            "courses": []
        },
        "error": True
    }
    
    response = client.generate_json_response(
        prompt=prompt,
        json_schema=json_schema,
        fallback_schema=fallback_schema
    )
    
    print(f"✅ Response: {response}")
    student = response.get('student', {})
    print(f"   Student Name: {student.get('name')}")
    print(f"   Student Email: {student.get('email')}")
    print(f"   Courses: {len(student.get('courses', []))}")
    print()

def demo_error_handling():
    """Demonstrate error handling with fallback schemas"""
    print("🔧 Demo 3: Error Handling with Fallback Schemas")
    print("=" * 50)
    
    client = OpenAIClient()
    
    # Example 3: Malformed prompt that might cause issues
    prompt = "Return a list of users (this might cause issues with JSON parsing)"
    
    json_schema = {
        "users": [
            {
                "id": 0,
                "name": "string",
                "active": True
            }
        ]
    }
    
    fallback_schema = {
        "users": [],
        "error": True,
        "error_message": "Failed to parse user list",
        "fallback_response": True
    }
    
    response = client.generate_json_response(
        prompt=prompt,
        json_schema=json_schema,
        fallback_schema=fallback_schema
    )
    
    print(f"✅ Response: {response}")
    print(f"   Has Error: {response.get('error', False)}")
    print(f"   Users Count: {len(response.get('users', []))}")
    print(f"   Error Message: {response.get('error_message', 'None')}")
    print()

def demo_ensure_json_parameter():
    """Demonstrate the ensure_json parameter in generate_response"""
    print("🔧 Demo 4: Using ensure_json Parameter")
    print("=" * 50)
    
    client = OpenAIClient()
    
    # Example 4: Using ensure_json parameter
    prompt = "Return a JSON object with status and message fields"
    
    # Use ensure_json=True for automatic JSON enforcement
    response = client.generate_response(
        prompt=prompt,
        ensure_json=True,
        json_schema={
            "status": "success|error",
            "message": "string"
        }
    )
    
    print(f"✅ Response: {response}")
    print(f"   Type: {type(response)}")
    
    # Parse the response (should be valid JSON now)
    try:
        parsed = json.loads(response)
        print(f"   Status: {parsed.get('status')}")
        print(f"   Message: {parsed.get('message')}")
    except json.JSONDecodeError as e:
        print(f"   ❌ Still failed to parse: {e}")
    print()


def main():
    """Run all demonstrations"""
    print("🚀 JSON Enforcement Demo")
    print("=" * 60)
    print("This demo shows the new JSON enforcement functionality")
    print("in the OpenAIClient to prevent JSON parsing errors.")
    print("=" * 60)
    print()
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some demos may fail.")
        print("   Set the environment variable to test with real API calls.")
        print()
    
    try:
        demo_basic_json_enforcement()
        demo_complex_json_enforcement()
        demo_error_handling()
        demo_ensure_json_parameter()
        
        print("✅ All demonstrations completed!")
        print("\n📝 Summary:")
        print("- Use ensure_json=True for basic JSON enforcement")
        print("- Use json_schema for structured responses")
        print("- Use generate_json_response() for robust parsing")
        print("- Always provide fallback_schema for error cases")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("This might be due to missing API key or network issues.")


if __name__ == "__main__":
    main() 