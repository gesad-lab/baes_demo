import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class TechLeadSWEA(BaseAgent):
    """
    Technical Lead Software Engineering Autonomous Agent responsible for:
    - Technical architecture decisions and technology stack management
    - Quality gate management and code review authority
    - SWEA coordination and conflict resolution
    - Performance, security, and technical standards enforcement
    - Continuous improvement and optimization oversight

    Acts as the technical governance layer between BAEs and implementation SWEAs.
    """

    def __init__(self):
        super().__init__("TechLeadSWEA", "Technical Leadership and Coordination Agent", "SWEA")
        self.llm_client = OpenAIClient()

        # Technical decision tracking
        self.architecture_decisions = {}
        self.quality_standards = {}
        self.performance_requirements = {}
        self.security_standards = {}

        # SWEA coordination state
        self.active_coordination_plans = {}
        self.swea_performance_metrics = {}
        self.conflict_resolution_history = []

        # Governance history tracking
        self.coordination_history = {}
        self.review_history = []
        self.test_coordination_history = {}

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "coordinate_system_generation": "_coordinate_system_generation",
        "review_and_approve": "_review_and_approve",
        "resolve_technical_conflict": "_resolve_technical_conflict",
        "optimize_architecture": "_optimize_architecture",
        "manage_quality_gate": "_manage_quality_gate",
        "coordinate_test_fixes": "_coordinate_test_fixes",
        "make_tech_decision": "_make_tech_decision",
        "assess_system_health": "_assess_system_health",
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle technical leadership tasks with comprehensive governance"""
        if task == "coordinate_system_generation":
            return self._coordinate_system_generation(payload)
        elif task == "review_and_approve":
            return self._review_and_approve(payload)
        elif task == "resolve_technical_conflict":
            return self._resolve_technical_conflict(payload)
        elif task == "coordinate_test_fixes":
            return self._coordinate_test_fixes(payload)
        elif task == "make_tech_decision":
            return self._make_tech_decision(payload)
        elif task == "assess_system_health":
            return self._assess_system_health(payload)
        elif task == "optimize_architecture":
            return self._optimize_architecture(payload)
        elif task == "manage_quality_gate":
            return self._manage_quality_gate(payload)
        else:
            return {"error": f"Unknown TechLeadSWEA task: {task}", "success": False}

    # ------------------------------------------------------------------
    # Core Coordination Methods
    # ------------------------------------------------------------------

    def _coordinate_system_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate complete system generation with technical governance"""
        try:
            entity = payload.get("entity", "Unknown")
            attributes = payload.get("attributes", [])
            context = payload.get("context", "")
            is_evolution = payload.get("is_evolution", False)
            business_requirements = payload.get("business_requirements", {})

            logger.info("🧠 TechLeadSWEA: Coordinating system generation for %s entity", entity)

            # Analyze technical requirements and create enhanced coordination plan
            technical_analysis = self._analyze_technical_requirements(
                entity, attributes, context, is_evolution
            )

            # Define quality gates based on business requirements
            quality_gates = self._define_quality_gates(business_requirements, is_evolution)

            # Create enhanced coordination plan with technical governance
            enhanced_plan = self._create_enhanced_coordination_plan(
                entity, attributes, context, is_evolution, technical_analysis, quality_gates
            )

            # Store coordination state for tracking
            coordination_id = f"coord_{entity}_{self._get_timestamp()}"
            self.coordination_history[coordination_id] = {
                "entity": entity,
                "attributes": attributes,
                "context": context,
                "is_evolution": is_evolution,
                "technical_analysis": technical_analysis,
                "quality_gates": quality_gates,
                "enhanced_plan": enhanced_plan,
                "status": "coordinating",
                "created_at": self._get_timestamp(),
            }

            return {
                "success": True,
                "data": {
                    "coordination_id": coordination_id,
                    "enhanced_coordination_plan": enhanced_plan,
                    "technical_analysis": technical_analysis,
                    "quality_gates": quality_gates,
                    "governance_strategy": "centralized_technical_oversight",
                    "approval_workflow": "sequential_with_quality_gates",
                },
                "message": f"Technical coordination plan established for {entity}",
                "technical_governance": True,
            }

        except Exception as e:
            logger.error("❌ TechLeadSWEA coordination failed: %s", str(e))
            return {
                "success": False,
                "error": f"Technical coordination failed: {str(e)}",
                "technical_governance": False,
            }

    def _coordinate_test_fixes(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate test failure resolution with SWEA collaboration"""
        try:
            entity = payload.get("entity", "Unknown")
            test_failures = payload.get("test_failures", [])
            coordination_id = payload.get(
                "coordination_id", f"test_fix_{entity}_{self._get_timestamp()}"
            )

            logger.info(
                "🧠 TechLeadSWEA: Coordinating test fixes for %s (%d failures)",
                entity,
                len(test_failures),
            )

            # Analyze test failures and categorize issues
            failure_analysis = self._analyze_test_failures(test_failures)

            # Create fix decisions with SWEA assignments
            fix_decisions = self._create_fix_decisions(failure_analysis, entity)

            # Generate coordination log
            coordination_log = [
                f"Analyzing {len(test_failures)} test failures for {entity}",
                f"Identified {len(failure_analysis.get('categories', []))} issue categories",
                f"Created {len(fix_decisions)} fix decisions",
                f"Coordination strategy: {failure_analysis.get('strategy', 'sequential_fixes')}",
            ]

            # Store coordination state
            self.test_coordination_history[coordination_id] = {
                "entity": entity,
                "test_failures": test_failures,
                "failure_analysis": failure_analysis,
                "fix_decisions": fix_decisions,
                "coordination_log": coordination_log,
                "status": "coordinating_fixes",
                "created_at": self._get_timestamp(),
            }

            return {
                "success": True,
                "data": {
                    "coordination_id": coordination_id,
                    "fix_decisions": fix_decisions,
                    "failure_analysis": failure_analysis,
                    "coordination_log": coordination_log,
                    "estimated_fix_time": self._estimate_fix_time(fix_decisions),
                },
                "message": f"Test fix coordination plan created for {entity}",
                "technical_governance": True,
            }

        except Exception as e:
            logger.error("❌ TechLeadSWEA test coordination failed: %s", str(e))
            return {
                "success": False,
                "error": f"Test coordination failed: {str(e)}",
                "technical_governance": False,
            }

    def _review_and_approve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Review SWEA outputs and make approval decisions with quality gate enforcement"""
        try:
            entity = payload.get("entity", "Unknown")
            swea_agent = payload.get("swea_agent", "")
            task_type = payload.get("task_type", "")
            result = payload.get("result", {})
            quality_gates = payload.get("quality_gates", {})
            final_review = payload.get("final_review", False)

            if final_review:
                return self._conduct_final_system_review(payload)

            logger.info("🧠 TechLeadSWEA: Reviewing %s.%s for %s", swea_agent, task_type, entity)

            # Comprehensive quality assessment
            quality_assessment = self._assess_component_quality(
                swea_agent, task_type, result, quality_gates
            )

            # Technical standards compliance check
            compliance_check = self._check_technical_compliance(swea_agent, task_type, result)

            # Business alignment validation
            business_alignment = self._validate_business_alignment(entity, result)

            # Overall approval decision
            overall_approval = (
                quality_assessment.get("meets_standards", False)
                and compliance_check.get("compliant", False)
                and business_alignment.get("aligned", False)
            )

            # Generate technical feedback
            technical_feedback = []
            if not quality_assessment.get("meets_standards", False):
                technical_feedback.extend(quality_assessment.get("issues", []))
            if not compliance_check.get("compliant", False):
                technical_feedback.extend(compliance_check.get("violations", []))
            if not business_alignment.get("aligned", False):
                technical_feedback.extend(business_alignment.get("misalignments", []))

            # Calculate quality score
            quality_score = self._calculate_quality_score(
                quality_assessment, compliance_check, business_alignment
            )

            # Record review decision
            review_record = {
                "entity": entity,
                "swea_agent": swea_agent,
                "task_type": task_type,
                "quality_score": quality_score,
                "overall_approval": overall_approval,
                "technical_feedback": technical_feedback,
                "reviewed_at": self._get_timestamp(),
                "reviewer": "TechLeadSWEA",
            }
            self.review_history.append(review_record)

            feedback = []
            if not quality_assessment.get("meets_standards", False):
                feedback.extend(quality_assessment.get("issues", []))
            if not compliance_check.get("compliant", False):
                feedback.extend(compliance_check.get("violations", []))
            if not business_alignment.get("aligned", False):
                feedback.extend(business_alignment.get("misalignments", []))

            return {
                "success": True,
                "data": {
                    "overall_approval": overall_approval,
                    "quality_score": quality_score,
                    "technical_feedback": technical_feedback,
                    "entity": entity,
                    "feedback": feedback,
                },
                "message": f"Review completed for {swea_agent}.{task_type}",
                "technical_governance": True,
            }

        except Exception as e:
            logger.error("❌ TechLeadSWEA review failed: %s", str(e))
            return {
                "success": False,
                "error": f"Technical review failed: {str(e)}",
                "overall_approval": False,
                "technical_governance": False,
            }

    def _resolve_technical_conflict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts between different SWEAs or technical approaches."""
        conflict_description = payload.get("conflict_description", "")
        involved_sweas = payload.get("involved_sweas", [])
        entity = payload.get("entity", "Unknown")
        conflict_details = payload.get("conflict_details", {})

        # Analyze the conflict using technical leadership expertise
        conflict_analysis = self._analyze_technical_conflict(
            conflict_description, involved_sweas, conflict_details
        )

        # Make authoritative technical decision
        resolution = self._make_conflict_resolution_decision(conflict_analysis, entity)

        # Create action plan for resolution
        action_plan = self._create_conflict_resolution_plan(resolution, involved_sweas)

        # Log conflict resolution for future reference
        self.conflict_resolution_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "entity": entity,
                "conflict": conflict_description,
                "involved_sweas": involved_sweas,
                "resolution": resolution,
                "action_plan": action_plan,
            }
        )

        resolution_result = {
            "entity": entity,
            "conflict_resolved": True,
            "resolution_decision": resolution,
            "action_plan": action_plan,
            "involved_sweas": involved_sweas,
            "technical_rationale": conflict_analysis["technical_rationale"],
            "implementation_priority": resolution.get("priority", "medium"),
        }

        return self.create_success_response("resolve_technical_conflict", resolution_result)

    # ------------------------------------------------------------------
    # Technical Decision Making Methods
    # ------------------------------------------------------------------

    def _make_architecture_decisions(
        self, entity: str, business_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make technical architecture decisions based on business requirements."""

        # Use LLM to analyze requirements and make architecture decisions
        prompt = f"""
        As a Technical Lead, make architecture decisions for the {entity} entity system.

        Business Requirements: {json.dumps(business_requirements, indent=2)}

        Make decisions on:
        1. Database design patterns (normalization level, indexing strategy)
        2. API design patterns (RESTful principles, error handling)
        3. UI/UX patterns (component organization, state management)
        4. Testing strategy (unit, integration, e2e coverage)
        5. Performance requirements (response times, scalability)
        6. Security considerations (validation, sanitization, auth)

        Return JSON with specific technical decisions and rationales.
        """

        response = self.llm_client.generate_response(prompt, temperature=0)

        try:
            arch_decisions = json.loads(response)
        except json.JSONDecodeError:
            # Fallback with default technical decisions
            arch_decisions = {
                "database_strategy": "normalized_sqlite_with_indexes",
                "api_pattern": "restful_crud_with_validation",
                "ui_pattern": "component_based_streamlit",
                "testing_strategy": "comprehensive_pyramid",
                "performance_targets": {"api_response": "< 200ms", "ui_load": "< 2s"},
                "security_requirements": [
                    "input_validation",
                    "email_sanitization",
                    "sql_injection_prevention",
                ],
            }

        # Store decisions for future reference
        self.architecture_decisions[entity] = arch_decisions

        return arch_decisions

    def _analyze_test_failure_and_decide(
        self, failure: Dict[str, Any], entity: str
    ) -> Dict[str, Any]:
        """Analyze test failure and make technical decision on how to fix it."""

        # failure_type = failure.get("category", "unknown")  # Currently unused
        error_details = failure.get("stderr", "") + " " + failure.get("stdout", "")

        # Technical decision matrix based on failure analysis
        if "ModuleNotFoundError" in error_details or "ImportError" in error_details:
            return {
                "issue_type": "dependency_management",
                "responsible_swea": "BackendSWEA",
                "recommended_action": "fix_dependencies",
                "priority": "high",
                "technical_rationale": "Missing dependencies block all functionality",
                "fix_context": {"error_details": error_details, "issue_type": "missing_dependency"},
            }

        elif "ValidationError" in error_details or "pydantic" in error_details.lower():
            if "empty" in error_details.lower() or "length" in error_details.lower():
                return {
                    "issue_type": "business_validation_mismatch",
                    "responsible_swea": "BackendSWEA",
                    "recommended_action": "update_model_validation",
                    "priority": "medium",
                    "technical_rationale": "Business rules should be enforced at model level",
                    "fix_context": {
                        "error_details": error_details,
                        "issue_type": "validation_rule",
                    },
                }
            else:
                return {
                    "issue_type": "test_expectation_mismatch",
                    "responsible_swea": "TestSWEA",
                    "recommended_action": "update_test_expectations",
                    "priority": "medium",
                    "technical_rationale": "Test expectations should match current Pydantic v2 behavior",
                    "fix_context": {
                        "error_details": error_details,
                        "issue_type": "test_expectation",
                    },
                }

        elif "SyntaxError" in error_details or "IndentationError" in error_details:
            return {
                "issue_type": "code_generation_quality",
                "responsible_swea": "BackendSWEA",
                "recommended_action": "fix_code_syntax",
                "priority": "high",
                "technical_rationale": "Syntax errors indicate code generation issues",
                "fix_context": {"error_details": error_details, "issue_type": "syntax_error"},
            }

        else:
            return {
                "issue_type": "general_technical_issue",
                "responsible_swea": "BackendSWEA",  # Default to backend for unknown issues
                "recommended_action": "investigate_and_fix",
                "priority": "medium",
                "technical_rationale": "Unknown issues require investigation",
                "fix_context": {"error_details": error_details, "issue_type": "unknown"},
            }

    def _create_swea_fix_task(
        self, fix_decision: Dict[str, Any], failure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a specific task for a SWEA to fix an issue."""
        return {
            "responsible_swea": fix_decision["responsible_swea"],
            "task_type": fix_decision["recommended_action"],
            "task_description": f"Fix {fix_decision['issue_type']} issue",
            "priority": fix_decision["priority"],
            "context": fix_decision.get("fix_context", {}),
            "original_failure": failure,
            "technical_requirements": self._get_fix_requirements(fix_decision),
        }

    def _get_fix_requirements(self, fix_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific technical requirements for fixing an issue."""
        issue_type = fix_decision.get("issue_type", "")

        if issue_type == "dependency_management":
            return {
                "update_requirements_txt": True,
                "install_missing_packages": True,
                "validate_compatibility": True,
            }
        elif issue_type == "business_validation_mismatch":
            return {
                "add_field_validation": True,
                "preserve_business_rules": True,
                "maintain_backward_compatibility": True,
            }
        elif issue_type == "test_expectation_mismatch":
            return {
                "update_error_message_expectations": True,
                "align_with_pydantic_v2": True,
                "maintain_test_coverage": True,
            }

        return {"investigate_thoroughly": True, "document_changes": True}

    def _define_next_steps(self, fix_decisions: List[Dict[str, Any]]) -> List[str]:
        """Define next steps after coordinating test fixes."""
        next_steps = []

        high_priority_count = sum(1 for decision in fix_decisions if decision["priority"] == "high")
        if high_priority_count > 0:
            next_steps.append(f"Address {high_priority_count} high-priority issues immediately")

        swea_groups = {}
        for decision in fix_decisions:
            swea = decision["responsible_swea"]
            if swea not in swea_groups:
                swea_groups[swea] = []
            swea_groups[swea].append(decision["issue_type"])

        for swea, issues in swea_groups.items():
            next_steps.append(f"{swea} should address: {', '.join(issues)}")

        next_steps.append("Re-run tests after all fixes are applied")
        next_steps.append("TechLeadSWEA will review and approve fixes")

        return next_steps

    def _create_enhanced_coordination_plan(
        self,
        entity: str,
        attributes: List[str],
        context: str,
        is_evolution: bool,
        technical_analysis: Dict[str, Any],
        quality_gates: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Create enhanced coordination plan with technical governance"""
        base_plan = [
            {
                "swea_agent": "DatabaseSWEA",
                "task_type": "setup_database" if not is_evolution else "migrate_schema",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "preserve_data": is_evolution,
                    "business_rules": True,
                },
                "priority": 1,
                "requires_approval": True,
                "technical_requirements": technical_analysis.get("database_requirements", {}),
                "quality_criteria": quality_gates.get("business_alignment", {}),
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "domain_focus": True,
                    "semantic_coherence": True,
                },
                "priority": 2,
                "requires_approval": True,
                "technical_requirements": technical_analysis.get("api_requirements", {}),
                "quality_criteria": quality_gates.get("code_quality", {}),
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_api",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "crud_operations": True,
                    "business_vocabulary": True,
                },
                "priority": 3,
                "requires_approval": True,
                "technical_requirements": technical_analysis.get("api_requirements", {}),
                "quality_criteria": quality_gates.get("performance", {}),
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "business_vocabulary": True,
                    "user_friendly": True,
                },
                "priority": 4,
                "requires_approval": True,
                "technical_requirements": technical_analysis.get("ui_requirements", {}),
                "quality_criteria": quality_gates.get("business_alignment", {}),
            },
            {
                "swea_agent": "TestSWEA",
                "task_type": "generate_all_tests_with_collaboration",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "test_types": ["unit", "integration", "api"],
                    "coverage_target": "comprehensive",
                },
                "priority": 5,
                "requires_approval": True,
                "technical_requirements": technical_analysis.get("testing_requirements", {}),
                "quality_criteria": quality_gates.get("test_coverage", {}),
            },
        ]

        return base_plan

    def _define_quality_gates(
        self, business_requirements: Dict[str, Any], is_evolution: bool
    ) -> Dict[str, Any]:
        """Define quality gates based on business requirements"""
        return {
            "code_quality": {
                "min_score": 8.0,
                "linting": "strict",
                "formatting": "black_compliant",
                "complexity": "low_to_medium",
            },
            "test_coverage": {"minimum": 85, "target": 95, "critical_paths": 100},
            "performance": {
                "api_response_time": 200,  # ms
                "ui_load_time": 2000,  # ms
                "database_query_time": 100,  # ms
            },
            "security": {
                "input_validation": "comprehensive",
                "sql_injection_protection": "enabled",
                "xss_protection": "enabled",
            },
            "business_alignment": {
                "vocabulary_preservation": "strict",
                "domain_coherence": "high",
                "semantic_consistency": "enforced",
            },
        }

    def _analyze_technical_requirements(
        self, entity: str, attributes: List[str], context: str, is_evolution: bool
    ) -> Dict[str, Any]:
        """Analyze technical requirements for system generation"""
        return {
            "complexity_level": "medium" if len(attributes) <= 5 else "high",
            "database_requirements": {
                "tables_needed": 1,
                "relationships": "minimal" if not is_evolution else "preserve_existing",
                "indexes": ["primary_key", "business_key"],
                "constraints": ["not_null", "unique_business_key"],
            },
            "api_requirements": {
                "endpoints": 5,  # CRUD + list
                "authentication": "basic",
                "validation": "comprehensive",
                "error_handling": "production_ready",
            },
            "ui_requirements": {
                "components": ["list", "create", "edit", "delete"],
                "responsiveness": "mobile_ready",
                "accessibility": "wcag_aa",
            },
            "testing_requirements": {
                "coverage_target": 90,
                "test_types": ["unit", "integration", "api"],
                "automation": "full",
            },
            "performance_targets": {
                "api_response": "< 200ms",
                "ui_load": "< 2s",
                "database_query": "< 100ms",
            },
        }

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def _review_artifact(self, artifact: Dict[str, Any], entity: str) -> Dict[str, Any]:
        """Review a single artifact for quality and compliance."""

        artifact_type = artifact.get("type", "unknown")
        artifact_content = artifact.get("content", "")

        # Basic quality checks
        syntax_valid = (
            "class " in artifact_content or "def " in artifact_content or "@" in artifact_content
        )
        has_documentation = '"""' in artifact_content or "# " in artifact_content
        follows_naming_conventions = entity.lower() in artifact_content.lower()

        # Calculate approval score
        quality_checks = {
            "syntax_valid": syntax_valid,
            "has_documentation": has_documentation,
            "follows_naming_conventions": follows_naming_conventions,
            "content_length_adequate": len(artifact_content) > 100,
        }

        approval_score = sum(quality_checks.values()) / len(quality_checks)
        approved = approval_score >= 0.75  # 75% quality threshold

        feedback = []
        if not syntax_valid:
            feedback.append("Improve code syntax and structure")
        if not has_documentation:
            feedback.append("Add comprehensive documentation")
        if not follows_naming_conventions:
            feedback.append(f"Ensure naming conventions include {entity} entity reference")

        return {
            "artifact_type": artifact_type,
            "approved": approved,
            "quality_score": approval_score,
            "quality_checks": quality_checks,
            "feedback": feedback,
        }

    def _determine_next_actions(
        self, overall_approval: bool, technical_feedback: List[str]
    ) -> List[str]:
        """Determine next actions based on review results"""
        if overall_approval:
            return ["Proceed with deployment", "Monitor system performance"]
        else:
            actions = ["Address technical feedback", "Re-run quality gates"]
            if technical_feedback:
                actions.extend([f"Fix: {feedback}" for feedback in technical_feedback[:3]])
            return actions

    def _analyze_test_failures(self, test_failures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test failures and categorize issues"""
        categories = {}
        strategy = "sequential_fixes"

        for failure in test_failures:
            category = failure.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(failure)

        return {
            "categories": categories,
            "total_failures": len(test_failures),
            "strategy": strategy,
            "priority": "high" if len(test_failures) > 5 else "medium",
        }

    def _create_fix_decisions(
        self, failure_analysis: Dict[str, Any], entity: str
    ) -> List[Dict[str, Any]]:
        """Create fix decisions with SWEA assignments"""
        fix_decisions = []
        categories = failure_analysis.get("categories", {})

        for category, failures in categories.items():
            if category == "import_error":
                fix_decisions.append(
                    {
                        "issue_type": "import_error",
                        "responsible_swea": "BackendSWEA",
                        "recommended_action": "fix_import_paths",
                        "priority": "high",
                        "estimated_effort": "low",
                    }
                )
            elif category == "test_execution_failure":
                fix_decisions.append(
                    {
                        "issue_type": "test_execution_failure",
                        "responsible_swea": "TestSWEA",
                        "recommended_action": "fix_test_configuration",
                        "priority": "high",
                        "estimated_effort": "medium",
                    }
                )
            elif category == "api_error":
                fix_decisions.append(
                    {
                        "issue_type": "api_error",
                        "responsible_swea": "BackendSWEA",
                        "recommended_action": "fix_api_endpoints",
                        "priority": "medium",
                        "estimated_effort": "medium",
                    }
                )
            else:
                fix_decisions.append(
                    {
                        "issue_type": category,
                        "responsible_swea": "BackendSWEA",
                        "recommended_action": "general_fix",
                        "priority": "medium",
                        "estimated_effort": "medium",
                    }
                )

        return fix_decisions

    def _estimate_fix_time(self, fix_decisions: List[Dict[str, Any]]) -> int:
        """Estimate total fix time in minutes"""
        effort_map = {"low": 5, "medium": 15, "high": 30}
        total_time = 0

        for decision in fix_decisions:
            effort = decision.get("estimated_effort", "medium")
            total_time += effort_map.get(effort, 15)

        return total_time

    def _assess_component_quality(
        self, swea_agent: str, task_type: str, result: Dict[str, Any], quality_gates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess quality of SWEA component output"""
        meets_standards = True
        issues = []

        # Basic quality checks
        if not result.get("success", False):
            meets_standards = False
            issues.append("Task execution failed")

        # Agent-specific quality checks - Updated to match actual SWEA response format
        data = result.get("data", {})
        
        if "Backend" in swea_agent:
            if "generate_model" in task_type:
                # BackendSWEA returns "code" not "model_code"
                if not data.get("code"):
                    meets_standards = False
                    issues.append("Missing model code generation")
                else:
                    # Validate that it looks like a Pydantic model
                    code = data.get("code", "")
                    if "BaseModel" not in code or "class " not in code:
                        meets_standards = False
                        issues.append("Generated code doesn't appear to be a valid Pydantic model")
                        
            elif "generate_api" in task_type:
                # BackendSWEA returns "code" not "api_code"
                if not data.get("code"):
                    meets_standards = False
                    issues.append("Missing API code generation")
                else:
                    # Validate that it looks like FastAPI code
                    code = data.get("code", "")
                    if "APIRouter" not in code or "from fastapi import" not in code:
                        meets_standards = False
                        issues.append("Generated code doesn't appear to be valid FastAPI routes")

        elif "Frontend" in swea_agent:
            # FrontendSWEA returns "code" not "ui_code"
            if not data.get("code"):
                meets_standards = False
                issues.append("Missing UI code generation")
            else:
                # Validate that it looks like Streamlit code
                code = data.get("code", "")
                if "streamlit" not in code.lower() or "st." not in code:
                    meets_standards = False
                    issues.append("Generated code doesn't appear to be valid Streamlit UI")

        elif "Database" in swea_agent:
            # DatabaseSWEA validation - appropriate for database operations
            if "setup_database" in task_type:
                # Check for database path or creation confirmation
                database_path = data.get("database_path")
                tables_created = data.get("tables_created", [])
                
                if not database_path and not tables_created:
                    meets_standards = False
                    issues.append("Missing database creation confirmation")
                else:
                    # Validate database setup details
                    if database_path and not database_path.endswith('.db'):
                        meets_standards = False
                        issues.append("Invalid database file path format")
                    
                    if not tables_created or len(tables_created) == 0:
                        meets_standards = False
                        issues.append("No database tables were created")
            
            elif "migrate_schema" in task_type:
                # Check for migration confirmation
                migration_applied = data.get("migration_applied", False)
                if not migration_applied:
                    meets_standards = False
                    issues.append("Schema migration was not applied successfully")

        return {
            "meets_standards": meets_standards,
            "issues": issues,
            "quality_level": "high" if meets_standards else "low",
        }

    def _check_technical_compliance(
        self, swea_agent: str, task_type: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check technical standards compliance"""
        compliant = True
        violations = []

        # Check for basic compliance indicators
        data = result.get("data", {})

        if "Backend" in swea_agent:
            # Check for proper code structure - Updated to use actual SWEA response format
            if "generate_model" in task_type:
                # BackendSWEA returns "code" not "model_code"
                model_code = data.get("code", "")
                if "from pydantic import BaseModel" not in model_code:
                    compliant = False
                    violations.append("Missing Pydantic BaseModel import")

            elif "generate_api" in task_type:
                # BackendSWEA returns "code" not "api_code" 
                api_code = data.get("code", "")
                if "from fastapi import" not in api_code:
                    compliant = False
                    violations.append("Missing FastAPI imports")

        return {
            "compliant": compliant,
            "violations": violations,
            "compliance_level": "high" if compliant else "low",
        }

    def _validate_business_alignment(self, entity: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business alignment of SWEA output"""
        try:
            # Check if result contains expected business vocabulary
            result_content = str(result).lower()
            entity_lower = entity.lower()
            
            # Get the task type to determine appropriate validation
            task_type = result.get("task", "")
            swea_agent = ""
            if "database" in task_type.lower():
                swea_agent = "Database"
            elif "backend" in task_type.lower() or "model" in task_type.lower() or "api" in task_type.lower():
                swea_agent = "Backend"
            elif "frontend" in task_type.lower() or "ui" in task_type.lower():
                swea_agent = "Frontend"

            misalignments = []
            
            if "Database" in swea_agent:
                # DatabaseSWEA business alignment - focus on data persistence and structure
                has_entity_reference = entity_lower in result_content
                has_database_terms = any(term in result_content for term in ["table", "database", "schema", "column"])
                
                if not has_entity_reference:
                    misalignments.append(f"Missing {entity} entity reference in database setup")
                if not has_database_terms:
                    misalignments.append("Missing database-specific vocabulary")
                
                semantic_coherence = has_entity_reference and has_database_terms
                
            else:
                # Code-generating SWEAs (Backend/Frontend) - original validation logic
                has_entity_reference = entity_lower in result_content
                follows_naming_convention = entity_lower in result_content and (
                    "model" in result_content or "class" in result_content
                )

                # Domain-specific vocabulary preservation
                business_terms = ["create", "read", "update", "delete", "list"]
                has_business_terms = any(term in result_content for term in business_terms)

                # Semantic coherence check
                semantic_coherence = has_entity_reference and has_business_terms

                if not has_entity_reference:
                    misalignments.append(f"Missing {entity} entity reference")
                if not follows_naming_convention:
                    misalignments.append("Naming convention not followed")
                if not has_business_terms:
                    misalignments.append("Missing business vocabulary terms")

            return {
                "aligned": len(misalignments) == 0,
                "alignment_score": 1.0 - (len(misalignments) / max(1, len(misalignments))),
                "misalignments": misalignments,
                "semantic_coherence": semantic_coherence,
            }

        except Exception as e:
            return {
                "aligned": False,
                "alignment_score": 0.0,
                "misalignments": [f"Business alignment validation failed: {str(e)}"],
                "semantic_coherence": False,
            }

    def _calculate_quality_score(
        self,
        quality_assessment: Dict[str, Any],
        compliance_check: Dict[str, Any],
        business_alignment: Dict[str, Any],
    ) -> float:
        """Calculate overall quality score"""
        quality_weight = 0.4
        compliance_weight = 0.3
        alignment_weight = 0.3

        quality_score = 1.0 if quality_assessment.get("meets_standards", False) else 0.0
        compliance_score = 1.0 if compliance_check.get("compliant", False) else 0.0
        alignment_score = business_alignment.get("alignment_score", 0.0)

        overall_score = (
            quality_score * quality_weight
            + compliance_score * compliance_weight
            + alignment_score * alignment_weight
        )

        return round(overall_score, 2)

    def _conduct_final_system_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct final comprehensive system review"""
        try:
            entity = payload.get("entity", "Unknown")
            execution_results = payload.get("execution_results", [])

            logger.info("🧠 TechLeadSWEA: Conducting final system review for %s", entity)

            # Analyze all execution results
            overall_success = True
            component_reviews = []

            for result in execution_results:
                if result.get("success", False):
                    component_reviews.append(
                        {
                            "component": result.get("task", "unknown"),
                            "status": "approved",
                            "quality_score": result.get("quality_score", 0.8),
                        }
                    )
                else:
                    overall_success = False
                    component_reviews.append(
                        {
                            "component": result.get("task", "unknown"),
                            "status": "rejected",
                            "issues": [result.get("error", "Unknown error")],
                        }
                    )

            # System integration assessment
            integration_score = self._assess_system_integration(execution_results)

            # Deployment readiness check
            deployment_ready = overall_success and integration_score > 0.7

            final_recommendations = []
            if deployment_ready:
                final_recommendations.extend(
                    [
                        "System meets technical standards for deployment",
                        "All quality gates passed successfully",
                        "Recommended for production deployment",
                    ]
                )
            else:
                final_recommendations.extend(
                    [
                        "System requires additional work before deployment",
                        "Address component issues identified in review",
                        "Re-run quality gates after fixes",
                    ]
                )

            return {
                "success": True,
                "data": {
                    "overall_approval": deployment_ready,
                    "system_quality_score": integration_score,
                    "component_reviews": component_reviews,
                    "deployment_ready": deployment_ready,
                    "final_recommendations": final_recommendations,
                    "review_summary": {
                        "total_components": len(execution_results),
                        "approved_components": len(
                            [r for r in component_reviews if r["status"] == "approved"]
                        ),
                        "rejected_components": len(
                            [r for r in component_reviews if r["status"] == "rejected"]
                        ),
                    },
                },
                "message": f"Final system review completed for {entity}",
                "technical_governance": True,
            }

        except Exception as e:
            logger.error("❌ TechLeadSWEA final review failed: %s", str(e))
            return {
                "success": False,
                "error": f"Final system review failed: {str(e)}",
                "overall_approval": False,
                "technical_governance": False,
            }

    def _assess_system_integration(self, execution_results: List[Dict[str, Any]]) -> float:
        """Assess overall system integration quality"""
        if not execution_results:
            return 0.0

        successful_components = len([r for r in execution_results if r.get("success", False)])
        total_components = len(execution_results)

        integration_score = successful_components / total_components

        # Bonus for having all core components
        core_components = ["DatabaseSWEA", "BackendSWEA", "FrontendSWEA"]
        present_core = [
            c for c in core_components if any(c in r.get("task", "") for r in execution_results)
        ]

        if len(present_core) == len(core_components):
            integration_score += 0.1  # 10% bonus for complete system

        return min(integration_score, 1.0)

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")
