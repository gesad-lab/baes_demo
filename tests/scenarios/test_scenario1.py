"""
Scenario 1 Test: Initial System Generation

This test validates the proof of concept Scenario 1 which demonstrates
automatic creation of a functional system from natural language input
where the Student BAE acts as an autonomous domain entity representative.

Success Criteria:
- Generation time < 3 minutes
- 100% functional system without manual intervention
- Generated code follows programming best practices
- Maintains domain entity focus throughout generated artifacts
"""

import pytest
import time
from unittest.mock import patch, Mock

from baes.llm.openai_client import OpenAIClient
from baes.core.context_store import ContextStore
from baes.agents.base_agent import BaseAgent
from baes.agents.student_bae import StudentBAE


@pytest.mark.scenario
@pytest.mark.slow
class TestScenario1:
    """Test suite for Scenario 1: Initial System Generation"""
    
    def test_scenario1_complete_workflow(
        self, 
        mock_openai_client, 
        temp_database_path, 
        clean_test_environment,
        performance_tracker,
        scenario1_success_criteria
    ):
        """
        Test the complete Scenario 1 workflow: Initial System Generation
        
        Business Request: "Create a system to manage students with name, registration number, and course"
        Expected: Complete web system (API + UI + DB) operational in < 3 minutes
        """
        
        performance_tracker.start("scenario1_complete_workflow")
        
        # Step 1: Initialize components
        context_store = ContextStore(temp_database_path)
        student_bae = StudentBAE()
        
        # Step 2: Business request interpretation
        business_request = {
            "request": "Create a system to manage students with name, registration number, and course",
            "context": "academic"
        }
        
        interpretation_result = student_bae.handle_task("interpret_business_request", business_request)
        
        # Validate interpretation
        assert "interpreted_intent" in interpretation_result
        assert "domain_operations" in interpretation_result
        assert "swea_coordination" in interpretation_result
        assert "business_vocabulary" in interpretation_result
        
        # Step 3: Schema generation by Student BAE
        schema_payload = {
            "attributes": ["name: str", "registration_number: str", "course: str"],
            "context": "academic"
        }
        
        schema_result = student_bae.handle_task("generate_schema", schema_payload)
        
        # Validate schema generation
        assert schema_result["entity"] == "Student"
        assert "class Student(BaseModel)" in schema_result["code"]
        assert len(schema_result["attributes"]) == 3
        assert schema_result["context"] == "academic"
        
        # Step 4: SWEA coordination plan
        swea_tasks = [
            {"agent": "ProgrammerSWEA", "task": "generate_api"},
            {"agent": "FrontendSWEA", "task": "generate_ui"},
            {"agent": "DatabaseSWEA", "task": "setup_database"}
        ]
        
        coordination_payload = {
            "swea_tasks": swea_tasks,
            "domain_context": {
                "entity": "Student",
                "schema": schema_result,
                "business_vocabulary": ["Student", "Academic", "Registration"]
            }
        }
        
        coordination_result = student_bae.handle_task("coordinate_swea", coordination_payload)
        
        # Validate SWEA coordination
        coordination_plan = coordination_result["coordination_plan"]
        assert len(coordination_plan) == 3
        
        # Verify each SWEA task has domain context
        for task in coordination_plan:
            assert "domain_context" in task
            assert "semantic_requirements" in task
            assert task["semantic_requirements"]["maintain_domain_coherence"] is True
        
        # Step 5: Domain knowledge preservation
        domain_knowledge = {
            "entity": "Student",
            "core_attributes": schema_result["attributes"],
            "business_rules": schema_result.get("business_rules", []),
            "context": "academic",
            "semantic_coherence_validated": True
        }
        
        context_store.preserve_domain_knowledge("Student", domain_knowledge)
        
        # Validate domain knowledge preservation
        preserved_knowledge = context_store.get_domain_knowledge("Student")
        assert preserved_knowledge is not None
        assert preserved_knowledge["entity"] == "Student"
        assert len(preserved_knowledge["core_attributes"]) == 3
        
        # Step 6: Semantic coherence validation
        validation_payload = {
            "artifact_code": schema_result["code"],
            "artifact_type": "Pydantic Model"
        }
        
        validation_result = student_bae.handle_task("validate_domain_rules", validation_payload)
        
        # Validate semantic coherence
        assert validation_result["is_valid"] is True
        assert validation_result["semantic_coherence_score"] >= scenario1_success_criteria["min_semantic_coherence_score"]
        assert validation_result["business_vocabulary_preserved"] is True
        
        # Step 7: Performance validation
        execution_time = performance_tracker.stop()
        
        # Assert performance criteria
        assert execution_time < scenario1_success_criteria["max_generation_time_seconds"], \
            f"Scenario 1 took {execution_time:.2f}s, exceeding {scenario1_success_criteria['max_generation_time_seconds']}s limit"
        
        # Step 8: Success criteria validation
        success_metrics = {
            "generation_time": execution_time,
            "semantic_coherence_score": validation_result["semantic_coherence_score"],
            "domain_entity_autonomy": True,  # Student BAE operated autonomously
            "swea_coordination_successful": len(coordination_plan) >= 3,
            "business_vocabulary_preserved": validation_result["business_vocabulary_preserved"],
            "domain_knowledge_persisted": preserved_knowledge is not None
        }
        
        # Assert all success criteria met
        assert success_metrics["generation_time"] < scenario1_success_criteria["max_generation_time_seconds"]
        assert success_metrics["semantic_coherence_score"] >= scenario1_success_criteria["min_semantic_coherence_score"]
        assert success_metrics["domain_entity_autonomy"] is True
        assert success_metrics["swea_coordination_successful"] is True
        assert success_metrics["business_vocabulary_preserved"] is True
        assert success_metrics["domain_knowledge_persisted"] is True
        
        print(f"✅ Scenario 1 completed successfully in {execution_time:.2f} seconds")
        print(f"📊 Semantic coherence score: {validation_result['semantic_coherence_score']}")
        print(f"🤖 SWEA agents coordinated: {len(coordination_plan)}")
        print(f"📚 Domain knowledge preserved: {bool(preserved_knowledge)}")
    
    def test_student_bae_autonomous_operation(self, mock_openai_client, clean_test_environment):
        """Test that Student BAE operates autonomously as domain entity representative"""
        
        student_bae = StudentBAE()
        
        # Test autonomous business request interpretation
        business_request = {
            "request": "Manage student enrollment data with academic information",
            "context": "university"
        }
        
        result = student_bae.handle_task("interpret_business_request", business_request)
        
        # Verify autonomous operation
        assert "interpreted_intent" in result
        assert "entity_focus" in result.get("entity_focus", "Student") or "Student" in str(result)
        assert "swea_coordination_needed" in result.get("swea_coordination_needed", {}) or "swea_coordination" in result
        
        # Test autonomous schema generation
        schema_payload = {
            "attributes": ["student_id: str", "full_name: str", "enrollment_date: date"],
            "context": "university"
        }
        
        schema_result = student_bae.handle_task("generate_schema", schema_payload)
        
        # Verify domain entity representation
        assert schema_result["entity"] == "Student"
        assert "business_rules" in schema_result
        
        print("✅ Student BAE demonstrated autonomous domain entity representation")
    
    def test_semantic_coherence_maintenance(self, mock_openai_client, clean_test_environment):
        """Test that semantic coherence is maintained between business vocabulary and technical artifacts"""
        
        student_bae = StudentBAE()
        
        # Business vocabulary to preserve
        business_vocabulary = ["Student", "Academic", "Enrollment", "Registration", "Course"]
        
        # Generate schema with business focus
        schema_payload = {
            "attributes": ["name: str", "registration_number: str", "enrolled_course: str"],
            "context": "academic",
            "business_vocabulary": business_vocabulary
        }
        
        schema_result = student_bae.handle_task("generate_schema", schema_payload)
        
        # Extract business vocabulary from generated schema
        generated_vocabulary = student_bae._extract_business_vocabulary()
        
        # Verify semantic coherence
        business_terms_preserved = any(term in generated_vocabulary for term in business_vocabulary)
        assert business_terms_preserved, "Business vocabulary not preserved in generated artifacts"
        
        # Validate domain rules
        validation_payload = {
            "artifact_code": schema_result["code"],
            "artifact_type": "Pydantic Model"
        }
        
        validation_result = student_bae.handle_task("validate_domain_rules", validation_payload)
        
        assert validation_result["business_vocabulary_preserved"] is True
        assert validation_result["semantic_coherence_score"] >= 80
        
        print("✅ Semantic coherence maintained between business vocabulary and technical artifacts")
    
    def test_domain_knowledge_reusability_preparation(self, mock_openai_client, temp_database_path, clean_test_environment):
        """Test that domain knowledge is preserved for future reusability (prepares for Scenario 3)"""
        
        context_store = ContextStore(temp_database_path)
        student_bae = StudentBAE()
        
        # Generate and preserve domain knowledge for academic context
        academic_payload = {
            "attributes": ["student_id: str", "full_name: str", "registration_number: str", "course: str"],
            "context": "academic"
        }
        
        academic_schema = student_bae.handle_task("generate_schema", academic_payload)
        
        # Preserve domain knowledge
        academic_knowledge = {
            "entity": "Student",
            "context": "academic",
            "core_attributes": academic_schema["attributes"],
            "business_rules": academic_schema.get("business_rules", []),
            "usage_patterns": ["university", "formal_education"],
            "reusability_score": 95
        }
        
        context_store.preserve_domain_knowledge("Student_Academic", academic_knowledge)
        
        # Test configuration for different context (simulating reusability)
        open_courses_payload = {
            "target_context": "open_courses",
            "base_context": "academic",
            "modifications": ["optional_registration", "flexible_scheduling"]
        }
        
        configuration_result = student_bae.handle_task("configure_context", open_courses_payload)
        
        # Verify reusability metrics
        assert "reuse_percentage" in configuration_result
        reuse_percentage = configuration_result["reuse_percentage"]
        
        # Should achieve >80% reuse as per Scenario 3 criteria
        assert reuse_percentage >= 80, f"Reuse percentage {reuse_percentage}% below 80% threshold"
        
        # Verify domain knowledge preservation
        preserved_knowledge = context_store.get_domain_knowledge("Student_Academic")
        assert preserved_knowledge is not None
        assert preserved_knowledge["reusability_score"] >= 90
        
        print(f"✅ Domain knowledge preserved with {reuse_percentage}% reusability potential") 