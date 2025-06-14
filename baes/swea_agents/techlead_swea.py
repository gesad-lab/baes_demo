import json
from datetime import datetime
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient


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
        """Dispatch task to internal coordination and decision-making methods."""
        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                f"Unknown task. Supported tasks: {list(self._SUPPORTED_TASKS.keys())}",
                "invalid_task",
            )

        method = getattr(self, self._SUPPORTED_TASKS[task])
        try:
            return method(payload)
        except Exception as e:
            return self.create_error_response(task, str(e), "execution_error")

    # ------------------------------------------------------------------
    # Core Coordination Methods
    # ------------------------------------------------------------------

    def _coordinate_system_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate the entire system generation process across all SWEAs."""
        entity = payload.get("entity", "Unknown")
        business_requirements = payload.get("business_requirements", {})
        bae_coordination_plan = payload.get("bae_coordination_plan", [])

        # Step 1: Make technical architecture decisions
        arch_decisions = self._make_architecture_decisions(entity, business_requirements)

        # Step 2: Create detailed SWEA coordination plan
        enhanced_plan = self._create_enhanced_coordination_plan(
            bae_coordination_plan, arch_decisions
        )

        # Step 3: Set quality gates and success criteria
        quality_gates = self._define_quality_gates(entity, business_requirements)

        # Step 4: Establish performance and security requirements
        tech_requirements = self._establish_technical_requirements(entity, business_requirements)

        coordination_result = {
            "entity": entity,
            "technical_leader": "TechLeadSWEA",
            "architecture_decisions": arch_decisions,
            "enhanced_coordination_plan": enhanced_plan,
            "quality_gates": quality_gates,
            "technical_requirements": tech_requirements,
            "coordination_id": f"coord_{entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }

        # Store coordination plan for tracking
        self.active_coordination_plans[coordination_result["coordination_id"]] = coordination_result

        return self.create_success_response("coordinate_system_generation", coordination_result)

    def _coordinate_test_fixes(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate test failure fixes between TestSWEA and other SWEAs."""
        test_failures = payload.get("test_failures", [])
        entity = payload.get("entity", "Unknown")
        coordination_id = payload.get("coordination_id", None)

        fix_coordination_log = []
        fix_decisions = []

        for failure in test_failures:
            # Analyze the failure and make technical decision
            fix_decision = self._analyze_test_failure_and_decide(failure, entity)
            fix_decisions.append(fix_decision)

            fix_coordination_log.append(
                f"🔧 TechLead Decision: {fix_decision['issue_type']} → "
                f"{fix_decision['responsible_swea']} should {fix_decision['recommended_action']}"
            )

            # Create specific task for the responsible SWEA
            swea_task = self._create_swea_fix_task(fix_decision, failure)
            fix_coordination_log.append(
                f"📋 Task assigned to {fix_decision['responsible_swea']}: {swea_task['task_description']}"
            )

        coordination_result = {
            "entity": entity,
            "coordination_id": coordination_id,
            "fix_decisions": fix_decisions,
            "coordination_log": fix_coordination_log,
            "total_issues": len(test_failures),
            "technical_leader_involved": True,
            "next_steps": self._define_next_steps(fix_decisions),
        }

        return self.create_success_response("coordinate_test_fixes", coordination_result)

    def _review_and_approve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Review generated artifacts and approve/reject with technical feedback."""
        artifacts = payload.get("artifacts", [])
        entity = payload.get("entity", "Unknown")
        coordination_id = payload.get("coordination_id", None)

        review_results = []
        overall_approval = True
        technical_feedback = []

        for artifact in artifacts:
            artifact_review = self._review_artifact(artifact, entity)
            review_results.append(artifact_review)

            if not artifact_review["approved"]:
                overall_approval = False
                technical_feedback.extend(artifact_review["feedback"])

        # Generate technical recommendations
        tech_recommendations = self._generate_technical_recommendations(review_results, entity)

        approval_result = {
            "entity": entity,
            "coordination_id": coordination_id,
            "overall_approval": overall_approval,
            "artifact_reviews": review_results,
            "technical_feedback": technical_feedback,
            "technical_recommendations": tech_recommendations,
            "quality_score": self._calculate_quality_score(review_results),
            "next_actions": self._determine_next_actions(overall_approval, technical_feedback),
        }

        return self.create_success_response("review_and_approve", approval_result)

    def _generate_technical_recommendations(
        self, review_results: List[Dict[str, Any]], entity: str
    ) -> List[str]:
        """Generate technical recommendations based on artifact reviews."""
        recommendations = []

        # Analyze review results for patterns
        failed_reviews = [r for r in review_results if not r.get("approved", True)]

        if failed_reviews:
            recommendations.append("Address quality issues before deployment")

            # Group issues by type
            issue_types = {}
            for review in failed_reviews:
                for issue in review.get("feedback", []):
                    issue_type = self._categorize_issue(issue)
                    if issue_type not in issue_types:
                        issue_types[issue_type] = []
                    issue_types[issue_type].append(issue)

            # Generate specific recommendations
            for issue_type, issues in issue_types.items():
                if issue_type == "code_quality":
                    recommendations.append(
                        "Improve code quality: refactor complex methods, add documentation"
                    )
                elif issue_type == "security":
                    recommendations.append(
                        "Address security concerns: validate inputs, sanitize outputs"
                    )
                elif issue_type == "performance":
                    recommendations.append(
                        "Optimize performance: add indexes, cache frequently accessed data"
                    )
                elif issue_type == "testing":
                    recommendations.append(
                        "Enhance test coverage: add edge cases, improve assertions"
                    )
        else:
            recommendations.append("All artifacts meet quality standards")
            recommendations.append("System ready for deployment")
            recommendations.append("Consider performance monitoring in production")

        return recommendations

    def _categorize_issue(self, issue: str) -> str:
        """Categorize a technical issue for recommendation generation."""
        issue_lower = issue.lower()

        if any(
            keyword in issue_lower for keyword in ["security", "validation", "sanitize", "auth"]
        ):
            return "security"
        elif any(
            keyword in issue_lower for keyword in ["performance", "slow", "optimize", "cache"]
        ):
            return "performance"
        elif any(keyword in issue_lower for keyword in ["test", "coverage", "assertion", "mock"]):
            return "testing"
        else:
            return "code_quality"

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
        self, base_plan: List[Dict[str, Any]], arch_decisions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance the BAE coordination plan with technical requirements."""

        enhanced_plan = []

        for task in base_plan:
            enhanced_task = {
                **task,  # Keep original BAE task
                "technical_requirements": self._get_tech_requirements_for_task(
                    task, arch_decisions
                ),
                "quality_criteria": self._get_quality_criteria_for_task(task, arch_decisions),
                "dependencies": self._identify_task_dependencies(task, base_plan),
                "estimated_complexity": self._estimate_task_complexity(task),
            }
            enhanced_plan.append(enhanced_task)

        # Add TechLead review task
        enhanced_plan.append(
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "review_and_approve",
                "description": "Technical review and approval of all generated artifacts",
                "dependencies": [task["swea_agent"] for task in base_plan],
                "quality_criteria": [
                    "architecture_compliance",
                    "performance_standards",
                    "security_requirements",
                ],
            }
        )

        return enhanced_plan

    def _define_quality_gates(
        self, entity: str, business_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define quality gates that all artifacts must pass."""

        return {
            "code_quality": {
                "syntax_validation": True,
                "naming_conventions": True,
                "documentation_coverage": "> 80%",
                "complexity_limits": {"cyclomatic": "< 10", "nesting": "< 4"},
            },
            "functionality": {
                "unit_test_coverage": "> 90%",
                "integration_test_coverage": "> 80%",
                "all_crud_operations": True,
                "error_handling": True,
            },
            "performance": {
                "api_response_time": "< 200ms",
                "ui_load_time": "< 2s",
                "database_query_optimization": True,
            },
            "security": {
                "input_validation": True,
                "sql_injection_prevention": True,
                "xss_prevention": True,
                "data_sanitization": True,
            },
            "business_alignment": {
                "domain_vocabulary_preserved": True,
                "business_rules_enforced": True,
                "semantic_coherence": True,
            },
        }

    def _establish_technical_requirements(
        self, entity: str, business_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Establish technical requirements for the system."""
        return {
            "scalability": "handle 1000+ concurrent users",
            "availability": "99.9% uptime",
            "maintainability": "modular, well-documented code",
            "testability": "comprehensive test coverage",
            "security": "secure by design principles",
        }

    def _get_tech_requirements_for_task(
        self, task: Dict[str, Any], arch_decisions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get specific technical requirements for a task."""
        swea_agent = task.get("swea_agent", "")

        if "Database" in swea_agent:
            return {
                "schema_normalization": arch_decisions.get("database_strategy", "normalized"),
                "indexing_required": True,
                "foreign_key_constraints": True,
            }
        elif "Backend" in swea_agent:
            return {
                "api_pattern": arch_decisions.get("api_pattern", "restful"),
                "validation_level": "strict",
                "error_handling": "comprehensive",
            }
        elif "Frontend" in swea_agent:
            return {
                "ui_pattern": arch_decisions.get("ui_pattern", "component_based"),
                "responsiveness": "required",
                "accessibility": "wcag_aa",
            }
        elif "Test" in swea_agent:
            return {
                "testing_strategy": arch_decisions.get("testing_strategy", "pyramid"),
                "coverage_target": "90%",
                "test_types": ["unit", "integration", "e2e"],
            }

        return {}

    def _get_quality_criteria_for_task(
        self, task: Dict[str, Any], arch_decisions: Dict[str, Any]
    ) -> List[str]:
        """Get quality criteria that the task output must meet."""
        swea_agent = task.get("swea_agent", "")

        base_criteria = ["syntax_valid", "follows_naming_conventions", "documented"]

        if "Database" in swea_agent:
            return base_criteria + ["schema_normalized", "indexes_optimized", "constraints_defined"]
        elif "Backend" in swea_agent:
            return base_criteria + [
                "restful_design",
                "validation_implemented",
                "error_handling_complete",
            ]
        elif "Frontend" in swea_agent:
            return base_criteria + ["user_friendly", "responsive_design", "accessibility_compliant"]
        elif "Test" in swea_agent:
            return base_criteria + [
                "comprehensive_coverage",
                "reliable_execution",
                "clear_assertions",
            ]

        return base_criteria

    def _identify_task_dependencies(
        self, task: Dict[str, Any], all_tasks: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify dependencies for a task."""
        swea_agent = task.get("swea_agent", "")
        dependencies = []

        # Basic dependency rules
        if "Backend" in swea_agent:
            dependencies.append("DatabaseSWEA")
        elif "Frontend" in swea_agent:
            dependencies.extend(["DatabaseSWEA", "BackendSWEA"])
        elif "Test" in swea_agent:
            dependencies.extend(["DatabaseSWEA", "BackendSWEA", "FrontendSWEA"])

        return dependencies

    def _estimate_task_complexity(self, task: Dict[str, Any]) -> str:
        """Estimate the complexity of a task."""
        swea_agent = task.get("swea_agent", "")

        complexity_map = {
            "DatabaseSWEA": "medium",
            "BackendSWEA": "high",
            "FrontendSWEA": "high",
            "TestSWEA": "medium",
            "TechLeadSWEA": "low",  # Review tasks are typically lower complexity
        }

        return complexity_map.get(swea_agent, "medium")

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
        follows_naming = entity.lower() in artifact_content.lower()

        # Calculate approval score
        quality_checks = {
            "syntax_valid": syntax_valid,
            "has_documentation": has_documentation,
            "follows_naming_conventions": follows_naming,
            "content_length_adequate": len(artifact_content) > 100,
        }

        approval_score = sum(quality_checks.values()) / len(quality_checks)
        approved = approval_score >= 0.75  # 75% quality threshold

        feedback = []
        if not syntax_valid:
            feedback.append("Improve code syntax and structure")
        if not has_documentation:
            feedback.append("Add comprehensive documentation")
        if not follows_naming:
            feedback.append(f"Ensure naming conventions include {entity} entity reference")

        return {
            "artifact_type": artifact_type,
            "approved": approved,
            "quality_score": approval_score,
            "quality_checks": quality_checks,
            "feedback": feedback,
        }

    def _calculate_quality_score(self, review_results: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score from all artifact reviews."""
        if not review_results:
            return 0.0

        total_score = sum(result["quality_score"] for result in review_results)
        return total_score / len(review_results)

    def _determine_next_actions(
        self, overall_approval: bool, technical_feedback: List[str]
    ) -> List[str]:
        """Determine next actions based on review results."""
        if overall_approval:
            return ["proceed_to_deployment", "monitor_system_performance", "collect_usage_metrics"]
        else:
            return [
                "address_technical_feedback",
                "re_submit_for_review",
                "coordinate_swea_improvements",
            ] + [
                f"fix: {feedback}" for feedback in technical_feedback[:3]
            ]  # Top 3 issues
