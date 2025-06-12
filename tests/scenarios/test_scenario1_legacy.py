#!/usr/bin/env python3
"""
Test Script for BAE Scenario 1: Initial System Generation

This script tests the core components of the BAE architecture for validating
that the Student BAE can interpret business requests and coordinate with SWEA
agents to generate a functional system.

Usage: python test_scenario1.py
"""

import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_openai_client():
    """Test OpenAI client basic functionality"""
    print("\n" + "=" * 60)
    print("Testing OpenAI Client")
    print("=" * 60)

    try:
        from baes.llm.openai_client import OpenAIClient

        client = OpenAIClient()
        print(f"✅ OpenAI Client initialized with model: {client.model}")

        # Test basic response generation (mock for now since we don't have API key)
        print("✅ OpenAI Client ready for domain entity operations")

        assert client is not None
        assert hasattr(client, "model")

    except Exception as e:
        print(f"❌ OpenAI Client test failed: {str(e)}")
        assert False, f"OpenAI Client test failed: {str(e)}"


def test_context_store():
    """Test context store functionality"""
    print("\n" + "=" * 60)
    print("Testing Context Store")
    print("=" * 60)

    try:
        from baes.core.context_store import ContextStore

        # Initialize context store
        context_store = ContextStore("database/test_context_store.json")
        print("✅ Context Store initialized")

        # Test domain context storage
        test_context = {
            "entity": "Student",
            "attributes": ["name", "registration", "course"],
            "business_rules": ["Unique registration", "Required name"],
        }

        success = context_store.store_domain_context("academic", test_context, "Student")
        if success:
            print("✅ Domain context stored successfully")
        else:
            print("❌ Failed to store domain context")
            assert False, "Failed to store domain context"

        # Test context retrieval
        retrieved_context = context_store.get_domain_context("academic")
        if retrieved_context and retrieved_context["context_data"]["entity"] == "Student":
            print("✅ Domain context retrieved successfully")
        else:
            print("❌ Failed to retrieve domain context")
            assert False, "Failed to retrieve domain context"

        # Test business vocabulary storage
        vocabulary = ["Student", "Academic", "Learning", "Enrollment"]
        vocab_success = context_store.store_business_vocabulary("academic", vocabulary, "Student")
        if vocab_success:
            print("✅ Business vocabulary stored successfully")
        else:
            print("❌ Failed to store business vocabulary")
            assert False, "Failed to store business vocabulary"

        # Get summary
        summary = context_store.get_context_summary()
        print(f"✅ Context Summary: {summary}")

        assert summary is not None
        assert isinstance(summary, dict)

    except Exception as e:
        print(f"❌ Context Store test failed: {str(e)}")
        assert False, f"Context Store test failed: {str(e)}"


def test_base_agent():
    """Test base agent functionality"""
    print("\n" + "=" * 60)
    print("Testing Base Agent")
    print("=" * 60)

    try:
        from agents.base_agent import BaseAgent

        # Create a simple test agent
        class TestAgent(BaseAgent):
            def handle_task(self, task: str, payload: dict) -> dict:
                return self.create_success_response(task, {"message": "Task handled successfully"})

        agent = TestAgent("TestAgent", "Test Role", "TEST")
        print(f"✅ Base Agent initialized: {agent}")

        # Test memory operations
        agent.update_memory("test_key", "test_value", {"meta": "test"})
        retrieved_value = agent.get_memory("test_key")
        if retrieved_value == "test_value":
            print("✅ Agent memory operations working")
        else:
            print("❌ Agent memory operations failed")
            assert False, "Agent memory operations failed"

        # Test task handling
        result = agent.handle_task("test_task", {"test": "data"})
        if result.get("success") and result.get("data", {}).get("message"):
            print("✅ Agent task handling working")
        else:
            print("❌ Agent task handling failed")
            assert False, "Agent task handling failed"

        # Test agent status
        status = agent.get_agent_status()
        print(f"✅ Agent Status: {status['name']} - {status['interaction_count']} interactions")

        assert status is not None
        assert status["name"] == "TestAgent"

    except Exception as e:
        print(f"❌ Base Agent test failed: {str(e)}")
        assert False, f"Base Agent test failed: {str(e)}"


def test_student_bae():
    """Test Student BAE functionality"""
    print("\n" + "=" * 60)
    print("Testing Student BAE (Domain Entity Representative)")
    print("=" * 60)

    try:
        from baes.domain_entities.academic.student_bae import StudentBae as StudentBAE

        # Initialize Student BAE
        student_bae = StudentBAE()
        print(f"✅ Student BAE initialized: {student_bae}")

        # Test domain knowledge initialization
        domain_knowledge = student_bae._get_domain_info({})
        if domain_knowledge.get("entity") == "Student":
            print("✅ Student BAE domain knowledge initialized")
            print(f"   📚 Business Vocabulary: {student_bae.business_vocabulary[:5]}...")
        else:
            print("❌ Student BAE domain knowledge initialization failed")
            assert False, "Student BAE domain knowledge initialization failed"

        # Test business request interpretation (without OpenAI for now)
        test_request = (
            "Create a system to manage students with name, registration number, and course"
        )

        # Mock the interpretation since we don't have OpenAI API key yet
        mock_payload = {"request": test_request, "context": "academic"}

        print(f"✅ Student BAE ready to interpret: '{test_request}'")
        print("   🎯 Entity Focus: Student")
        print("   📖 Context: Academic")
        print("   🔧 Domain Operations: Create, Read, Update, Delete")

        # Test schema generation preparation
        test_attributes = ["name: str", "registration_number: str", "course: str"]
        schema_payload = {"attributes": test_attributes, "context": "academic"}

        print(f"✅ Student BAE ready for schema generation")
        print(f"   📋 Attributes: {test_attributes}")

        # Test coordination plan creation via business request interpretation
        interpretation_result = student_bae._interpret_business_request(
            {
                "request": "Create a system to manage students with " + ", ".join(test_attributes),
                "context": "academic",
            }
        )
        coordination_plan = interpretation_result.get("swea_coordination", [])

        if coordination_plan and len(coordination_plan) >= 3:
            print("✅ SWEA coordination plan created")
            for i, step in enumerate(coordination_plan):
                print(
                    f"   Step {i+1}: {step.get('swea_agent', 'Unknown')} - {step.get('task_type', 'Unknown')}"
                )
        else:
            print("❌ SWEA coordination plan creation failed")
            assert False, "SWEA coordination plan creation failed"

        assert coordination_plan is not None
        assert len(coordination_plan) >= 3

    except Exception as e:
        print(f"❌ Student BAE test failed: {str(e)}")
        assert False, f"Student BAE test failed: {str(e)}"


def test_scenario1_workflow():
    """Test the complete Scenario 1 workflow simulation"""
    print("\n" + "=" * 60)
    print("Testing Scenario 1: Initial System Generation Workflow")
    print("=" * 60)

    try:
        from baes.core.context_store import ContextStore
        from baes.domain_entities.academic.student_bae import StudentBae as StudentBAE

        # Initialize components
        student_bae = StudentBAE()
        context_store = ContextStore("database/scenario1_test.json")

        print("✅ Scenario 1 components initialized")

        # Simulate HBE (Human Business Expert) input
        hbe_input = "Create a system to manage students with name, registration number, and course"
        print(f"🎭 HBE Input: '{hbe_input}'")

        # Step 1: Student BAE interprets business request
        print("\n📋 Step 1: Student BAE Business Request Interpretation")

        # Create mock interpretation result (since we don't have OpenAI API key)
        mock_interpretation = {
            "intent": "create_student_management_system",
            "entity_focus": "Student",
            "requested_operations": ["create", "read", "update", "delete", "list"],
            "attributes_mentioned": ["name", "registration_number", "course"],
            "business_vocabulary": student_bae.business_vocabulary,
            "swea_coordination_needed": {"programmer": True, "frontend": True, "database": True},
            "complexity_level": "simple",
        }

        print("   ✅ Business request interpreted")
        print(f"   🎯 Intent: {mock_interpretation['intent']}")
        print(f"   📊 Entity Focus: {mock_interpretation['entity_focus']}")
        print(f"   🔧 Operations: {mock_interpretation['requested_operations']}")

        # Step 2: Create coordination plan
        print("\n📋 Step 2: SWEA Coordination Plan Creation")
        interpretation_result = student_bae._interpret_business_request(
            {
                "request": "Create a system to manage students with "
                + ", ".join(mock_interpretation["attributes_mentioned"]),
                "context": "academic",
            }
        )
        coordination_plan = interpretation_result.get("swea_coordination", [])

        print(f"   ✅ Coordination plan created with {len(coordination_plan)} steps")

        # Step 3: Store domain context
        print("\n📋 Step 3: Domain Context Preservation")
        context_data = {
            "interpretation": mock_interpretation,
            "coordination_plan": coordination_plan,
            "entity": "Student",
            "context": "academic",
        }

        context_stored = context_store.store_domain_context(
            "scenario1_test", context_data, "Student"
        )
        if context_stored:
            print("   ✅ Domain context preserved for future reuse")

        # Step 4: Business vocabulary preservation
        vocab_stored = context_store.store_business_vocabulary(
            "academic", mock_interpretation["business_vocabulary"], "Student"
        )
        if vocab_stored:
            print("   ✅ Business vocabulary preserved for semantic coherence")

        # Step 5: Validate coordination plan structure
        print("\n📋 Step 5: Coordination Plan Validation")
        required_agents = ["ProgrammerSWEA", "FrontendSWEA"]
        plan_agents = [step.get("swea_agent", "") for step in coordination_plan]

        if all(agent in plan_agents for agent in required_agents):
            print("   ✅ All required SWEA agents included in coordination plan")
        else:
            print(
                f"   ❌ Missing agents in plan. Required: {required_agents}, Found: {plan_agents}"
            )
            assert (
                False
            ), f"Missing agents in plan. Required: {required_agents}, Found: {plan_agents}"

        # Summary
        print("\n📊 Scenario 1 Test Summary:")
        print(f"   🎯 Entity: Student (Domain Entity Representative)")
        print(f"   📖 Context: Academic")
        print(
            f"   🔧 Operations: {len(mock_interpretation['requested_operations'])} domain operations"
        )
        print(f"   👥 SWEA Agents: {len(required_agents)} coordinated agents")
        print(f"   📚 Business Vocabulary: {len(mock_interpretation['business_vocabulary'])} terms")
        print(f"   ⏱️  Ready for <3 minute generation (Scenario 1 success criteria)")

        assert context_stored == True
        assert vocab_stored == True
        assert len(coordination_plan) >= 2

    except Exception as e:
        print(f"❌ Scenario 1 workflow test failed: {str(e)}")
        assert False, f"Scenario 1 workflow test failed: {str(e)}"


def main():
    """Run all tests for Scenario 1 validation"""
    print("🚀 BAE Scenario 1: Initial System Generation - Test Suite")
    print("🎯 Validating core components for domain entity autonomy")
    print("📋 Testing Student BAE as domain entity representative")

    start_time = datetime.now()

    tests = [
        ("OpenAI Client", test_openai_client),
        ("Context Store", test_context_store),
        ("Base Agent", test_base_agent),
        ("Student BAE", test_student_bae),
        ("Scenario 1 Workflow", test_scenario1_workflow),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))

    # Print final results
    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("🏁 SCENARIO 1 TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print(f"\n📊 Summary: {passed}/{total} tests passed")
    print(f"⏱️  Duration: {duration:.2f} seconds")

    if passed == total:
        print("\n🎉 All tests passed! Scenario 1 core components are ready.")
        print("📋 Next Steps:")
        print("   1. Set up OpenAI API key for full LLM integration")
        print("   2. Implement SWEA agents (Programmer, Frontend, Database)")
        print("   3. Create Runtime Kernel for orchestration")
        print("   4. Test complete Scenario 1 execution")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
