"""
Integration tests for TechLeadSWEA centralized governance functionality.
Validates that TechLeadSWEA acts as the "Technical Brain" of the BAE system.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
from baes.domain_entities.academic.student_bae import StudentBae
from baes.swea_agents.techlead_swea import TechLeadSWEA


class TestTechLeadGovernance:
    """Test TechLeadSWEA centralized governance and coordination"""

    @pytest.fixture(autouse=True)
    def setup_temp_environment(self):
        """Setup temporary environment for tests"""
        # Set environment variable for managed system path
        self.temp_dir = tempfile.mkdtemp()
        os.environ["MANAGED_SYSTEM_PATH"] = os.path.join(self.temp_dir, "managed_system")
        yield
        # Cleanup is handled by tempfile module

    @pytest.fixture
    def runtime_kernel(self):
        """Create runtime kernel for testing"""
        return EnhancedRuntimeKernel()

    @pytest.fixture
    def student_bae(self):
        """Create student BAE for testing"""
        return StudentBae()

    @pytest.fixture
    def techlead_swea(self):
        """Create TechLeadSWEA for testing"""
        return TechLeadSWEA()

    def test_techlead_coordinates_system_generation(self, runtime_kernel, student_bae):
        """Test that TechLeadSWEA coordinates initial system generation"""

        # Mock the coordination plan interpretation
        with patch.object(student_bae, "handle_task") as mock_handle_task:
            mock_handle_task.return_value = {
                "success": True,
                "data": {
                    "entity": "Student",
                    "attributes": ["name: str", "email: str", "age: int"],
                    "swea_coordination": [
                        {
                            "swea_agent": "TechLeadSWEA",
                            "task_type": "coordinate_system_generation",
                            "payload": {
                                "entity": "Student",
                                "attributes": ["name: str", "email: str", "age: int"],
                                "context": "Create student management system",
                                "business_requirements": {
                                    "domain_focus": True,
                                    "semantic_coherence": True,
                                    "quality_gates": True,
                                    "technical_governance": True,
                                },
                            },
                        },
                        {
                            "swea_agent": "DatabaseSWEA",
                            "task_type": "setup_database",
                            "payload": {"attributes": ["name: str", "email: str", "age: int"]},
                        },
                        {
                            "swea_agent": "BackendSWEA",
                            "task_type": "generate_model",
                            "payload": {"attributes": ["name: str", "email: str", "age: int"]},
                        },
                    ],
                },
            }

            # Mock SWEA responses
            with patch.object(runtime_kernel.techlead_swea, "handle_task") as mock_techlead:
                mock_techlead.return_value = {
                    "success": True,
                    "data": {
                        "coordination_id": "coord_Student_20241201_120000",
                        "enhanced_coordination_plan": [],
                        "technical_analysis": {"complexity_level": "medium"},
                        "quality_gates": {"code_quality": {"min_score": 8.0}},
                        "governance_strategy": "centralized_technical_oversight",
                    },
                    "technical_governance": True,
                }

                with patch.object(runtime_kernel.database_swea, "handle_task") as mock_db:
                    mock_db.return_value = {"success": True, "data": {"database_setup": True}}

                    with patch.object(runtime_kernel.backend_swea, "handle_task") as mock_backend:
                        mock_backend.return_value = {
                            "success": True,
                            "data": {"model_code": "class Student(BaseModel): pass"},
                        }

                        # Execute coordination plan
                        result = runtime_kernel._execute_coordination_plan(
                            mock_handle_task.return_value["data"]["swea_coordination"],
                            student_bae,
                            "Create student management system",
                        )

                        # Verify TechLeadSWEA was called for coordination
                        assert mock_techlead.called
                        techlead_calls = [
                            call
                            for call in mock_techlead.call_args_list
                            if call[0][0] == "coordinate_system_generation"
                        ]
                        assert len(techlead_calls) > 0

                        # Verify technical governance is applied
                        assert any(r.get("technical_governance") for r in result)

                        # Verify coordination result includes TechLeadSWEA oversight
                        techlead_results = [
                            r for r in result if "TechLeadSWEA" in r.get("task", "")
                        ]
                        assert len(techlead_results) > 0

    def test_techlead_reviews_and_approves_swea_outputs(self, techlead_swea):
        """Test that TechLeadSWEA reviews and approves SWEA outputs"""

        # Test successful review
        review_payload = {
            "entity": "Student",
            "swea_agent": "BackendSWEA",
            "task_type": "generate_model",
            "result": {
                "success": True,
                "data": {
                    "model_code": "from pydantic import BaseModel\n\nclass Student(BaseModel):\n    name: str\n    email: str"
                },
            },
            "quality_gates": {"code_quality": {"min_score": 8.0}},
        }

        result = techlead_swea.handle_task("review_and_approve", review_payload)

        assert result["success"] is True
        assert "data" in result
        assert "overall_approval" in result["data"]
        assert "quality_score" in result["data"]
        assert "technical_feedback" in result["data"]
        assert result.get("technical_governance") is True

    def test_techlead_coordinates_test_failure_resolution(self, techlead_swea):
        """Test that TechLeadSWEA coordinates test failure resolution"""

        test_failure_payload = {
            "entity": "Student",
            "test_failures": [
                {
                    "category": "import_error",
                    "stderr": "ModuleNotFoundError: No module named 'student_model'",
                    "stdout": "",
                    "execution_results": [],
                },
                {
                    "category": "api_error",
                    "stderr": "404 Not Found",
                    "stdout": "",
                    "execution_results": [],
                },
            ],
            "coordination_id": "test_fix_Student_20241201_120000",
        }

        result = techlead_swea.handle_task("coordinate_test_fixes", test_failure_payload)

        assert result["success"] is True
        assert "data" in result
        assert "fix_decisions" in result["data"]
        assert "coordination_log" in result["data"]
        assert (
            len(result["data"]["fix_decisions"]) == 2
        )  # Two failures should generate two fix decisions
        assert result.get("technical_governance") is True

        # Verify fix decisions have proper SWEA assignments
        fix_decisions = result["data"]["fix_decisions"]
        assert any(d["responsible_swea"] == "BackendSWEA" for d in fix_decisions)

    def test_techlead_defines_quality_gates(self, techlead_swea):
        """Test that TechLeadSWEA defines comprehensive quality gates"""

        business_requirements = {
            "domain_focus": True,
            "semantic_coherence": True,
            "quality_gates": True,
            "technical_governance": True,
        }

        quality_gates = techlead_swea._define_quality_gates(business_requirements, False)

        # Verify comprehensive quality gates are defined
        assert "code_quality" in quality_gates
        assert "test_coverage" in quality_gates
        assert "performance" in quality_gates
        assert "security" in quality_gates
        assert "business_alignment" in quality_gates

        # Verify specific quality criteria
        assert quality_gates["code_quality"]["min_score"] == 8.0
        assert quality_gates["test_coverage"]["minimum"] == 85
        assert quality_gates["performance"]["api_response_time"] == 200
        assert quality_gates["business_alignment"]["vocabulary_preservation"] == "strict"

    def test_techlead_technical_analysis(self, techlead_swea):
        """Test that TechLeadSWEA performs comprehensive technical analysis"""

        attributes = ["name: str", "email: str", "age: int", "enrollment_date: date"]
        analysis = techlead_swea._analyze_technical_requirements(
            "Student", attributes, "Academic system", False
        )

        # Verify comprehensive technical analysis
        assert "complexity_level" in analysis
        assert "database_requirements" in analysis
        assert "api_requirements" in analysis
        assert "ui_requirements" in analysis
        assert "testing_requirements" in analysis
        assert "performance_targets" in analysis

        # Verify complexity assessment
        assert analysis["complexity_level"] == "medium"  # 4 attributes = medium complexity

        # Verify specific requirements
        assert analysis["database_requirements"]["tables_needed"] == 1
        assert analysis["api_requirements"]["endpoints"] == 5  # CRUD + list
        assert analysis["testing_requirements"]["coverage_target"] == 90

    def test_techlead_final_system_review(self, techlead_swea):
        """Test that TechLeadSWEA conducts final system review"""

        execution_results = [
            {
                "task": "TechLeadSWEA.coordinate_system_generation",
                "success": True,
                "result": {"coordination_id": "coord_123"},
                "technical_governance": True,
            },
            {
                "task": "DatabaseSWEA.setup_database",
                "success": True,
                "result": {"database_setup": True},
                "technical_review": "approved",
                "quality_score": 0.9,
            },
            {
                "task": "BackendSWEA.generate_model",
                "success": True,
                "result": {"model_code": "class Student(BaseModel): pass"},
                "technical_review": "approved",
                "quality_score": 0.85,
            },
            {
                "task": "FrontendSWEA.generate_ui",
                "success": True,
                "result": {"ui_code": "def main(): st.title('Student Management')"},
                "technical_review": "approved",
                "quality_score": 0.8,
            },
        ]

        final_review_payload = {
            "entity": "Student",
            "execution_results": execution_results,
            "context": "Student management system",
            "final_review": True,
        }

        result = techlead_swea.handle_task("review_and_approve", final_review_payload)

        assert result["success"] is True
        assert "data" in result
        assert "overall_approval" in result["data"]
        assert "system_quality_score" in result["data"]
        assert "deployment_ready" in result["data"]
        assert "final_recommendations" in result["data"]
        assert result.get("technical_governance") is True

        # Verify system integration assessment
        data = result["data"]
        assert data["system_quality_score"] > 0.7  # Should be high with all successful components
        assert data["deployment_ready"] is True
        assert len(data["final_recommendations"]) > 0

    def test_techlead_integration_with_runtime_kernel(self, runtime_kernel):
        """Test complete integration of TechLeadSWEA with runtime kernel"""

        # Mock a complete workflow with TechLeadSWEA governance
        request = "Create a student management system with name, email, and age"

        with patch.object(runtime_kernel.bae_registry, "get_bae") as mock_get_bae:
            mock_bae = Mock()
            mock_bae.entity_name = "Student"
            mock_bae.handle_task.return_value = {
                "success": True,
                "data": {
                    "entity": "Student",
                    "attributes": ["name: str", "email: str", "age: int"],
                    "swea_coordination": [
                        {
                            "swea_agent": "TechLeadSWEA",
                            "task_type": "coordinate_system_generation",
                            "payload": {
                                "entity": "Student",
                                "attributes": ["name: str", "email: str", "age: int"],
                            },
                        }
                    ],
                },
            }
            mock_get_bae.return_value = mock_bae

            with patch.object(runtime_kernel.techlead_swea, "handle_task") as mock_techlead:
                mock_techlead.return_value = {
                    "success": True,
                    "data": {
                        "coordination_id": "coord_Student_123",
                        "enhanced_coordination_plan": [],
                        "technical_analysis": {"complexity_level": "medium"},
                        "quality_gates": {"code_quality": {"min_score": 8.0}},
                        "governance_strategy": "centralized_technical_oversight",
                    },
                    "technical_governance": True,
                }

                with patch.object(runtime_kernel.managed_system_manager, "create_managed_system"):
                    with patch.object(runtime_kernel.managed_system_manager, "start_servers"):

                        result = runtime_kernel.process_natural_language_request(
                            request, start_servers=False
                        )

                        # Verify TechLeadSWEA was involved in the process
                        assert result["success"] is True
                        assert mock_techlead.called

                        # Verify technical governance is maintained throughout
                        execution_results = result.get("execution_results", [])
                        techlead_involvement = any(
                            r.get("technical_governance") for r in execution_results
                        )
                        assert techlead_involvement

    def test_techlead_quality_assessment_comprehensive(self, techlead_swea):
        """Test comprehensive quality assessment by TechLeadSWEA"""

        # Test quality assessment for different SWEA outputs
        test_cases = [
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "result": {
                    "success": True,
                    "data": {
                        "model_code": "from pydantic import BaseModel\n\nclass Student(BaseModel):\n    name: str"
                    },
                },
                "expected_quality": True,
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "result": {"success": False, "error": "Generation failed"},
                "expected_quality": False,
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "result": {
                    "success": True,
                    "data": {
                        "ui_code": "import streamlit as st\n\ndef main():\n    st.title('Student Management')"
                    },
                },
                "expected_quality": True,
            },
        ]

        for case in test_cases:
            quality_assessment = techlead_swea._assess_component_quality(
                case["swea_agent"], case["task_type"], case["result"], {}
            )

            assert quality_assessment["meets_standards"] == case["expected_quality"]
            assert "issues" in quality_assessment
            assert "quality_level" in quality_assessment

    def test_techlead_maintains_governance_state(self, techlead_swea):
        """Test that TechLeadSWEA maintains governance state and history"""

        # Test coordination history tracking
        coordination_payload = {
            "entity": "Student",
            "attributes": ["name: str", "email: str"],
            "context": "Test system",
            "is_evolution": False,
            "business_requirements": {"domain_focus": True},
        }

        result = techlead_swea.handle_task("coordinate_system_generation", coordination_payload)

        assert result["success"] is True
        coordination_id = result["data"]["coordination_id"]

        # Verify coordination state is stored
        assert coordination_id in techlead_swea.coordination_history
        stored_coordination = techlead_swea.coordination_history[coordination_id]
        assert stored_coordination["entity"] == "Student"
        assert stored_coordination["status"] == "coordinating"

        # Test review history tracking
        review_payload = {
            "entity": "Student",
            "swea_agent": "BackendSWEA",
            "task_type": "generate_model",
            "result": {"success": True, "data": {"model_code": "class Student: pass"}},
            "quality_gates": {},
        }

        review_result = techlead_swea.handle_task("review_and_approve", review_payload)

        assert review_result["success"] is True

        # Verify review history is maintained
        assert len(techlead_swea.review_history) > 0
        latest_review = techlead_swea.review_history[-1]
        assert latest_review["entity"] == "Student"
        assert latest_review["swea_agent"] == "BackendSWEA"
        assert latest_review["reviewer"] == "TechLeadSWEA"


if __name__ == "__main__":
    pytest.main([__file__])
