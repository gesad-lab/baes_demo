import json
import logging
import os
import re
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


def is_debug_mode():
    """Check if debug mode is enabled"""
    return os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes")


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

    feedback_storage = {}  # Class-level storage for structured feedback

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
        "hybrid_coordination": "_hybrid_coordination",
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
        elif task == "hybrid_coordination":
            return self._hybrid_coordination(payload)
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
            if is_debug_mode():
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
            # Simple decision log
            self._log_decision(
                "coordination",
                entity,
                "APPROVED",
                f"{len(enhanced_plan)} SWEA tasks scheduled",
                type="evolution" if is_evolution else "creation",
                attributes=len(attributes),
                quality_gates=len(quality_gates),
            )
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
        """
        Coordinate test failure resolution across SWEA agents
        Enhanced with detailed failure analysis and specific fix routing
        """
        try:
            entity = payload.get("entity", "Unknown")
            test_failures = payload.get("test_failures", [])
            coordination_id = payload.get("coordination_id", f"test_fix_{entity}")
            # NEW: Extract detailed failure context from test execution
            failure_context = payload.get("failure_context", {})
            test_execution = failure_context.get("test_execution", {})
            stderr = test_execution.get("stderr", "")
            stdout = test_execution.get("stdout", "")
            exit_code = test_execution.get("exit_code", -1)
            logger.info("🧠 TechLeadSWEA: Coordinating test fixes for %s", entity)
            logger.info(
                "   📊 Test Context: %d failures, exit_code=%s", len(test_failures), exit_code
            )
            if stderr:
                logger.info("   📝 Key errors: %s", stderr[:200])  # First 200 chars
            coordination_log = []
            fix_decisions = []
            # ENHANCED: Analyze actual test execution output for specific issues
            specific_issues = self._analyze_detailed_test_failures(stderr, stdout, entity)
            coordination_log.append(
                f"🔍 Analyzed test output - found {len(specific_issues)} specific issues"
            )
            # Create targeted fix decisions based on specific issues
            for issue in specific_issues:
                fix_decision = {
                    "swea_agent": issue["responsible_swea"],
                    "responsible_swea": issue["responsible_swea"],
                    "fix_actions": issue["fix_actions"],
                    "priority": issue["priority"],
                    "reasoning": issue["description"],
                    "confidence": issue["confidence"],
                    "specific_issue": issue["issue_type"],
                    "detailed_context": issue.get("context", {}),
                    "recommended_action": (
                        issue["fix_actions"][0] if issue["fix_actions"] else "analyze_and_fix"
                    ),
                }
                fix_decisions.append(fix_decision)
                coordination_log.append(
                    f"📋 {issue['issue_type']} → {issue['responsible_swea']}: {issue['description']}"
                )
            # Fallback: If no specific issues found, analyze generic test failures
            if not fix_decisions and test_failures:
                coordination_log.append(
                    "🔄 No specific issues found, analyzing generic test failures"
                )
                for i, failure in enumerate(test_failures):
                    failure_category = failure.get("category", "unknown")
                    stderr_content = failure.get("stderr", "")
                    if (
                        "import" in failure_category.lower()
                        or "modulenotfounderror" in stderr_content.lower()
                    ):
                        fix_decision = {
                            "swea_agent": "BackendSWEA",
                            "responsible_swea": "BackendSWEA",
                            "fix_actions": [
                                "fix_import_dependencies",
                                "regenerate_model_with_imports",
                            ],
                            "priority": "high",
                            "reasoning": f"Import error in test failure {i+1}",
                            "confidence": 0.8,
                            "recommended_action": "fix_import_dependencies",
                        }
                    elif "api" in failure_category.lower() or "404" in stderr_content:
                        fix_decision = {
                            "swea_agent": "BackendSWEA",
                            "responsible_swea": "BackendSWEA",
                            "fix_actions": ["fix_api_routing", "regenerate_api_endpoints"],
                            "priority": "high",
                            "reasoning": f"API error in test failure {i+1}",
                            "confidence": 0.8,
                            "recommended_action": "fix_api_routing",
                        }
                    elif "assertion" in failure_category.lower():
                        fix_decision = {
                            "swea_agent": "TestSWEA",
                            "responsible_swea": "TestSWEA",
                            "fix_actions": ["review_test_assertions", "fix_test_expectations"],
                            "priority": "medium",
                            "reasoning": f"Test assertion error in failure {i+1}",
                            "confidence": 0.7,
                            "recommended_action": "review_test_assertions",
                        }
                    else:
                        fix_decision = {
                            "swea_agent": "TestSWEA",
                            "responsible_swea": "TestSWEA",
                            "fix_actions": ["analyze_test_failure", "fix_test_issues"],
                            "priority": "medium",
                            "reasoning": f"Unknown test failure {i+1}",
                            "confidence": 0.5,
                            "recommended_action": "analyze_test_failure",
                        }
                    fix_decisions.append(fix_decision)
                    coordination_log.append(
                        f"Analyzed failure {i+1}: {failure_category} → {fix_decision['swea_agent']}"
                    )
            # Create coordination result with enhanced information
            coordination_result = {
                "entity": entity,
                "coordination_id": coordination_id,
                "fix_decisions": fix_decisions,
                "coordination_log": coordination_log,
                "total_failures": len(test_failures),
                "fixes_planned": len(fix_decisions),
                "specific_issues_found": len(specific_issues),
                "failure_analysis": {
                    "stderr_summary": stderr[:500] if stderr else "",
                    "exit_code": exit_code,
                    "issues_detected": [issue["issue_type"] for issue in specific_issues],
                },
            }
            # Enhanced decision logging
            swea_distribution = {}
            for decision in fix_decisions:
                swea = decision["swea_agent"]
                swea_distribution[swea] = swea_distribution.get(swea, 0) + 1
            self._log_decision(
                "test_fix_coordination",
                entity,
                "COORDINATED",
                f"{len(fix_decisions)} specific fixes planned",
                failures_analyzed=len(test_failures),
                specific_issues=len(specific_issues),
                swea_assignments=", ".join(f"{s}:{c}" for s, c in swea_distribution.items()),
            )
            response = self.create_success_response("coordinate_test_fixes", coordination_result)
            response["technical_governance"] = True
            return response
        except Exception as e:
            logger.error(f"❌ TechLeadSWEA test fix coordination failed: {str(e)}")
            return self.create_error_response("coordinate_test_fixes", str(e), "coordination_error")

    def _analyze_detailed_test_failures(
        self, stderr: str, stdout: str, entity: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze detailed test execution output to identify specific issues and route fixes appropriately
        """
        issues = []
        combined_output = f"{stderr} {stdout}".lower()
        # 1. Mock object issues (common in generated tests)
        if "magicmock" in combined_output or "mock object" in combined_output:
            issues.append(
                {
                    "issue_type": "mock_configuration_error",
                    "responsible_swea": "TestSWEA",
                    "fix_actions": ["fix_test_mocking", "update_test_configuration"],
                    "priority": "high",
                    "confidence": 0.9,
                    "description": "Test mocking configuration issues - tests expecting real data but getting Mock objects",
                    "context": {"error_pattern": "mock_object_validation"},
                }
            )
        # 2. Missing function errors (UI tests)
        if "nameerror: name" in combined_output and (
            "display_" in combined_output
            or "create_" in combined_output
            or "edit_" in combined_output
        ):
            issues.append(
                {
                    "issue_type": "missing_ui_functions",
                    "responsible_swea": "FrontendSWEA",
                    "fix_actions": [
                        "regenerate_ui_with_functions",
                        "add_missing_streamlit_functions",
                    ],
                    "priority": "high",
                    "confidence": 0.9,
                    "description": "Missing UI functions in Streamlit application - tests reference functions that don't exist",
                    "context": {"error_pattern": "missing_functions"},
                }
            )
        # 3. API status code mismatches
        if "assert" in combined_output and (
            "200 == 422" in combined_output or "200 == 404" in combined_output
        ):
            issues.append(
                {
                    "issue_type": "api_validation_mismatch",
                    "responsible_swea": "BackendSWEA",
                    "fix_actions": ["fix_api_validation", "update_error_handling"],
                    "priority": "high",
                    "confidence": 0.8,
                    "description": "API validation errors - endpoints returning wrong status codes",
                    "context": {"error_pattern": "status_code_mismatch"},
                }
            )
        # 4. Pydantic validation errors
        if (
            "validationerror" in combined_output
            and "input should be a valid string" in combined_output
        ):
            issues.append(
                {
                    "issue_type": "pydantic_validation_error",
                    "responsible_swea": "BackendSWEA",
                    "fix_actions": ["fix_model_validation", "update_pydantic_models"],
                    "priority": "high",
                    "confidence": 0.8,
                    "description": "Pydantic model validation errors - incorrect data types or validation rules",
                    "context": {"error_pattern": "pydantic_validation"},
                }
            )
        # 5. Database connection/query issues
        if "sqlite" in combined_output and (
            "fetchone" in combined_output or "fetchall" in combined_output
        ):
            issues.append(
                {
                    "issue_type": "database_query_error",
                    "responsible_swea": "DatabaseSWEA",
                    "fix_actions": ["fix_database_queries", "update_schema"],
                    "priority": "medium",
                    "confidence": 0.7,
                    "description": "Database query issues - problems with SQL queries or database connection",
                    "context": {"error_pattern": "database_query"},
                }
            )
        # 6. Import/module errors
        if "modulenotfounderror" in combined_output or "importerror" in combined_output:
            issues.append(
                {
                    "issue_type": "import_dependency_error",
                    "responsible_swea": "BackendSWEA",
                    "fix_actions": ["fix_imports", "update_dependencies"],
                    "priority": "high",
                    "confidence": 0.9,
                    "description": "Import or module dependency errors - missing or incorrect imports",
                    "context": {"error_pattern": "import_error"},
                }
            )
        # 7. Syntax errors
        if "syntaxerror" in combined_output:
            issues.append(
                {
                    "issue_type": "syntax_error",
                    "responsible_swea": "BackendSWEA",
                    "fix_actions": ["fix_syntax_errors", "regenerate_code"],
                    "priority": "critical",
                    "confidence": 0.95,
                    "description": "Syntax errors in generated code - code compilation failures",
                    "context": {"error_pattern": "syntax_error"},
                }
            )
        return issues

    def _review_and_approve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced review and approval with comprehensive LLM-based validation.
        Now performs detailed artifact analysis to catch issues before approval.
        """
        entity = payload.get("entity", "Unknown")
        swea_agent = payload.get("swea_agent", "Unknown")
        task_type = payload.get("task_type", "Unknown")
        result = payload.get("result", {})
        final_review = payload.get("final_review", False)
        retry_count = payload.get("retry_count", 0)
        if swea_agent == "TechLeadSWEA" and task_type == "coordinate_system_generation":
            logger.info(
                f"🔍 TechLeadSWEA (as reviewer) is validating its own coordination plan (author: TechLeadSWEA) for entity '{entity}' (retry: {retry_count})"
            )
            # For coordination tasks, we validate the coordination plan structure instead of code
            validation_result = self._validate_coordination_plan(entity, result)
            if validation_result["is_valid"]:
                logger.info(
                    f"✅ TechLeadSWEA (as reviewer) APPROVED task '{task_type}' from {swea_agent} (author) for entity '{entity}'"
                )
                return {
                    "approved": True,
                    "success": True,
                    "data": {
                        "overall_approval": True,
                        "quality_score": validation_result["quality_score"],
                        "validation_details": validation_result["details"],
                        "feedback": validation_result["suggestions"],
                        "technical_feedback": validation_result["suggestions"],
                    },
                    "quality_score": validation_result["quality_score"],
                    "validation_details": validation_result["details"],
                    "feedback": validation_result["suggestions"],
                }
            else:
                # Get the primary reason for rejection (first issue)
                primary_reason = validation_result.get("issues", ["Quality standards not met"])[0]
                logger.warning(
                    f"❌ TechLeadSWEA (as reviewer) REJECTED task '{task_type}' from {swea_agent} (author) for entity '{entity}' - Reason: {primary_reason}"
                )
                return {
                    "approved": False,
                    "success": False,
                    "data": {
                        "overall_approval": False,
                        "quality_score": validation_result["quality_score"],
                        "validation_details": validation_result["details"],
                        "feedback": validation_result["issues"],
                        "technical_feedback": validation_result["issues"],
                        "retry_required": True,
                        "rejection_reason": primary_reason,
                    },
                    "quality_score": validation_result["quality_score"],
                    "validation_details": validation_result["details"],
                    "feedback": validation_result["issues"],
                    "retry_required": True,
                }
        else:
            logger.info(
                f"🔍 TechLeadSWEA (as reviewer) is reviewing output from {swea_agent} (author) for task '{task_type}' on entity '{entity}' (retry: {retry_count})"
            )
        if final_review:
            return self._conduct_final_system_review(payload)
        # Special case: TechLeadSWEA coordination tasks don't produce code artifacts
        if swea_agent == "TechLeadSWEA" and task_type == "coordinate_system_generation":
            # For coordination tasks, we validate the coordination plan structure instead of code
            validation_result = self._validate_coordination_plan(entity, result)
        else:
            # Perform comprehensive LLM-based validation for code-producing tasks
            validation_result = self._validate_generated_artifact(
                entity, swea_agent, task_type, result
            )
        if validation_result["is_valid"]:
            logger.info(
                f"✅ TechLeadSWEA (as reviewer) APPROVED task '{task_type}' from {swea_agent} (author) for entity '{entity}'"
            )
            # Stage 4 Improvement #1: Clear stored feedback on successful approval
            self._clear_feedback_storage(entity, swea_agent, task_type)
            return {
                "approved": True,
                "success": True,
                "data": {
                    "overall_approval": True,
                    "quality_score": validation_result["quality_score"],
                    "validation_details": validation_result["details"],
                    "feedback": validation_result["suggestions"],
                    "technical_feedback": validation_result["suggestions"],
                },
                "quality_score": validation_result["quality_score"],
                "validation_details": validation_result["details"],
                "feedback": validation_result["suggestions"],
            }
        else:
            # Stage 4 Improvement #1: Extract and store structured feedback for reuse
            extracted_feedback = self._extract_structured_feedback(
                validation_result, entity, swea_agent, task_type
            )
            self._store_feedback_for_reuse(extracted_feedback)
            # Stage 3 Improvement #4: Check for escalation needed for CRITICAL issues
            feedback_summary = validation_result.get("feedback_summary", {})
            escalation_needed = feedback_summary.get("escalation_needed", False)
            critical_feedback = validation_result.get("critical_feedback", [])
            # Check if we've reached max retries with CRITICAL issues
            max_retries = int(os.getenv("BAE_MAX_RETRIES", "3"))
            if retry_count >= max_retries and critical_feedback and escalation_needed:
                logger.error(
                    "🚨 Max retries reached with CRITICAL issues - escalating to Human Expert"
                )
                escalation_report = self._escalate_to_human_expert(
                    entity, critical_feedback, retry_count
                )
                return {
                    "approved": False,
                    "success": False,
                    "escalation_required": True,
                    "escalation_report": escalation_report,
                    "data": {
                        "overall_approval": False,
                        "quality_score": validation_result["quality_score"],
                        "validation_details": validation_result["details"],
                        "feedback": validation_result.get(
                            "actionable_feedback", validation_result["suggestions"]
                        ),
                        "technical_feedback": validation_result.get(
                            "actionable_feedback", validation_result["suggestions"]
                        ),
                        "retry_required": False,  # No more retries, escalation needed
                        "escalation_reason": f"CRITICAL issues unresolved after {retry_count} attempts",
                        "human_expert_required": True,
                    },
                    "quality_score": validation_result["quality_score"],
                    "validation_details": validation_result["details"],
                    "feedback": validation_result.get(
                        "actionable_feedback", validation_result["suggestions"]
                    ),
                }
            # Normal rejection with categorized feedback
            actionable_feedback = validation_result.get(
                "actionable_feedback", validation_result.get("suggestions", [])
            )
            primary_reason = validation_result.get("issues", ["Quality standards not met"])[0]
            # Create rejection message with prioritized feedback
            if actionable_feedback:
                # Fix: Handle both string and dictionary formats in actionable_feedback
                priority_fixes = []
                for f in actionable_feedback:
                    if isinstance(f, str) and f.startswith("[CRITICAL]"):
                        priority_fixes.append(f)
                    elif isinstance(f, dict):
                        # Extract the relevant string from dictionary
                        feedback_text = f.get("fix", f.get("issue", f.get("description", str(f))))
                        if isinstance(feedback_text, str) and feedback_text.startswith(
                            "[CRITICAL]"
                        ):
                            priority_fixes.append(feedback_text)
                    if len(priority_fixes) >= 2:
                        break

                if not priority_fixes:
                    # Fallback to first 3 actionable items
                    priority_fixes = actionable_feedback[:3]
                    # Convert dict items to strings if needed
                    priority_fixes = [
                        (
                            f
                            if isinstance(f, str)
                            else str(f.get("fix", f.get("issue", f.get("description", f))))
                        )
                        for f in priority_fixes
                    ]

                rejection_message = (
                    f"{primary_reason}. Priority fixes needed: {'; '.join(priority_fixes)}"
                )
            else:
                rejection_message = primary_reason
            logger.warning(
                f"❌ TechLeadSWEA (as reviewer) REJECTED task '{task_type}' from {swea_agent} (author) for entity '{entity}' - Reason: {rejection_message}"
            )
            # Log feedback categorization if available
            if feedback_summary:
                logger.info(
                    f"📊 Feedback Summary: {feedback_summary.get('critical_count', 0)} CRITICAL, {feedback_summary.get('required_count', 0)} REQUIRED, {feedback_summary.get('optional_count', 0)} OPTIONAL"
                )
            return {
                "approved": False,
                "success": False,
                "data": {
                    "overall_approval": False,
                    "quality_score": validation_result["quality_score"],
                    "validation_details": validation_result["details"],
                    "feedback": actionable_feedback,  # Use actionable feedback (CRITICAL + REQUIRED)
                    "technical_feedback": actionable_feedback,
                    "retry_required": True,
                    "rejection_reason": rejection_message,
                    "feedback_summary": feedback_summary,
                },
                "quality_score": validation_result["quality_score"],
                "validation_details": validation_result["details"],
                "feedback": actionable_feedback,
                "retry_required": True,
            }

    def _validate_coordination_plan(self, entity: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate coordination plan structure and completeness.
        This is used for TechLeadSWEA coordination tasks that don't produce code artifacts.
        """
        try:
            logger.info(
                "🔍 TechLeadSWEA: Validating coordination plan for entity '{}'".format(entity)
            )
            # Check if the result has the expected structure for coordination tasks
            if not result.get("success", False):
                logger.warning("❌ TechLeadSWEA: Coordination task failed - success=False")
                return {
                    "is_valid": False,
                    "quality_score": 0.0,
                    "details": "Coordination task failed",
                    "issues": ["Coordination task returned success=False"],
                    "suggestions": ["Check coordination task implementation"],
                }
            data = result.get("data", {})
            enhanced_plan = data.get("enhanced_coordination_plan", [])
            # Validate that we have a coordination plan
            if not enhanced_plan:
                logger.warning("❌ TechLeadSWEA: Coordination plan is empty")
                return {
                    "is_valid": False,
                    "quality_score": 0.0,
                    "details": "No coordination plan generated",
                    "issues": ["Empty coordination plan"],
                    "suggestions": ["Ensure coordination plan contains SWEA tasks"],
                }
            # Check for required SWEA tasks in the plan
            required_sweas = ["DatabaseSWEA", "BackendSWEA", "FrontendSWEA"]
            found_sweas = set()
            for task in enhanced_plan:
                swea_agent = task.get("swea_agent", "")
                if swea_agent in required_sweas:
                    found_sweas.add(swea_agent)
            # Validate that all required SWEAs are included
            if len(found_sweas) != len(required_sweas):
                missing_sweas = set(required_sweas) - found_sweas
                logger.warning(
                    f"❌ TechLeadSWEA: Coordination plan missing required SWEAs: {missing_sweas}"
                )
                return {
                    "is_valid": False,
                    "quality_score": 0.3,
                    "details": f"Missing required SWEAs: {missing_sweas}",
                    "issues": [f"Coordination plan missing: {', '.join(missing_sweas)}"],
                    "suggestions": ["Include all required SWEAs in coordination plan"],
                }
            # Check for proper task structure
            valid_tasks = 0
            total_tasks = len(enhanced_plan)
            for task in enhanced_plan:
                if all(key in task for key in ["swea_agent", "task_type", "payload"]):
                    valid_tasks += 1
            quality_score = valid_tasks / total_tasks if total_tasks > 0 else 0.0
            if quality_score >= 0.8:
                logger.info("✅ TechLeadSWEA: Coordination plan validated successfully")
                return {
                    "is_valid": True,
                    "quality_score": quality_score,
                    "details": f"Coordination plan validated: {valid_tasks}/{total_tasks} tasks properly structured",
                    "issues": [],
                    "suggestions": ["Coordination plan ready for execution"],
                }
            else:
                logger.warning("❌ TechLeadSWEA: Structural issues in coordination plan")
                return {
                    "is_valid": False,
                    "quality_score": quality_score,
                    "details": f"Coordination plan has structural issues: {valid_tasks}/{total_tasks} tasks properly structured",
                    "issues": ["Some tasks missing required fields"],
                    "suggestions": [
                        "Ensure all tasks have swea_agent, task_type, and payload fields"
                    ],
                }
        except Exception as e:
            logger.error(f"❌ TechLeadSWEA: Error validating coordination plan: {str(e)}")
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "details": f"Validation error: {str(e)}",
                "issues": [f"Validation process failed: {str(e)}"],
                "suggestions": ["Retry the validation process"],
            }

    def _validate_generated_artifact(
        self, entity: str, swea_agent: str, task_type: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of generated artifacts.
        Handles both code artifacts and database artifacts appropriately.
        """
        try:
            # Special handling for DatabaseSWEA - it returns database metadata, not code
            if swea_agent == "DatabaseSWEA" and task_type == "setup_database":
                return self._validate_database_artifact(entity, result)
            # For code-producing SWEAs, use LLM-based validation
            return self._validate_code_artifact(entity, swea_agent, task_type, result)
        except Exception as e:
            logger.error(
                f"❌ TechLeadSWEA: Validation failed for {swea_agent}.{task_type}: {str(e)}"
            )
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "details": f"Validation error: {str(e)}",
                "issues": [f"Validation process failed: {str(e)}"],
                "suggestions": ["Retry the validation process"],
            }

    def _validate_database_artifact(self, entity: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate DatabaseSWEA artifacts by checking database-specific fields.
        This is more reliable than LLM-based validation for database metadata.
        """
        try:
            # Check basic result structure
            if not result.get("success", False):
                return {
                    "is_valid": False,
                    "quality_score": 0.0,
                    "details": "Database setup failed",
                    "issues": ["Database setup returned success=False"],
                    "suggestions": ["Check database setup implementation"],
                }
            data = result.get("data", {})
            if not data:
                return {
                    "is_valid": False,
                    "quality_score": 0.0,
                    "details": "No database data provided",
                    "issues": ["Missing database setup data"],
                    "suggestions": ["Ensure database setup returns proper data"],
                }
            # Check for required database fields
            required_fields = ["database_path", "tables_created"]
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return {
                    "is_valid": False,
                    "quality_score": 0.2,
                    "details": f"Missing database fields: {missing_fields}",
                    "issues": [f"Database setup missing: {', '.join(missing_fields)}"],
                    "suggestions": ["Ensure database setup returns all required fields"],
                }
            # Check if tables were actually created
            tables_created = data.get("tables_created", [])
            if not tables_created or len(tables_created) == 0:
                return {
                    "is_valid": False,
                    "quality_score": 0.0,
                    "details": "No database tables were created",
                    "issues": ["No database tables were created"],
                    "suggestions": ["Check database table creation logic"],
                }
            # Validate database path format
            database_path = data.get("database_path", "")
            if not database_path:
                return {
                    "is_valid": False,
                    "quality_score": 0.2,
                    "details": "Database path not provided",
                    "issues": ["Missing database path"],
                    "suggestions": ["Ensure database path is specified"],
                }
            # Validate table names match entity
            entity_table = f"{entity.lower()}s"
            if entity_table not in tables_created:
                # Check for alternative naming patterns
                alternative_names = [entity.lower(), f"{entity.lower()}_table"]
                if not any(alt in tables_created for alt in alternative_names):
                    return {
                        "is_valid": False,
                        "quality_score": 0.6,
                        "details": f"Expected table '{entity_table}' not found in: {tables_created}",
                        "issues": [f"Entity table '{entity_table}' not created"],
                        "suggestions": [f"Ensure table for entity '{entity}' is created"],
                    }
            return {
                "is_valid": True,
                "quality_score": 1.0,
                "details": f"Database setup validated: {len(tables_created)} tables created at {database_path}",
                "issues": [],
                "suggestions": ["Database setup completed successfully"],
            }
        except Exception as e:
            logger.error(f"❌ Database artifact validation failed: {str(e)}")
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "details": f"Database validation error: {str(e)}",
                "issues": [f"Database validation failed: {str(e)}"],
                "suggestions": ["Retry database validation"],
            }

    def _validate_code_artifact(
        self, entity: str, swea_agent: str, task_type: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LLM-based validation for code artifacts (BackendSWEA, FrontendSWEA, etc.).
        """
        try:
            # Extract artifact information - handle nested data structure from SWEAs
            data = result.get("data", {})
            code = data.get("code", "") if data else result.get("code", "")
            file_path = data.get("file_path", "") if data else result.get("file_path", "")
            # Log what we found for debugging
            logger.info(f"🔍 TechLeadSWEA: Extracted code length: {len(code)} characters")
            logger.info(f"🔍 TechLeadSWEA: File path: {file_path}")
            # Determine validation type based on SWEA and task
            validation_type = self._determine_validation_type(swea_agent, task_type)
            # Perform LLM-based validation
            validation_prompt = self._build_validation_prompt(
                entity, swea_agent, task_type, validation_type, code, file_path
            )
            validation_response = self.llm_client.generate_response(
                validation_prompt,
                system_prompt="You are a TechLeadSWEA performing code quality validation. Be thorough and critical.",
            )
            # Parse validation response
            validation_result = self._parse_validation_response(validation_response)
            # Add context-specific checks
            validation_result.update(
                self._perform_context_checks(entity, swea_agent, task_type, code, file_path)
            )
            return validation_result
        except Exception as e:
            logger.error(
                f"❌ TechLeadSWEA: Code validation failed for {swea_agent}.{task_type}: {str(e)}"
            )
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "details": f"Code validation error: {str(e)}",
                "issues": [f"Code validation process failed: {str(e)}"],
                "suggestions": ["Retry the code validation process"],
            }

    def _determine_validation_type(self, swea_agent: str, task_type: str) -> str:
        """Determine the type of validation needed based on SWEA and task."""
        if "backend" in swea_agent.lower() or "programmer" in swea_agent.lower():
            if "model" in task_type.lower():
                return "pydantic_model"
            elif "api" in task_type.lower():
                return "fastapi_routes"
            else:
                return "python_code"
        elif "frontend" in swea_agent.lower():
            return "streamlit_ui"
        elif "database" in swea_agent.lower():
            return "database_schema"
        elif "test" in swea_agent.lower():
            return "test_code"
        else:
            return "general_code"

    def _build_validation_prompt(
        self,
        entity: str,
        swea_agent: str,
        task_type: str,
        validation_type: str,
        code: str,
        file_path: str,
    ) -> str:
        """Build comprehensive validation prompt for LLM analysis with detailed, actionable feedback."""
        validation_requirements = {
            "pydantic_model": """
            CRITICAL CHECKS:
            1. All classes have complete field definitions (no empty classes)
            2. Proper type hints and validation for all fields
            3. No placeholder comments or TODO items
            4. Proper inheritance structure (Base → Create → Response)
            5. All required fields are properly defined
            SPECIFIC FIX SUGGESTIONS:
            - If empty classes found: "Add field definitions with proper types (e.g., name: str, age: int)"
            - If missing validation: "Add Pydantic validators (e.g., @validator('email') def validate_email)"
            - If wrong inheritance: "Fix inheritance: BaseModel → Base, Base → Create/Response"
            """,
            "fastapi_routes": """
            CRITICAL CHECKS:
            1. Complete CRUD endpoints (POST, GET, PUT, DELETE)
            2. Proper HTTP status codes (201, 200, 404, 500)
            3. Error handling with HTTPException
            4. Database integration with proper dependencies
            5. Pydantic models embedded in the same file
            6. No empty function bodies or placeholder comments
            7. Proper router configuration with prefix
            SPECIFIC FIX SUGGESTIONS:
            - If missing endpoints: "Add missing CRUD endpoints: POST /, GET /, GET /{id}, PUT /{id}, DELETE /{id}"
            - If wrong status codes: "Use correct status codes: 201 for POST, 200 for GET/PUT, 404 for not found"
            - If database issues: "Use context manager pattern: @contextmanager def get_db_connection(): try: yield conn; finally: conn.close()"
            - If missing error handling: "Add try/except blocks with HTTPException for all database operations"
            - If empty functions: "Implement function bodies with actual database operations and error handling"
            """,
            "streamlit_ui": """
            CRITICAL CHECKS:
            1. Complete main() function with all UI components
            2. Proper form handling and data validation
            3. CRUD operations integration with API
            4. Error handling and user feedback
            5. No placeholder comments or TODO items
            6. Proper Streamlit component usage
            SPECIFIC FIX SUGGESTIONS:
            - If missing main(): "Add def main(): function with st.title() and all UI components"
            - If empty forms: "Implement form handling with st.form(), st.text_input(), st.button()"
            - If missing API calls: "Add requests.get/post/put/delete() calls to interact with FastAPI endpoints"
            - If no error handling: "Add try/except blocks with st.error() for user feedback"
            """,
            "database_schema": """
            CRITICAL CHECKS:
            1. Complete table creation with all fields
            2. Proper data types and constraints
            3. Primary key and foreign key definitions
            4. No placeholder SQL or TODO items
            5. Proper database initialization
            SPECIFIC FIX SUGGESTIONS:
            - If missing fields: "Add all required fields with proper SQLite types (TEXT, INTEGER, REAL, BLOB)"
            - If missing constraints: "Add PRIMARY KEY, NOT NULL, UNIQUE constraints where appropriate"
            - If wrong types: "Use correct SQLite types: TEXT for strings, INTEGER for numbers, REAL for floats"
            - If empty schema: "Create complete CREATE TABLE statement with all entity fields"
            """,
            "test_code": """
            CRITICAL CHECKS:
            1. Complete test functions with assertions
            2. Proper test data and setup
            3. API endpoint testing with correct URLs
            4. Error case testing
            5. No placeholder tests or TODO items
            6. Proper import statements
            SPECIFIC FIX SUGGESTIONS:
            - If missing tests: "Add test functions for each CRUD operation: test_create, test_read, test_update, test_delete"
            - If no assertions: "Add assert statements to verify response status codes and data"
            - If wrong URLs: "Use correct API endpoints: POST /api/students/, GET /api/students/, etc."
            - If missing error tests: "Add tests for error cases: 404 for not found, 400 for bad request"
            """,
            "general_code": """
            CRITICAL CHECKS:
            1. Complete implementation (no empty functions)
            2. Proper error handling
            3. No placeholder comments or TODO items
            4. Proper imports and dependencies
            5. Type hints where applicable
            SPECIFIC FIX SUGGESTIONS:
            - If empty functions: "Implement function bodies with actual logic and return statements"
            - If missing error handling: "Add try/except blocks with proper exception handling"
            - If placeholder comments: "Replace TODO comments with actual implementation"
            - If missing imports: "Add required import statements at the top of the file"
            """,
        }
        return f"""
        You are a TechLeadSWEA performing comprehensive code quality validation with detailed, actionable feedback.
        TASK: Validate generated artifact for quality, completeness, and adherence to requirements. Provide specific, actionable feedback that tells the SWEA exactly what to fix and how.
        CONTEXT:
        - Entity: {entity}
        - SWEA Agent: {swea_agent}
        - Task Type: {task_type}
        - Validation Type: {validation_type}
        - File Path: {file_path}
        {validation_requirements.get(validation_type, validation_requirements["general_code"])}
        CODE TO VALIDATE:
        ```python
        {code}
        ```
        VALIDATION REQUIREMENTS:
        1. Check for completeness (no empty classes, functions, or placeholder comments)
        2. Verify proper implementation (working code, not just structure)
        3. Validate adherence to requirements (CRUD operations, error handling, etc.)
        4. Check for consistency (proper naming, imports, structure)
        5. Identify any critical issues that would prevent the code from working
        RESPONSE FORMAT:
        ```json
        {{
            "is_valid": true/false,
            "quality_score": 0.0-1.0,
            "details": "Detailed analysis of the code with specific issues identified",
            "issues": [
                "Specific issue 1 with exact location and problem description",
                "Specific issue 2 with exact location and problem description"
            ],
            "suggestions": [
                "Specific fix suggestion 1 with exact code pattern to implement",
                "Specific fix suggestion 2 with exact code pattern to implement"
            ],
            "fix_instructions": [
                "Step-by-step instruction 1 for the SWEA to follow",
                "Step-by-step instruction 2 for the SWEA to follow"
            ],
            "categorized_feedback": [
                {{
                    "priority": "CRITICAL",
                    "issue": "Specific critical issue that prevents system from working",
                    "fix": "Exact fix instruction with code pattern"
                }},
                {{
                    "priority": "REQUIRED",
                    "issue": "Important issue that affects functionality",
                    "fix": "Exact fix instruction with code pattern"
                }},
                {{
                    "priority": "OPTIONAL",
                    "issue": "Nice-to-have improvement",
                    "fix": "Suggested enhancement"
                }}
            ]
        }}
        ```
        CRITICAL: Be specific and actionable. Instead of saying "database connection not properly managed", say:
        - "Use context manager pattern: @contextmanager def get_db_connection(): try: yield conn; finally: conn.close()"
        - "Add try/except/finally blocks around all database operations"
        - "Ensure connections are closed in finally block even when exceptions occur"
        Instead of saying "missing error handling", say:
        - "Add try/except blocks with HTTPException(status_code=500, detail='error message')"
        - "Add db.rollback() in except blocks for database operations"
        Instead of saying "incomplete implementation", say:
        - "Add actual database operations: cursor.execute('SELECT * FROM table')"
        - "Add proper return statements with response models"
        PRIORITY CATEGORIZATION GUIDELINES:
        **CRITICAL** - Issues that prevent the system from working at all:
        - Empty classes, functions, or missing core implementation
        - Syntax errors, import errors, or runtime failures
        - Security vulnerabilities or data corruption risks
        - Database connection leaks or transaction failures
        **REQUIRED** - Issues that affect functionality but don't prevent basic operation:
        - Missing error handling or incomplete CRUD operations
        - Incorrect HTTP status codes or response formats
        - Missing validation or improper data handling
        - Performance issues or resource management problems
        **OPTIONAL** - Improvements that enhance quality but aren't essential:
        - Code style improvements or better naming conventions
        - Additional logging or documentation
        - Performance optimizations or UX enhancements
        - Non-essential features or convenience methods
        STAGE 3 IMPROVEMENT #4: You MUST categorize ALL feedback with explicit priority levels.
        SWEAs will handle CRITICAL and REQUIRED issues together, ignoring OPTIONAL ones.
        Be thorough and critical. If the code has empty classes, placeholder comments, or incomplete implementations, mark it as invalid and provide specific fix instructions.
        """

    def _parse_validation_response(self, validation_response: str) -> Dict[str, Any]:
        """Parse LLM validation response into structured format with categorized feedback."""
        try:
            # Try to extract JSON from the response
            import re

            json_match = re.search(r"```json\s*(\{.*?\})\s*```", validation_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_response = json.loads(json_str)
                # Stage 3 Improvement #4: Process categorized feedback
                if "categorized_feedback" in parsed_response:
                    parsed_response = self._process_categorized_feedback(parsed_response)
                return parsed_response
            # Fallback: try to find JSON without markdown
            json_match = re.search(r"\{.*\}", validation_response, re.DOTALL)
            if json_match:
                parsed_response = json.loads(json_match.group(0))
                # Stage 3 Improvement #4: Process categorized feedback
                if "categorized_feedback" in parsed_response:
                    parsed_response = self._process_categorized_feedback(parsed_response)
                return parsed_response
            # If no JSON found, parse manually
            return self._parse_manual_validation_response(validation_response)
        except Exception as e:
            logger.warning(f"Failed to parse validation response as JSON: {str(e)}")
            return self._parse_manual_validation_response(validation_response)

    def _process_categorized_feedback(self, validation_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 3 Improvement #4: Process categorized feedback with priority routing.
        Handle CRITICAL and REQUIRED together, ignore OPTIONAL.
        Escalate unresolvable CRITICAL issues to Human Expert.
        """
        try:
            categorized_feedback = validation_response.get("categorized_feedback", [])
            # Separate feedback by priority
            critical_feedback = []
            required_feedback = []
            optional_feedback = []
            for feedback_item in categorized_feedback:
                priority = feedback_item.get("priority", "REQUIRED").upper()
                if priority == "CRITICAL":
                    critical_feedback.append(feedback_item)
                elif priority == "REQUIRED":
                    required_feedback.append(feedback_item)
                elif priority == "OPTIONAL":
                    optional_feedback.append(feedback_item)
            # Stage 3 Improvement #4: Handle CRITICAL + REQUIRED together, ignore OPTIONAL
            actionable_feedback = critical_feedback + required_feedback
            # Log feedback categorization for analytics
            logger.info("📊 TechLeadSWEA Feedback Categorization:")
            logger.info(f"   🚨 CRITICAL: {len(critical_feedback)} issues")
            logger.info(f"   ⚠️  REQUIRED: {len(required_feedback)} issues")
            logger.info(f"   💡 OPTIONAL: {len(optional_feedback)} issues (ignored)")
            logger.info(f"   🎯 ACTIONABLE: {len(actionable_feedback)} issues to address")
            # Update validation response with processed feedback
            validation_response.update(
                {
                    "critical_feedback": critical_feedback,
                    "required_feedback": required_feedback,
                    "optional_feedback": optional_feedback,
                    "actionable_feedback": actionable_feedback,
                    "feedback_summary": {
                        "critical_count": len(critical_feedback),
                        "required_count": len(required_feedback),
                        "optional_count": len(optional_feedback),
                        "actionable_count": len(actionable_feedback),
                        "escalation_needed": self._check_escalation_needed(critical_feedback),
                        "routing_strategy": "handle_critical_and_required",
                    },
                }
            )
            # Create consolidated fix instructions from actionable feedback
            consolidated_fix_instructions = []
            for feedback_item in actionable_feedback:
                fix_instruction = f"[{feedback_item.get('priority', 'REQUIRED')}] {feedback_item.get('fix', feedback_item.get('issue', 'Unknown issue'))}"
                consolidated_fix_instructions.append(fix_instruction)
            # Update fix_instructions with prioritized feedback
            if consolidated_fix_instructions:
                validation_response["fix_instructions"] = consolidated_fix_instructions
            return validation_response
        except Exception as e:
            logger.warning(f"Failed to process categorized feedback: {str(e)}")
            # Return original response if processing fails
            return validation_response

    def _extract_structured_feedback(
        self, validation_result: Dict[str, Any], entity: str, swea_agent: str, task_type: str
    ) -> Dict[str, Any]:
        """
        Stage 4 Improvement #1: Extract structured feedback for prompt injection.
        Extracts ALL suggestions with original reasoning and context for reuse across retry attempts.
        """
        try:
            extracted_feedback = {
                "entity": entity,
                "swea_agent": swea_agent,
                "task_type": task_type,
                "extraction_timestamp": self._get_timestamp(),
                "all_suggestions": [],
                "original_reasoning": "",
                "structured_instructions": "",
                "feedback_context": {},
            }
            # Extract original reasoning from validation result
            original_reasoning = validation_result.get("details", "")
            extracted_feedback["original_reasoning"] = original_reasoning
            # Extract ALL suggestions from various sources
            all_suggestions = []
            # From categorized feedback (Stage 3)
            categorized_feedback = validation_result.get("categorized_feedback", [])
            for feedback_item in categorized_feedback:
                suggestion = {
                    "priority": feedback_item.get("priority", "REQUIRED"),
                    "issue": feedback_item.get("issue", ""),
                    "fix": feedback_item.get("fix", ""),
                    "source": "categorized_feedback",
                }
                all_suggestions.append(suggestion)
            # From traditional suggestions array
            suggestions = validation_result.get("suggestions", [])
            for suggestion in suggestions:
                all_suggestions.append(
                    {
                        "priority": "REQUIRED",
                        "issue": "",
                        "fix": suggestion,
                        "source": "suggestions_array",
                    }
                )
            # From fix instructions
            fix_instructions = validation_result.get("fix_instructions", [])
            for instruction in fix_instructions:
                all_suggestions.append(
                    {
                        "priority": "REQUIRED",
                        "issue": "",
                        "fix": instruction,
                        "source": "fix_instructions",
                    }
                )
            # From issues array (convert issues to suggestions)
            issues = validation_result.get("issues", [])
            for issue in issues:
                all_suggestions.append(
                    {
                        "priority": "CRITICAL",
                        "issue": issue,
                        "fix": f"Fix: {issue}",
                        "source": "issues_array",
                    }
                )
            extracted_feedback["all_suggestions"] = all_suggestions
            # Create structured instructions for prompt injection
            structured_instructions = []
            if original_reasoning:
                structured_instructions.append(f"TECHLEAD REASONING: {original_reasoning}")
                structured_instructions.append("")
            if all_suggestions:
                structured_instructions.append("PREVIOUS FEEDBACK TO ADDRESS:")
                for i, suggestion in enumerate(all_suggestions, 1):
                    priority_emoji = (
                        "🚨"
                        if suggestion["priority"] == "CRITICAL"
                        else "⚠️" if suggestion["priority"] == "REQUIRED" else "💡"
                    )
                    structured_instructions.append(
                        f"{i}. {priority_emoji} [{suggestion['priority']}] {suggestion['fix']}"
                    )
                    if suggestion["issue"]:
                        structured_instructions.append(f"   Issue: {suggestion['issue']}")
                structured_instructions.append("")
                structured_instructions.append(
                    "MANDATORY: You MUST address ALL the above feedback in your response."
                )
            extracted_feedback["structured_instructions"] = "\n".join(structured_instructions)
            # Store feedback context for analytics
            extracted_feedback["feedback_context"] = {
                "total_suggestions": len(all_suggestions),
                "critical_count": len([s for s in all_suggestions if s["priority"] == "CRITICAL"]),
                "required_count": len([s for s in all_suggestions if s["priority"] == "REQUIRED"]),
                "optional_count": len([s for s in all_suggestions if s["priority"] == "OPTIONAL"]),
                "sources_used": list(set(s["source"] for s in all_suggestions)),
            }
            # Log extraction for analytics
            logger.info(
                f"📋 Stage 4: Structured feedback extracted for {entity}.{swea_agent}.{task_type}"
            )
            logger.info(f"   📝 Total suggestions: {len(all_suggestions)}")
            logger.info(
                f"   🚨 Critical: {extracted_feedback['feedback_context']['critical_count']}"
            )
            logger.info(
                f"   ⚠️  Required: {extracted_feedback['feedback_context']['required_count']}"
            )
            logger.info(
                f"   💡 Optional: {extracted_feedback['feedback_context']['optional_count']}"
            )
            return extracted_feedback
        except Exception as e:
            logger.warning(f"Failed to extract structured feedback: {str(e)}")
            # Return minimal structure if extraction fails
            return {
                "entity": entity,
                "swea_agent": swea_agent,
                "task_type": task_type,
                "extraction_timestamp": self._get_timestamp(),
                "all_suggestions": [],
                "original_reasoning": validation_result.get("details", ""),
                "structured_instructions": "PREVIOUS FEEDBACK TO ADDRESS:\nNo structured feedback available.",
                "feedback_context": {"total_suggestions": 0},
            }

    def _store_feedback_for_reuse(self, extracted_feedback: Dict[str, Any]) -> None:
        """
        Stage 4 Improvement #1: Store extracted feedback for reuse across retry attempts.
        """
        try:
            entity = extracted_feedback.get("entity", "unknown")
            swea_agent = extracted_feedback.get("swea_agent", "unknown")
            task_type = extracted_feedback.get("task_type", "unknown")
            # Create storage key for this specific task
            storage_key = f"{entity}_{swea_agent}_{task_type}"
            # Store in memory for quick access during retry attempts
            TechLeadSWEA.feedback_storage[storage_key] = extracted_feedback
            # Log storage for analytics
            logger.info(f"💾 Stage 4: Feedback stored for reuse: {storage_key}")
            logger.info(
                f"   📝 Suggestions stored: {extracted_feedback.get('feedback_context', {}).get('total_suggestions', 0)}"
            )
        except Exception as e:
            logger.warning(f"Failed to store feedback for reuse: {str(e)}")

    def _retrieve_feedback_for_injection(self, entity: str, swea_agent: str, task_type: str) -> str:
        """
        Stage 4 Improvement #1: Retrieve stored feedback for prompt injection.
        Returns structured instructions ready for prompt injection.
        """
        try:
            storage_key = f"{entity}_{swea_agent}_{task_type}"
            stored_feedback = TechLeadSWEA.feedback_storage.get(storage_key)
            if not stored_feedback:
                return ""
            # Return the structured instructions for prompt injection
            structured_instructions = stored_feedback.get("structured_instructions", "")
            if structured_instructions:
                logger.info(f"📤 Stage 4: Feedback retrieved for injection: {storage_key}")
                logger.info(f"   📝 Instructions length: {len(structured_instructions)} characters")
            return structured_instructions
        except Exception as e:
            logger.warning(f"Failed to retrieve feedback for injection: {str(e)}")
            return ""

    def _clear_feedback_storage(
        self, entity: str = None, swea_agent: str = None, task_type: str = None
    ) -> None:
        """
        Stage 4 Improvement #1: Clear stored feedback when no longer needed.
        Can clear specific feedback or all feedback.
        """
        try:
            if entity and swea_agent and task_type:
                # Clear specific feedback
                storage_key = f"{entity}_{swea_agent}_{task_type}"
                if storage_key in TechLeadSWEA.feedback_storage:
                    del TechLeadSWEA.feedback_storage[storage_key]
                    logger.info(f"🗑️  Stage 4: Cleared specific feedback: {storage_key}")
            else:
                # Clear all feedback
                cleared_count = len(TechLeadSWEA.feedback_storage)
                TechLeadSWEA.feedback_storage.clear()
                logger.info(f"🗑️  Stage 4: Cleared all feedback storage ({cleared_count} entries)")
        except Exception as e:
            logger.warning(f"Failed to clear feedback storage: {str(e)}")

    def _check_escalation_needed(self, critical_feedback: List[Dict[str, Any]]) -> bool:
        """
        Stage 3 Improvement #4: Check if CRITICAL issues need Human Expert escalation.
        Based on issue complexity and retry history.
        """
        if not critical_feedback:
            return False
        # Escalation criteria for CRITICAL issues
        escalation_patterns = [
            "security vulnerability",
            "data corruption",
            "system architecture",
            "infrastructure",
            "deployment",
            "performance critical",
            "memory leak",
            "deadlock",
            "race condition",
        ]
        for feedback_item in critical_feedback:
            issue_text = feedback_item.get("issue", "").lower()
            if any(pattern in issue_text for pattern in escalation_patterns):
                logger.warning(
                    f"🚨 CRITICAL issue may need Human Expert escalation: {issue_text[:100]}"
                )
                return True
        return False

    def _escalate_to_human_expert(
        self, entity: str, critical_issues: List[Dict[str, Any]], retry_count: int
    ) -> Dict[str, Any]:
        """
        Stage 3 Improvement #4: Option A - Human Expert Escalation for unresolvable CRITICAL issues.
        """
        escalation_report = {
            "escalation_type": "human_expert_required",
            "entity": entity,
            "critical_issues_count": len(critical_issues),
            "retry_attempts": retry_count,
            "max_retries_reached": True,
            "escalation_timestamp": self._get_timestamp(),
            "critical_issues": critical_issues,
            "recommended_actions": [],
            "human_expert_guidance_needed": True,
            "system_generation_paused": True,
        }
        # Generate specific recommendations for human expert
        for issue in critical_issues:
            escalation_report["recommended_actions"].append(
                {
                    "issue": issue.get("issue", "Unknown critical issue"),
                    "suggested_fix": issue.get("fix", "Manual intervention required"),
                    "complexity": "high",
                    "requires_architecture_decision": True,
                }
            )
        # Log escalation for human expert attention
        logger.error("🚨 ESCALATION TO HUMAN EXPERT REQUIRED:")
        logger.error(f"   📋 Entity: {entity}")
        logger.error(f"   🔄 Retry attempts: {retry_count}")
        logger.error(f"   🚨 Critical issues: {len(critical_issues)}")
        logger.error("   ⏸️  System generation PAUSED - Human Expert intervention needed")
        # Create detailed escalation log
        escalation_log = []
        for i, issue in enumerate(critical_issues, 1):
            escalation_log.append(f"CRITICAL ISSUE {i}: {issue.get('issue', 'Unknown')}")
            escalation_log.append(
                f"SUGGESTED FIX: {issue.get('fix', 'Manual intervention required')}"
            )
            escalation_log.append("---")
        logger.error("📋 ESCALATION DETAILS:\n" + "\n".join(escalation_log))
        return escalation_report

    def _parse_manual_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response manually when JSON parsing fails."""
        response_lower = response.lower()
        # Determine validity from response content
        is_valid = True
        quality_score = 0.8
        issues = []
        suggestions = []
        # Check for rejection indicators
        if any(
            phrase in response_lower
            for phrase in ["invalid", "reject", "fail", "error", "incomplete", "empty"]
        ):
            is_valid = False
            quality_score = 0.3
        # Check for approval indicators
        if any(
            phrase in response_lower for phrase in ["valid", "approve", "pass", "complete", "good"]
        ):
            is_valid = True
            quality_score = 0.9
        # Extract issues and suggestions
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                if any(word in line.lower() for word in ["issue", "problem", "error", "fail"]):
                    issues.append(line[1:].strip())
                elif any(word in line.lower() for word in ["suggest", "improve", "fix"]):
                    suggestions.append(line[1:].strip())
        return {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "details": response,
            "issues": issues if issues else ["Manual parsing used - review required"],
            "suggestions": suggestions if suggestions else ["Review the generated code manually"],
        }

    def _perform_context_checks(
        self, entity: str, swea_agent: str, task_type: str, code: str, file_path: str
    ) -> Dict[str, Any]:
        """Perform additional context-specific validation checks."""
        context_issues = []
        context_suggestions = []
        # Check for empty code
        if not code.strip():
            context_issues.append("Generated code is empty")
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "context_issues": context_issues,
                "context_suggestions": ["Regenerate the code with proper implementation"],
            }
        # Check for placeholder comments
        placeholder_patterns = [
            r"# TODO",
            r"# FIXME",
            r"pass\s*#",
            r"# placeholder",
            r"# implement",
            r"# add",
            r"# complete",
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                context_issues.append(f"Contains placeholder comments: {pattern}")
        # Check for empty classes/functions
        if "class" in code and "pass" in code:
            context_issues.append("Contains empty classes with pass statements")
        # Check for proper imports
        if "from fastapi import" in code and "import fastapi" not in code:
            context_suggestions.append("Consider using 'import fastapi' for better clarity")
        # Check for proper error handling
        if "HTTPException" not in code and "except" not in code and "api" in task_type.lower():
            context_suggestions.append("Add proper error handling with HTTPException")
        # Check for proper status codes
        if "status_code=201" not in code and "post" in code.lower():
            context_suggestions.append("Add proper status codes for POST endpoints")
        return {"context_issues": context_issues, "context_suggestions": context_suggestions}

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

    def _create_enhanced_coordination_plan(
        self,
        entity: str,
        attributes: List[str],
        context: str,
        is_evolution: bool,
        technical_analysis: Dict[str, Any],
        quality_gates: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Create enhanced coordination plan with test generation moved to Phase 2.
        Phase 1 focuses on artifact generation, Phase 2 handles test generation and validation.
        """
        coordination_plan = []
        # Phase 1: Artifact Generation (Database, Backend, Frontend)
        if not is_evolution:
            # Initial system generation
            coordination_plan.extend(
                [
                    {
                        "swea_agent": "DatabaseSWEA",
                        "task_type": "setup_database",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "database_type": "sqlite",
                            "schema_optimization": True,
                        },
                        "priority": 1,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "database_type": "sqlite",
                            "schema_optimization": True,
                            "data_integrity": "high",
                        },
                        "quality_criteria": [
                            "schema_validation",
                            "data_integrity_check",
                            "performance_optimization",
                        ],
                    },
                    {
                        "swea_agent": "BackendSWEA",
                        "task_type": "generate_model",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "framework": "pydantic",
                            "validation": "comprehensive",
                        },
                        "priority": 2,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "framework": "pydantic",
                            "validation": "comprehensive",
                            "type_safety": "strict",
                        },
                        "quality_criteria": [
                            "model_validation",
                            "type_safety_check",
                            "business_rule_compliance",
                        ],
                    },
                    {
                        "swea_agent": "BackendSWEA",
                        "task_type": "generate_api",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "framework": "fastapi",
                            "crud_operations": True,
                        },
                        "priority": 3,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "framework": "fastapi",
                            "crud_operations": True,
                            "api_documentation": "auto_generated",
                        },
                        "quality_criteria": [
                            "api_validation",
                            "endpoint_coverage",
                            "documentation_quality",
                        ],
                    },
                    {
                        "swea_agent": "FrontendSWEA",
                        "task_type": "generate_ui",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "framework": "streamlit",
                            "features": ["crud_operations", "data_visualization"],
                        },
                        "priority": 4,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "framework": "streamlit",
                            "responsiveness": "mobile_friendly",
                            "user_experience": "intuitive",
                        },
                        "quality_criteria": [
                            "ui_usability",
                            "accessibility_compliance",
                            "user_experience_validation",
                        ],
                    },
                ]
            )
        else:
            # Evolution: Update existing components
            coordination_plan.extend(
                [
                    {
                        "swea_agent": "DatabaseSWEA",
                        "task_type": "migrate_schema",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "migration_strategy": "backward_compatible",
                        },
                        "priority": 1,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "migration_strategy": "backward_compatible",
                            "data_preservation": True,
                        },
                        "quality_criteria": [
                            "migration_safety",
                            "data_integrity_preservation",
                            "backward_compatibility",
                        ],
                    },
                    {
                        "swea_agent": "BackendSWEA",
                        "task_type": "generate_model",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "evolution": True,
                            "backward_compatibility": True,
                        },
                        "priority": 2,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "evolution": True,
                            "backward_compatibility": True,
                            "api_versioning": "semantic",
                        },
                        "quality_criteria": [
                            "evolution_safety",
                            "backward_compatibility_check",
                            "api_versioning_validation",
                        ],
                    },
                    {
                        "swea_agent": "BackendSWEA",
                        "task_type": "generate_api",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "evolution": True,
                            "version_compatibility": True,
                        },
                        "priority": 3,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "evolution": True,
                            "version_compatibility": True,
                            "endpoint_consistency": True,
                        },
                        "quality_criteria": [
                            "evolution_validation",
                            "version_compatibility_check",
                            "endpoint_consistency_validation",
                        ],
                    },
                    {
                        "swea_agent": "FrontendSWEA",
                        "task_type": "generate_ui",
                        "payload": {
                            "entity": entity,
                            "attributes": attributes,
                            "context": context,
                            "evolution": True,
                            "ui_consistency": True,
                        },
                        "priority": 4,
                        "requires_approval": "TechLeadSWEA",
                        "technical_requirements": {
                            "evolution": True,
                            "ui_consistency": True,
                            "user_experience_preservation": True,
                        },
                        "quality_criteria": [
                            "evolution_ui_validation",
                            "consistency_check",
                            "user_experience_preservation",
                        ],
                    },
                ]
            )
        # Final review for Phase 1 (artifact generation only)
        coordination_plan.append(
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "review_and_approve",
                "payload": {
                    "entity": entity,
                    "context": context,
                    "system_components": ["database", "backend", "frontend"],
                    "phase": "phase_1_complete",
                    "final_review": True,
                },
                "priority": 5,
                "governance_role": "phase_1_approval",
                "technical_requirements": {
                    "artifact_quality": "production_ready",
                    "integration": "seamless",
                    "phase_2_ready": True,
                },
                "quality_criteria": [
                    "artifact_quality_validation",
                    "integration_validation",
                    "phase_2_readiness_check",
                ],
            }
        )
        return coordination_plan

    def _conduct_final_system_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct final system review with comprehensive technical governance"""
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
                        "System ready for production deployment",
                        "Monitor system performance metrics",
                        "Implement continuous integration",
                    ]
                )
            else:
                final_recommendations.extend(
                    [
                        "Address component failures before deployment",
                        "Improve system integration score",
                        "Review technical architecture decisions",
                    ]
                )
            # Calculate system quality score
            quality_score = integration_score if overall_success else integration_score * 0.5
            return {
                "success": True,
                "data": {
                    "overall_approval": overall_success,
                    "deployment_ready": deployment_ready,
                    "system_quality_score": quality_score,
                    "integration_score": integration_score,
                    "component_reviews": component_reviews,
                    "final_recommendations": final_recommendations,
                    "entity": entity,
                    "reviewed_components": len(execution_results),
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

    def _log_decision(
        self, decision_type: str, entity: str, decision: str, rationale: str, **kwargs
    ):
        """
        Centralized decision logging for all TechLeadSWEA decisions.
        Provides simple, concise summaries without code duplication.
        Args:
            decision_type: Type of decision (Architecture, Coordination, Conflict, etc.)
            entity: Entity being processed
            decision: The decision made (APPROVED, REJECTED, RESOLVED, etc.)
            rationale: Brief explanation of why this decision was made
            **kwargs: Additional context-specific information
        """
        # Only log technical details in debug mode
        if is_debug_mode():
            logger.info(
                "🧠 TechLeadSWEA %s: %s → %s (%s)",
                decision_type.upper(),
                entity,
                decision,
                rationale,
            )
            # Log additional context if provided
            for key, value in kwargs.items():
                if value is not None:
                    logger.info("   📋 %s: %s", key.replace("_", " ").title(), value)
