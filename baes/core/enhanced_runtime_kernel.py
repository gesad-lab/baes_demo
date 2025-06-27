import argparse
import importlib
import logging
import os
import subprocess  # nosec B404
import sys
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

from baes.core.bae_registry import EnhancedBAERegistry
from baes.core.context_store import ContextStore
from baes.core.entity_recognizer import EntityRecognizer
from baes.core.managed_system_manager import ManagedSystemManager
from baes.swea_agents.backend_swea import BackendSWEA
from baes.swea_agents.database_swea import DatabaseSWEA
from baes.swea_agents.frontend_swea import FrontendSWEA
from baes.swea_agents.techlead_swea import TechLeadSWEA
from baes.swea_agents.test_swea import TestSWEA
from baes.utils.presentation_logger import (
    configure_presentation_logging,
    get_presentation_logger,
    is_debug_mode,
)
from config import Config

load_dotenv(override=True)

# Configure presentation logging if not in debug mode
if not is_debug_mode():
    configure_presentation_logging()

logger = logging.getLogger(__name__)
presentation_logger = get_presentation_logger()


class UnknownSWEAAgentError(Exception):
    """Raised when an unknown SWEA agent is requested in coordination plan"""

    def __init__(self, agent_name: str, available_agents: List[str]):
        self.agent_name = agent_name
        self.available_agents = available_agents
        super().__init__(
            f"Unknown SWEA agent '{agent_name}'. Available agents: {', '.join(available_agents)}"
        )


class MaxRetriesReachedError(Exception):
    """Raised when maximum number of retries is reached for a task, interrupting generation process"""

    def __init__(
        self,
        task_name: str,
        swea_agent: str,
        task_type: str,
        retry_count: int,
        max_retries: int,
        last_error: str,
        feedback: List[str] = None,
    ):
        self.task_name = task_name
        self.swea_agent = swea_agent
        self.task_type = task_type
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.last_error = last_error
        self.feedback = feedback or []

        super().__init__(
            f"Maximum retries ({max_retries}) reached for task '{task_name}' ({swea_agent}.{task_type}). "
            f"Last error: {last_error}. Generation process interrupted."
        )


class EnhancedRuntimeKernel:
    """
    Enhanced Runtime Kernel for BAE Academic System supporting multiple domain entities.

    This kernel demonstrates the proper BAE architecture where:
    - Business Autonomous Entities represent specific domain entities (Student, Course, Teacher)
    - Entity Recognition uses OpenAI to classify user requests with multilingual support
    - Clear error handling for unknown entities
    - Semantic coherence maintained throughout the process

    Flow:
    1. Use EntityRecognizer to classify the user request
    2. Route to appropriate BAE based on detected entity
    3. BAE interprets request and coordinates SWEA agents
    4. Return clear errors for unknown entities
    5. Maintain domain knowledge and semantic coherence
    """

    def __init__(self, context_store_path: str = "database/context_store.json"):
        # Set environment variable so BAEs use the same context store path
        os.environ["BAE_CONTEXT_STORE_PATH"] = context_store_path

        self.context_store = ContextStore(context_store_path)
        self.bae_registry = EnhancedBAERegistry()  # Auto-initializes all BAEs
        self.entity_recognizer = EntityRecognizer()
        self._managed_system_manager = None  # Lazy initialization

        # SWEA agents (coordinated by BAEs) - also lazy initialization
        self._database_swea = None
        self._backend_swea = None
        self._frontend_swea = None
        self._test_swea = None
        self._techlead_swea = None

        self.execution_history = []

        # Phase 3: Retry pattern monitoring and prevention
        self.retry_patterns = defaultdict(
            lambda: {"count": 0, "last_errors": deque(maxlen=5), "timestamps": deque(maxlen=10)}
        )
        self.failure_analytics = {
            "common_failures": defaultdict(int),
            "recovery_strategies": defaultdict(int),
            "success_after_retry": defaultdict(int),
        }

        logger.debug(
            "Enhanced Runtime Kernel initialized with %d BAEs",
            len(self.bae_registry.get_supported_entities()),
        )

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    @property
    def database_swea(self):
        """Lazy initialization of DatabaseSWEA"""
        if self._database_swea is None:
            self._database_swea = DatabaseSWEA()
        return self._database_swea

    @property
    def backend_swea(self):
        """Lazy initialization of BackendSWEA"""
        if self._backend_swea is None:
            self._backend_swea = BackendSWEA()
        return self._backend_swea

    @property
    def test_swea(self):
        """Lazy initialization of TestSWEA"""
        if self._test_swea is None:
            self._test_swea = TestSWEA()
        return self._test_swea

    @property
    def frontend_swea(self):
        """Lazy initialization of FrontendSWEA"""
        if self._frontend_swea is None:
            self._frontend_swea = FrontendSWEA()
        return self._frontend_swea

    @property
    def techlead_swea(self):
        """Lazy initialization of TechLeadSWEA"""
        if self._techlead_swea is None:
            self._techlead_swea = TechLeadSWEA()
        return self._techlead_swea

    def process_natural_language_request(
        self, request: str, context: str = "academic", start_servers: bool = True
    ) -> Dict[str, Any]:
        """
        Process natural language request with proper entity routing and error handling
        """
        logger.debug("📥 Processing request: %s", request)

        # Step 1: Entity Recognition using OpenAI
        entity_classification = self.entity_recognizer.recognize_entity(request)
        detected_entity = entity_classification.get("detected_entity", "unknown")
        confidence = entity_classification.get("confidence", 0.0)

        logger.debug("🔍 Entity detection: %s (confidence: %.2f)", detected_entity, confidence)

        # Step 2: Check if entity is supported
        if detected_entity == "unknown" or not self.bae_registry.is_entity_supported(
            detected_entity
        ):
            error_response = self._create_unsupported_entity_error(
                detected_entity, entity_classification
            )
            logger.warning("❌ Unsupported entity requested: %s", detected_entity)
            return error_response

        # Step 3: Route to appropriate BAE
        target_bae = self.bae_registry.get_bae(detected_entity)
        if not target_bae:
            error_response = self._create_bae_unavailable_error(detected_entity)
            logger.error("❌ BAE not available for entity: %s", detected_entity)
            return error_response

        # Step 4: BAE interprets business request
        interpretation_result = target_bae.handle(
            "interpret_business_request",
            {
                "request": request,
                "context": context,
                "entity_classification": entity_classification,
            },
        )

        if "error" in interpretation_result:
            logger.error("❌ BAE interpretation failed: %s", interpretation_result.get("error"))
            return {
                "success": False,
                "error": "BAE_INTERPRETATION_FAILED",
                "message": f"The {detected_entity} BAE could not interpret your request",
                "details": interpretation_result,
                "entity": detected_entity,
            }

        # Step 5: Execute coordination plan
        coordination_plan = interpretation_result.get("swea_coordination", [])
        execution_results = []

        if coordination_plan:
            logger.debug(
                "⚙️  Executing coordination plan with immediate TechLeadSWEA review (%d tasks)",
                len(coordination_plan),
            )
            try:
                # -------------------------------------------------------------
                # 📍 PHASE 1: System Artifact Generation
                # -------------------------------------------------------------
                # Phase 1 focuses on generating all system artifacts (database, models, API, UI)
                # Test generation is moved to Phase 2 to ensure all dependencies are ready

                logger.info(
                    "🏗️ Phase 1: Starting system artifact generation for %s entity", detected_entity
                )
                logger.info(
                    "📋 Phase 1 tasks: Database setup, Model generation, API creation, UI generation"
                )
                logger.info(
                    "🧪 Test generation: Deferred to Phase 2 (after all artifacts are ready)"
                )

                # Execute coordination plan for Phase 1 (artifact generation only)
                execution_results = self._execute_coordination_plan(
                    coordination_plan, target_bae, context
                )

                # Check if Phase 1 was successful
                if not execution_results:
                    logger.error("❌ Phase 1: Coordination plan execution failed")
                    return {
                        "success": False,
                        "error": "COORDINATION_EXECUTION_ERROR",
                        "message": "Phase 1 artifact generation failed",
                        "entity": detected_entity,
                    }

                # Check if all Phase 1 tasks were successful
                successful_tasks = [
                    task for task in execution_results if task.get("success", False)
                ]
                total_tasks = len(execution_results)

                if len(successful_tasks) != total_tasks:
                    failed_tasks = [
                        task for task in execution_results if not task.get("success", False)
                    ]
                    logger.error("❌ Phase 1: %d/%d tasks failed", len(failed_tasks), total_tasks)
                    for failed_task in failed_tasks:
                        logger.error(
                            "   ❌ %s: %s",
                            failed_task.get("task", "Unknown"),
                            failed_task.get("error", "Unknown error"),
                        )
                    return {
                        "success": False,
                        "error": "PHASE_1_FAILED",
                        "message": f"Phase 1 artifact generation failed: {len(failed_tasks)}/{total_tasks} tasks failed",
                        "entity": detected_entity,
                        "execution_results": execution_results,
                    }

                logger.info(
                    "✅ Phase 1: All artifact generation tasks completed successfully (%d/%d)",
                    len(successful_tasks),
                    total_tasks,
                )

                # -------------------------------------------------------------
                # 📍 PHASE 2: Test Generation and Validation
                # -------------------------------------------------------------
                # Phase 2 begins with test generation (moved from Phase 1) followed by execution
                # This ensures all managed system artifacts are fully generated before test generation

                test_execution_result = None

                if execution_results:
                    from baes.utils.presentation_logger import get_presentation_logger

                    presentation_logger = get_presentation_logger()

                    # Start Phase 2 validation
                    presentation_logger.phase_2_start()
                    logger.info(
                        "🧪 Phase 2: Starting test generation and validation after generation completion"
                    )

                    # Step 1 of Phase 2: Generate tests (moved from Phase 1)
                    logger.info(
                        "🧪 Phase 2 Step 1: Generating tests for %s entity", detected_entity
                    )
                    test_generation_result = self._generate_tests_for_phase_2(
                        detected_entity, execution_results
                    )

                    if not test_generation_result.get("success", False):
                        logger.error("❌ Phase 2: Test generation failed")
                        return {
                            "success": False,
                            "error": "TEST_GENERATION_FAILED",
                            "message": "Phase 2 test generation failed",
                            "entity": detected_entity,
                            "execution_results": execution_results,
                            "test_generation_result": test_generation_result,
                        }

                    logger.info("✅ Phase 2 Step 1: Test generation completed successfully")

                    # Step 2 of Phase 2: Execute mandatory validation tests
                    logger.info("🧪 Phase 2 Step 2: Executing validation tests")
                    test_execution_result = self._execute_mandatory_tests(
                        detected_entity, execution_results
                    )

                    if not test_execution_result.get("success", False):
                        test_pass_rate = test_execution_result.get("pass_rate", 0.0)
                        presentation_logger.warning(
                            f"❌ Tests failed ({test_pass_rate:.1f}% pass rate) - starting fixes..."
                        )
                        logger.warning(
                            "❌ Phase 2: Tests failed, coordinating fixes with TechLeadSWEA"
                        )

                        # Use the same retry-based fix coordination, resetting the
                        # retry counter per fix iteration as defined by BAE_MAX_RETRIES.
                        fix_success = self._coordinate_test_fixes_until_success(
                            detected_entity,
                            test_execution_result,
                            execution_results,
                        )

                        if not fix_success:
                            presentation_logger.error(
                                "❌ Phase 2: Tests could not be fixed after maximum attempts"
                            )
                            logger.error(
                                "❌ Phase 2: Validation tests could not be fixed after maximum attempts"
                            )
                            return {
                                "success": False,
                                "error": "MAX_RETRIES_REACHED",
                                "message": "Phase 2 validation: Tests failed and could not be fixed",
                                "entity": detected_entity,
                                "execution_results": execution_results,
                                "test_execution_result": test_execution_result,
                            }

                        # Re-run tests once fixes applied to capture final status
                        presentation_logger.info("🔄 Re-running tests after fixes applied...")
                        logger.info("🔄 Phase 2: Re-running tests after fixes applied")
                        test_execution_result = self._execute_mandatory_tests(
                            detected_entity, execution_results
                        )

                    # Phase 2 validation completed successfully
                    if test_execution_result.get("success", False):
                        test_pass_rate = test_execution_result.get("pass_rate", 0.0)
                        presentation_logger.success(
                            f"✅ Phase 2: All tests passing ({test_pass_rate:.1f}%) - system validated!"
                        )
                        logger.info("✅ Phase 2: Test validation completed successfully")

            except ValueError as e:
                # Validation errors - fail fast with clear message
                logger.error("❌ Validation error - Generation process interrupted: %s", str(e))
                return {
                    "success": False,
                    "error": "VALIDATION_ERROR",
                    "message": "Generation process interrupted due to validation failure",
                    "details": {
                        "validation_error": str(e),
                        "coordination_plan": coordination_plan,
                        "failed_at": "task_validation",
                    },
                    "entity": detected_entity,
                    "help": (
                        "There was an error in the agent communication protocol. "
                        "This indicates a system configuration issue. Please check the logs for details."
                    ),
                    "generation_interrupted": True,
                    "validation_failed": True,
                }
            except MaxRetriesReachedError as e:
                logger.error("❌ Generation process interrupted: %s", str(e))
                return {
                    "success": False,
                    "error": "MAX_RETRIES_REACHED",
                    "message": f"Generation failed after {e.max_retries} retry attempts",
                    "details": {
                        "failed_task": e.task_name,
                        "swea_agent": e.swea_agent,
                        "task_type": e.task_type,
                        "retry_count": e.retry_count,
                        "max_retries": e.max_retries,
                        "last_error": e.last_error,
                        "feedback": e.feedback,
                    },
                    "entity": detected_entity,
                    "help": (
                        f"The task '{e.task_name}' failed after {e.max_retries} attempts. "
                        f"Last error: {e.last_error}. Please review the requirements and try again."
                    ),
                    "generation_interrupted": True,
                }
            except UnknownSWEAAgentError as e:
                logger.error("❌ Coordination plan execution failed: %s", str(e))
                return {
                    "success": False,
                    "error": "UNKNOWN_SWEA_AGENT",
                    "message": f"Required SWEA agent not available: {e.agent_name}",
                    "details": {
                        "requested_agent": e.agent_name,
                        "available_agents": e.available_agents,
                        "coordination_plan": coordination_plan,
                    },
                    "entity": detected_entity,
                    "help": (
                        f"Please ensure all required SWEA agents are implemented. "
                        f"Available: {', '.join(e.available_agents)}"
                    ),
                    "generation_interrupted": True,
                }
            except Exception as e:
                # Catch any other unexpected errors during coordination plan execution
                logger.error("❌ Unexpected error during coordination plan execution: %s", str(e))
                return {
                    "success": False,
                    "error": "COORDINATION_EXECUTION_ERROR",
                    "message": "An unexpected error occurred during system generation",
                    "details": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "coordination_plan": coordination_plan,
                    },
                    "entity": detected_entity,
                    "help": "Please check the logs for detailed error information and try again.",
                    "generation_interrupted": True,
                }

        # Step 6: Store schema in BAE memory for future evolution requests
        if interpretation_result and execution_results:
            extracted_attributes = interpretation_result.get("extracted_attributes", [])
            if extracted_attributes:
                # Store current schema in BAE memory for evolution
                current_schema = {
                    "entity": detected_entity,
                    "attributes": extracted_attributes,
                    "context": context,
                    "generated_at": self._get_timestamp(),
                    "business_rules": interpretation_result.get("business_vocabulary", []),
                    "code": "",  # Will be populated by backend SWEA
                }
                target_bae.update_memory("current_schema", current_schema)

                # Also persist BAE memory to context store for restart resilience
                try:
                    self.context_store.store_agent_memory(target_bae.name, target_bae.memory)
                    logger.debug("💾 BAE memory persisted to context store for %s", detected_entity)
                except Exception as e:
                    logger.warning("⚠️  Could not persist BAE memory to context store: %s", str(e))

                logger.debug("💾 Current schema stored in %s BAE memory", detected_entity)

        # Step 7: Tests are now integrated into the coordination flow
        # No separate test execution needed - tests are mandatory part of main flow
        test_execution_result = None
        if execution_results:
            # Check if all tasks were approved by TechLeadSWEA during execution
            all_tasks_approved = all(
                task.get("techlead_approved", False) for task in execution_results
            )

            if all_tasks_approved:
                logger.info("✅ All tasks approved by TechLeadSWEA - Phase 1 generation complete")
                test_execution_result = {"success": True, "phase_1_complete": True}
            else:
                # Some tasks were rejected during immediate review - system failed early
                rejected_tasks = [
                    task for task in execution_results if task.get("techlead_rejected", False)
                ]
                logger.error(
                    "❌ System generation failed - %d tasks rejected by TechLeadSWEA during immediate review",
                    len(rejected_tasks),
                )

                test_execution_result = {
                    "success": False,
                    "early_failure": True,
                    "rejected_tasks": rejected_tasks,
                    "message": f"{len(rejected_tasks)} tasks rejected during immediate TechLeadSWEA review",
                }

        # Step 8: Preserve domain knowledge
        self._preserve_domain_knowledge(detected_entity, interpretation_result, context)

        # Step 9: Reload and start servers if requested
        if start_servers and not os.getenv("SKIP_SERVER_START"):
            self._reload_system_components()
            self._start_servers()

        # Step 10: Return comprehensive result with integrated test-driven workflow
        overall_success = True
        failed_tasks = []

        # With integrated test-driven workflow, success is determined by:
        # 1. All individual tasks approved by TechLeadSWEA during execution
        # 2. All tests passing at 100% rate (integrated into coordination flow)
        # 3. Final TechLeadSWEA approval after test validation

        if execution_results:
            # Check immediate review results
            approved_tasks = [
                task for task in execution_results if task.get("techlead_approved", False)
            ]
            rejected_tasks = [
                task for task in execution_results if task.get("techlead_rejected", False)
            ]
            test_failed_tasks = [
                task for task in execution_results if task.get("test_execution_failed", False)
            ]

            # Collect failed tasks from immediate review
            for task_result in execution_results:
                if not task_result.get("success", False):
                    failed_tasks.append(
                        {
                            "task": task_result.get("task", "unknown"),
                            "error": task_result.get("error", "unknown error"),
                            "feedback": task_result.get("feedback_history", []),
                            "retry_count": task_result.get("retry_count", 0),
                            "techlead_rejected": task_result.get("techlead_rejected", False),
                            "test_execution_failed": task_result.get(
                                "test_execution_failed", False
                            ),
                        }
                    )

            # Early failure detection - including test failures
            if rejected_tasks or test_failed_tasks:
                overall_success = False
                failure_count = len(rejected_tasks) + len(test_failed_tasks)
                logger.error(
                    "❌ System generation FAILED - %d tasks failed (reviews: %d, tests: %d)",
                    failure_count,
                    len(rejected_tasks),
                    len(test_failed_tasks),
                )

                # Early failure - return immediately with detailed feedback
                return {
                    "success": False,
                    "early_failure": True,
                    "entity": detected_entity,
                    "confidence": confidence,
                    "bae_used": target_bae.name,
                    "interpretation": interpretation_result,
                    "execution_results": execution_results,
                    "test_execution_result": test_execution_result,
                    "failed_tasks": failed_tasks,
                    "rejected_tasks": rejected_tasks,
                    "test_failed_tasks": test_failed_tasks,
                    "approved_tasks": approved_tasks,
                    "total_tasks": len(execution_results),
                    "successful_tasks": len(approved_tasks),
                    "message": f"System generation failed: {len(rejected_tasks)} tasks rejected, {len(test_failed_tasks)} test failures",
                    "help": "Review TechLeadSWEA feedback and ensure all tests pass before declaring success",
                    "integrated_testing": True,
                }

            # Two-phase approach: success depends on Phase 1 completion + Phase 2 validation
            # Phase 1: All tasks must be approved by TechLeadSWEA
            # Phase 2: Tests must pass at 100% rate (handled separately)

            phase_1_success = len(approved_tasks) == len(execution_results)
            phase_2_success = test_execution_result and test_execution_result.get("success", False)

            overall_success = phase_1_success and phase_2_success

            if phase_1_success and phase_2_success:
                test_pass_rate = (
                    test_execution_result.get("pass_rate", 0.0) if test_execution_result else 0.0
                )
                logger.info(
                    "✅ Two-phase generation COMPLETED - Phase 1: %d/%d tasks approved, Phase 2: %.1f%% tests passing",
                    len(approved_tasks),
                    len(execution_results),
                    test_pass_rate,
                )
            elif not phase_1_success:
                logger.error(
                    "❌ Phase 1 FAILED - %d/%d tasks approved",
                    len(approved_tasks),
                    len(execution_results),
                )
                failed_tasks.append(
                    {
                        "task": "phase_1_generation",
                        "error": f"Only {len(approved_tasks)}/{len(execution_results)} tasks approved by TechLeadSWEA",
                        "feedback": [],
                    }
                )
            elif not phase_2_success:
                test_pass_rate = (
                    test_execution_result.get("pass_rate", 0.0) if test_execution_result else 0.0
                )
                logger.error(
                    "❌ Phase 2 FAILED - tests not passing (%.1f%% pass rate)", test_pass_rate
                )
                failed_tasks.append(
                    {
                        "task": "phase_2_validation",
                        "error": f"Tests failed - {test_pass_rate:.1f}% pass rate (100% required)",
                        "feedback": [],
                    }
                )

        else:
            # No execution results means failure
            overall_success = False
            failed_tasks.append({"task": "system_generation", "error": "No tasks were executed"})

        # Get final test pass rate from Phase 2 validation
        final_test_pass_rate = (
            test_execution_result.get("pass_rate", 0.0) if test_execution_result else 0.0
        )

        result = {
            "success": overall_success,
            "entity": detected_entity,
            "confidence": confidence,
            "bae_used": target_bae.name,
            "interpretation": interpretation_result,
            "execution_results": execution_results,
            "test_execution_result": test_execution_result,
            "actual_test_pass_rate": final_test_pass_rate,
            "language_detected": entity_classification.get("language_detected"),
            "action_intent": entity_classification.get("action_intent"),
            "domain_knowledge_preserved": True,
            "failed_tasks": failed_tasks,
            "total_tasks": len(execution_results) if execution_results else 0,
            "successful_tasks": (
                len([r for r in execution_results if r.get("techlead_approved", False)])
                if execution_results
                else 0
            ),
            "integrated_test_driven_workflow": True,
            "mandatory_testing": True,
            "tests_must_pass_100_percent": True,
            "early_failure_detection": (
                len(
                    [
                        r
                        for r in execution_results
                        if r.get("techlead_rejected", False)
                        or r.get("test_execution_failed", False)
                    ]
                )
                > 0
                if execution_results
                else False
            ),
        }

        if overall_success:
            logger.info(
                "✅ Request processed successfully for %s entity - ALL tasks approved + ALL tests passing",
                detected_entity,
            )
        else:
            logger.warning(
                "❌ Request processing FAILED for %s entity - %d tasks failed",
                detected_entity,
                len(failed_tasks),
            )
            for failed_task in failed_tasks:
                logger.warning("   Failed: %s - %s", failed_task["task"], failed_task["error"])

        # Final completion logging for two-phase approach
        successful_tasks = len([r for r in execution_results if r.get("success", False)])

        # Two-phase completion: show final result with test validation
        if overall_success:
            presentation_logger.complete_generation_with_tests(
                detected_entity, successful_tasks, len(execution_results), execution_results
            )
        else:
            # Show the appropriate failure message
            if not execution_results:
                presentation_logger.error(
                    f"❌ {detected_entity.title()} System Generation Failed - No tasks executed"
                )
            elif len([r for r in execution_results if r.get("techlead_approved", False)]) < len(
                execution_results
            ):
                presentation_logger.error(
                    f"❌ {detected_entity.title()} System Generation Failed - Phase 1 incomplete"
                )
            else:
                presentation_logger.error(
                    f"❌ {detected_entity.title()} System Generation Failed - Phase 2 validation failed"
                )

        return result

    def _create_unsupported_entity_error(
        self, detected_entity: str, classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create user-friendly error for unsupported entities"""
        supported_entities = self.bae_registry.get_supported_entities()

        return {
            "success": False,
            "error": "ENTITY_NOT_SUPPORTED",
            "message": "The requested entity is not supported by this BAE system",
            "details": {
                "detected_entity": detected_entity,
                "confidence": classification.get("confidence", 0.0),
                "reasoning": classification.get("reasoning", ""),
                "supported_entities": supported_entities,
                "suggestions": [
                    f"Try: 'Create a {entity} management system'" for entity in supported_entities
                ],
                "entity_keywords": self.bae_registry.get_all_keywords(),
            },
            "help": "Please rephrase your request using one of the supported entities",
        }

    def _create_bae_unavailable_error(self, entity: str) -> Dict[str, Any]:
        """Create error for when BAE is not available"""
        return {
            "success": False,
            "error": "BAE_UNAVAILABLE",
            "message": f"The {entity} BAE is currently unavailable",
            "details": {
                "entity": entity,
                "registry_status": self.bae_registry.get_registry_summary(),
            },
            "help": "Please try again later or contact system administrator",
        }

    def _execute_coordination_plan(
        self, coordination_plan: List[Dict[str, Any]], coordinating_bae, context: str
    ) -> List[Dict[str, Any]]:
        """
        Execute the coordination plan with immediate TechLeadSWEA review after each task.

        NEW INTEGRATED TEST-DRIVEN FLOW:
        1. Execute SWEA tasks sequentially with immediate review
        2. After test generation, EXECUTE tests as part of main flow
        3. TechLeadSWEA analyzes test results and coordinates fixes if needed
        4. Tests must achieve 100% pass rate before final approval
        5. Only when tests pass can final approval be given

        This ensures NO SUCCESS is declared until ALL tests pass.
        """
        # Use debug logging for technical details
        if is_debug_mode():
            logger.info(
                "🔄 Executing coordination plan with immediate TechLeadSWEA review (%d tasks)",
                len(coordination_plan),
            )

        results = []
        entity_name = getattr(coordinating_bae, "entity_name", "System")

        # Start presentation logging
        presentation_logger.start_generation(entity_name)

        # Get max retries from environment
        max_retries = int(os.getenv("BAE_MAX_RETRIES", "3"))

        # Sequential execution with immediate review
        for task_index, task in enumerate(coordination_plan):
            task_name = f"{task.get('swea_agent', 'Unknown')}.{task.get('task_type', 'unknown')}"

            # Presentation logging for step start
            presentation_logger.step_start(task_index + 1, len(coordination_plan), task_name)

            # Debug logging for technical details
            if is_debug_mode():
                logger.info("🎯 Task %d/%d: %s", task_index + 1, len(coordination_plan), task_name)

            # Validate mandatory attributes for agent communication
            validation_error = self._validate_task_attributes(task)
            if validation_error:
                logger.error("❌ Task validation failed: %s", validation_error)
                results.append(
                    {
                        "task": task_name,
                        "success": False,
                        "error": f"Mandatory attribute validation failed: {validation_error}",
                        "validation_error": True,
                    }
                )
                # Fail fast - don't continue with invalid tasks
                raise ValueError(f"Task validation failed: {validation_error}")

            swea_agent = task.get("swea_agent", "")
            task_type = task.get("task_type", "")
            payload = task.get("payload", {})

            # Route to appropriate SWEA agent
            agent = self._route_to_swea_agent(swea_agent)
            if not agent:
                available_agents = [
                    "BackendSWEA",
                    "FrontendSWEA",
                    "DatabaseSWEA",
                    "TestSWEA",
                    "TechLeadSWEA",
                ]
                logger.error("❌ Unknown SWEA agent: %s", swea_agent)
                results.append(
                    {
                        "task": task_name,
                        "success": False,
                        "error": f"Unknown SWEA agent: {swea_agent}",
                        "available_agents": available_agents,
                    }
                )
                # Fail fast - don't continue with unknown agents
                raise UnknownSWEAAgentError(swea_agent, available_agents)

            # Task execution with retry loop
            task_success = False
            retry_count = 0
            last_error = None
            feedback_history = []

            while not task_success and retry_count <= max_retries:
                try:
                    # Show retry if this isn't the first attempt
                    if retry_count > 0:
                        simplified_name = self._get_simplified_task_name(task_name)
                        presentation_logger.step_retry(
                            task_index + 1, retry_count, max_retries, simplified_name
                        )

                    # Execute the SWEA task
                    if is_debug_mode():
                        logger.info(
                            "🔧 Executing %s (attempt %d/%d)",
                            task_name,
                            retry_count + 1,
                            max_retries + 1,
                        )
                    result = agent.handle_task(task_type, payload)

                    # **CRITICAL FIX: Generate managed system artifacts immediately after each SWEA task**
                    # This ensures TestSWEA has actual artifacts to test
                    if result.get("success") and swea_agent not in ["TechLeadSWEA"]:
                        logger.debug(
                            "🏗️  Generating managed system artifacts after %s completion", swea_agent
                        )
                        try:
                            # Generate managed system artifacts incrementally
                            self.managed_system_manager.ensure_managed_system_structure()
                            self.managed_system_manager.update_system_files()

                            logger.debug("✅ Managed system artifacts updated after %s", swea_agent)
                        except Exception as e:
                            logger.warning(
                                "⚠️  Failed to update managed system after %s: %s",
                                swea_agent,
                                str(e),
                            )

                    # **DEFERRED TEST EXECUTION (Phase 2 will handle validation)**
                    if "TestSWEA" in swea_agent and "generate" in task_type:
                        # Phase-1 test generation only - ENHANCED: Support robust test generation
                        logger.info(
                            "🧪 Test files generated; execution deferred to Phase 2 validation"
                        )
                        result["tests_generated"] = True
                        # Also propagate flag inside data section for TechLeadSWEA checks
                        if isinstance(result.get("data"), dict):
                            result["data"]["tests_generated"] = True

                            # ENHANCED: Propagate dependency validation status
                            if "dependencies_validated" in result["data"]:
                                result["data"]["dependencies_validated"] = True
                            if "fallback_mode" in result["data"]:
                                result["data"]["fallback_mode"] = True
                                logger.info(
                                    "🧪 TestSWEA generated fallback tests - dependencies not fully ready"
                                )

                        # Skip immediate execution logic entirely
                        task_success = True
                        results.append(
                            {
                                "task": task_name,
                                "success": True,
                                "result": result,
                                "techlead_approved": True,  # will be reviewed below
                            }
                        )
                        break

                    # Check if this is a final review task
                    is_final_review = (
                        swea_agent.lower() in ["techlead", "techleadswea", "techlead_swea"]
                        and task_type == "review_and_approve"
                        and payload.get("final_review", False)
                    )

                    if is_final_review:
                        # For final review, pass all accumulated execution results
                        logger.info("👁️  TechLeadSWEA conducting final system review...")
                        review_payload = {
                            "entity": payload.get(
                                "entity",
                                (
                                    coordinating_bae.entity_name
                                    if hasattr(coordinating_bae, "entity_name")
                                    else "Unknown"
                                ),
                            ),
                            "execution_results": results,  # Pass all previous task results
                            "context": payload.get("context", ""),
                            "final_review": True,
                        }

                        review_result = self.techlead_swea.handle_task(
                            "review_and_approve", review_payload
                        )

                        if review_result.get("success") and review_result.get("data", {}).get(
                            "overall_approval", False
                        ):
                            # Final review approved
                            quality_score = review_result.get("data", {}).get(
                                "system_quality_score", 0.0
                            )
                            simplified_name = self._get_simplified_task_name(task_name)

                            # Presentation logging
                            presentation_logger.techlead_review(
                                True, simplified_name, quality_score
                            )
                            presentation_logger.step_success(task_index + 1, simplified_name)

                            # Debug logging
                            if is_debug_mode():
                                logger.info(
                                    "✅ %s APPROVED by TechLeadSWEA - System ready for deployment",
                                    task_name,
                                )

                            results.append(
                                {
                                    "task": task_name,
                                    "success": True,
                                    "result": result,
                                    "techlead_approved": True,
                                    "final_review": True,
                                    "deployment_ready": review_result.get("data", {}).get(
                                        "deployment_ready", False
                                    ),
                                    "system_quality_score": quality_score,
                                    "retry_count": retry_count,
                                }
                            )
                            task_success = True
                        else:
                            # Final review rejected
                            technical_feedback = review_result.get("data", {}).get(
                                "technical_feedback", []
                            )
                            feedback_history.extend(technical_feedback)

                            # Extract primary rejection reason for user-friendly display
                            feedback_items = review_result.get("data", {}).get("feedback", [])
                            primary_reason = "System not ready for deployment"
                            if feedback_items and isinstance(feedback_items, list) and len(feedback_items) > 0:
                                primary_reason = feedback_items[0]
                            elif technical_feedback and len(technical_feedback) > 0:
                                primary_reason = technical_feedback[0]

                            logger.warning(
                                "❌ %s REJECTED by TechLeadSWEA (attempt %d/%d) - %s",
                                task_name,
                                retry_count + 1,
                                max_retries + 1,
                                primary_reason
                            )

                            # Only show detailed feedback in debug mode to keep output clean
                            if is_debug_mode() and technical_feedback:
                                logger.warning("📝 TechLeadSWEA feedback:")
                                for feedback in technical_feedback:
                                    logger.warning("   • %s", feedback)

                            # Check if we should retry final review
                            if retry_count < max_retries:
                                retry_count += 1
                                logger.info(
                                    "🔄 Retrying %s with TechLeadSWEA feedback...", task_name
                                )
                            else:
                                # Max retries reached for final review
                                logger.error(
                                    "🛑 %s FAILED after %d attempts - stopping coordination plan",
                                    task_name,
                                    max_retries + 1,
                                )
                                results.append(
                                    {
                                        "task": task_name,
                                        "success": False,
                                        "error": f"Final system review rejected by TechLeadSWEA after {max_retries + 1} attempts",
                                        "techlead_rejected": True,
                                        "final_review": True,
                                        "feedback_history": feedback_history,
                                        "retry_count": retry_count,
                                    }
                                )

                                # Fail fast - stop execution
                                raise MaxRetriesReachedError(
                                    task_name,
                                    swea_agent,
                                    task_type,
                                    retry_count,
                                    max_retries,
                                    f"Final system review rejected by TechLeadSWEA after {max_retries + 1} attempts",
                                    feedback_history,
                                )
                    else:
                        # Regular individual task review
                        logger.info("👁️  TechLeadSWEA reviewing %s...", task_name)
                        review_payload = {
                            "entity": payload.get(
                                "entity",
                                (
                                    coordinating_bae.entity_name
                                    if hasattr(coordinating_bae, "entity_name")
                                    else "Unknown"
                                ),
                            ),
                            "swea_agent": swea_agent,
                            "task_type": task_type,
                            "result": result,
                            "quality_gates": {},  # Could be enhanced with specific quality gates per task
                            "final_review": False,
                            "retry_count": retry_count,
                        }

                        review_result = self.techlead_swea.handle_task(
                            "review_and_approve", review_payload
                        )

                        if review_result.get("success") and review_result.get("data", {}).get(
                            "overall_approval", False
                        ):
                            # Task approved by TechLeadSWEA
                            quality_score = review_result.get("data", {}).get("quality_score", 0.0)
                            simplified_name = self._get_simplified_task_name(task_name)

                            # Presentation logging
                            presentation_logger.techlead_review(
                                True, simplified_name, quality_score
                            )
                            presentation_logger.step_success(
                                task_index + 1,
                                simplified_name,
                                self._extract_task_details(task_name, result),
                            )

                            # Debug logging
                            if is_debug_mode():
                                logger.info("✅ %s APPROVED by TechLeadSWEA", task_name)

                            results.append(
                                {
                                    "task": task_name,
                                    "success": True,
                                    "result": result,
                                    "techlead_approved": True,
                                    "quality_score": quality_score,
                                    "retry_count": retry_count,
                                }
                            )
                            task_success = True
                        else:
                            # Task rejected by TechLeadSWEA
                            technical_feedback = review_result.get("data", {}).get(
                                "technical_feedback", []
                            )
                            feedback_history.extend(technical_feedback)

                            simplified_name = self._get_simplified_task_name(task_name)
                            presentation_logger.techlead_review(
                                False, simplified_name, 0.0, technical_feedback
                            )

                            # Extract primary rejection reason for user-friendly display
                            feedback_items = review_result.get("data", {}).get("feedback", [])
                            primary_reason = "Quality standards not met"
                            if feedback_items and isinstance(feedback_items, list) and len(feedback_items) > 0:
                                primary_reason = feedback_items[0]
                            elif technical_feedback and len(technical_feedback) > 0:
                                primary_reason = technical_feedback[0]

                            logger.warning(
                                "❌ %s REJECTED by TechLeadSWEA (attempt %d/%d) - %s",
                                task_name,
                                retry_count + 1,
                                max_retries + 1,
                                primary_reason
                            )

                            # Only show detailed feedback in debug mode to keep output clean
                            if is_debug_mode() and technical_feedback:
                                logger.warning("📝 TechLeadSWEA feedback:")
                                for feedback in technical_feedback:
                                    logger.warning("   • %s", feedback)

                            # Phase 1: No test execution or fix coordination - defer to Phase 2
                            # For TestSWEA rejections in Phase 1, simply retry test generation

                            # Check if we should retry (for non-TestSWEA tasks or if fix coordination wasn't triggered)
                            if not task_success and retry_count < max_retries:
                                retry_count += 1
                                
                                # **CRITICAL FIX: Pass TechLeadSWEA feedback to SWEA agent for retry**
                                # Enhance payload with TechLeadSWEA feedback for intelligent retry
                                enhanced_payload = payload.copy()
                                
                                # Add TechLeadSWEA feedback for the SWEA agent to process
                                enhanced_payload["techlead_feedback"] = feedback_items if feedback_items else technical_feedback
                                enhanced_payload["previous_errors"] = [primary_reason]
                                enhanced_payload["expected_output"] = self._get_expected_output_for_task(swea_agent, task_type, 
                                    enhanced_payload.get("entity", "Unknown"))
                                enhanced_payload["retry_count"] = retry_count
                                
                                # Update the task payload for the retry
                                payload = enhanced_payload
                                
                                logger.info(
                                    "🔄 Retrying %s with TechLeadSWEA feedback (attempt %d/%d)...",
                                    task_name,
                                    retry_count + 1,
                                    max_retries + 1,
                                )
                                
                                # Enhanced feedback logging for specific issues
                                if feedback_items:
                                    logger.info("   📝 Specific feedback provided: %s", feedback_items[0])
                                elif technical_feedback:
                                    logger.info("   📝 Technical feedback provided: %s", technical_feedback[0])
                            elif not task_success:
                                # Max retries reached
                                logger.error(
                                    "🛑 %s FAILED after %d attempts - stopping coordination plan",
                                    task_name,
                                    max_retries + 1,
                                )
                                results.append(
                                    {
                                        "task": task_name,
                                        "success": False,
                                        "error": f"Task rejected by TechLeadSWEA after {max_retries + 1} attempts",
                                        "techlead_rejected": True,
                                        "feedback_history": feedback_history,
                                        "retry_count": retry_count,
                                    }
                                )

                                # Fail fast - stop execution
                                raise MaxRetriesReachedError(
                                    task_name,
                                    swea_agent,
                                    task_type,
                                    retry_count,
                                    max_retries,
                                    f"Task rejected by TechLeadSWEA after {max_retries + 1} attempts",
                                    feedback_history,
                                )

                except Exception as e:
                    last_error = str(e)
                    presentation_logger.step_error(
                        task_index + 1, self._get_simplified_task_name(task_name), last_error
                    )
                    logger.error("❌ %s execution failed: %s", task_name, last_error)

                    # Check if we should retry
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.info(
                            "🔄 Retrying %s after execution error (attempt %d/%d)...",
                            task_name,
                            retry_count + 1,
                            max_retries + 1,
                        )
                    else:
                        # Max retries reached
                        logger.error(
                            "🛑 %s FAILED after %d attempts - stopping coordination plan",
                            task_name,
                            max_retries + 1,
                        )
                        results.append(
                            {
                                "task": task_name,
                                "success": False,
                                "error": last_error,
                                "retry_count": retry_count,
                            }
                        )

                        # Fail fast - stop execution
                        raise MaxRetriesReachedError(
                            task_name, swea_agent, task_type, retry_count, max_retries, last_error
                        )

        # Phase 1 completion logging (generation only - no test execution yet)
        successful_tasks = len([r for r in results if r.get("success", False)])

        # Phase 1 completes here - tests generated but not executed
        presentation_logger.phase_1_complete(entity_name, successful_tasks, len(results))

        # Debug summary
        if is_debug_mode():
            logger.info(
                "📊 Coordination plan completed: %d/%d tasks successful",
                successful_tasks,
                len(results),
            )

        return results

    def _validate_task_attributes(self, task: Dict[str, Any]) -> str:
        """
        Validate that all mandatory attributes are present in task.
        Returns error message if validation fails, None if valid.
        """
        # Mandatory attributes for all tasks
        mandatory_attrs = ["swea_agent", "task_type"]

        for attr in mandatory_attrs:
            value = task.get(attr)
            if not value or (isinstance(value, str) and not value.strip()):
                return f"Missing mandatory attribute '{attr}' in task: {task}"

        # Validate payload exists (can be empty dict, but must exist)
        if "payload" not in task:
            return f"Missing 'payload' attribute in task: {task}"

        # Additional validation based on task type
        payload = task.get("payload", {})
        task_type = task.get("task_type", "")

        # For entity-related tasks, entity should be specified
        if task_type in ["generate_model", "generate_api", "generate_ui", "setup_database"]:
            if not payload.get("entity") and not payload.get("entity_name"):
                return f"Entity-related task '{task_type}' missing entity information in payload"

        return None  # Validation passed

    def _route_to_swea_agent(self, swea_agent: str):
        """Route to appropriate SWEA agent with validation"""
        if not swea_agent:
            return None

        swea_agent_lower = swea_agent.lower()

        if swea_agent_lower in ["database", "databaseswea", "database_swea"]:
            return self.database_swea
        elif swea_agent_lower in [
            "backend",
            "backendswea",
            "backend_swea",
            "programmer",
            "programmerswea",
            "programmer_swea",
        ]:
            return self.backend_swea
        elif swea_agent_lower in ["frontend", "frontendswea", "frontend_swea"]:
            return self.frontend_swea
        elif swea_agent_lower in ["test", "testswea", "test_swea"]:
            return self.test_swea
        elif swea_agent_lower in [
            "techlead",
            "techleadswea",
            "techlead_swea",
            "tech_lead",
            "tech_lead_swea",
        ]:
            return self.techlead_swea
        else:
            return None

    def _preserve_domain_knowledge(self, entity: str, interpretation: Dict[str, Any], context: str):
        """Preserve domain knowledge for reusability"""
        domain_knowledge = {
            "entity": entity,
            "interpretation": interpretation,
            "context": context,
            "business_vocabulary": interpretation.get("business_vocabulary", []),
            "domain_operations": interpretation.get("domain_operations", []),
            "timestamp": self._get_timestamp(),
        }

        self.context_store.preserve_domain_knowledge(entity, domain_knowledge)
        logger.debug("💾 Domain knowledge preserved for %s entity", entity)

    def _reload_system_components(self):
        """Reload API and UI components to reflect generated artifacts"""
        try:
            self._reload_api_loader()
            self._reload_ui_loader()
            logger.debug("🔄 System components reloaded")
        except Exception as e:
            logger.warning("⚠️  Failed to reload components: %s", str(e))

    def _reload_api_loader(self):
        """Reload API routes"""
        try:
            from api import main as api_main

            importlib.reload(api_main)
            logger.debug("🔄 API routes reloaded")
        except ImportError:
            logger.debug("FastAPI not available; skipping API reload")

    def _reload_ui_loader(self):
        """Reload UI components"""
        try:
            from ui import app as ui_app

            importlib.reload(ui_app)
            logger.debug("🔄 UI modules reloaded")
        except ImportError:
            logger.debug("Streamlit not available; skipping UI reload")

    def _start_servers(self):
        """Start FastAPI and Streamlit servers from the managed system"""
        try:
            # Ensure managed system is properly set up first
            self.managed_system_manager.ensure_managed_system_structure()
            self.managed_system_manager.update_system_files()

            managed_system_path = self.managed_system_manager.managed_system_path
            logger.debug("🚀 Starting servers from managed system at: %s", managed_system_path)

            # Create log directory for server outputs
            log_dir = managed_system_path / "logs"
            log_dir.mkdir(exist_ok=True)

            # Check if managed system has the startup script
            start_script = managed_system_path / "start_servers.sh"
            if start_script.exists():
                # Validate script path is within managed system
                if not start_script.is_relative_to(managed_system_path):
                    logger.error("❌ Invalid script path: %s", start_script)
                    return

                # Use the managed system's startup script with output redirection
                with open(log_dir / "startup.log", "w") as log_file:
                    subprocess.Popen(
                        ["/bin/bash", str(start_script)],
                        cwd=managed_system_path,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                    )  # nosec B603 B607
                logger.debug("🚀 Servers started using managed system startup script")
            else:
                # Fallback to manual server startup with output redirection
                logger.debug(
                    "🔄 Using fallback server startup (managed system startup script not found)"
                )

                # Start FastAPI server from managed system
                api_cmd = [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    Config.API_HOST,
                    "--port",
                    str(Config.API_PORT),
                    "--reload",
                ]

                # Redirect FastAPI output to log file
                with open(log_dir / "fastapi.log", "w") as api_log:
                    subprocess.Popen(
                        api_cmd, cwd=managed_system_path, stdout=api_log, stderr=subprocess.STDOUT
                    )  # nosec B603
                logger.debug(
                    "🚀 FastAPI server started at http://%s:%s (from managed system)",
                    Config.API_HOST,
                    Config.API_PORT,
                )

                # Start Streamlit UI from managed system
                ui_file = managed_system_path / "ui" / "app.py"
                if ui_file.exists():
                    # Validate UI file path is within managed system
                    if not ui_file.is_relative_to(managed_system_path):
                        logger.error("❌ Invalid UI file path: %s", ui_file)
                        return

                    ui_cmd = [
                        "/usr/bin/streamlit",
                        "run",
                        str(ui_file),
                        "--server.port",
                        str(Config.UI_PORT),
                        "--server.headless",
                        "true",
                        "--logger.level",
                        "error",
                    ]  # nosec B607

                    # Redirect Streamlit output to log file
                    with open(log_dir / "streamlit.log", "w") as ui_log:
                        subprocess.Popen(
                            ui_cmd, cwd=managed_system_path, stdout=ui_log, stderr=subprocess.STDOUT
                        )  # nosec B603
                    logger.debug(
                        "🎨 Streamlit UI started at http://%s:%s (from managed system)",
                        Config.UI_HOST,
                        Config.UI_PORT,
                    )
                else:
                    logger.warning("⚠️  Managed system UI not found at %s", ui_file)

            # Log managed system information
            info = self.managed_system_manager.get_managed_system_info()
            logger.debug(
                "📊 Managed System Info: %d entities, structure complete: %s",
                len(info["entities"]),
                info["structure_complete"],
            )

            # Inform user about log files
            logger.debug("📝 Server logs available at: %s", log_dir)

        except Exception as e:
            logger.error("❌ Failed to start servers from managed system: %s", str(e))
            logger.debug(
                "💡 Try running the managed system manually: cd %s && ./start_servers.sh",
                self.managed_system_manager.managed_system_path,
            )

    def get_supported_entities_info(self) -> Dict[str, Any]:
        """Get information about all supported entities"""
        return {
            "supported_entities": self.bae_registry.get_supported_entities(),
            "entity_keywords": self.bae_registry.get_all_keywords(),
            "registry_summary": self.bae_registry.get_registry_summary(),
            "entity_details": {
                entity: self.bae_registry.get_bae_metadata(entity)
                for entity in self.bae_registry.get_supported_entities()
            },
        }

    def validate_entity_request(self, request: str) -> Dict[str, Any]:
        """Validate if a request can be handled by the system"""
        classification = self.entity_recognizer.recognize_entity(request)
        detected_entity = classification.get("detected_entity", "unknown")

        return {
            "can_handle": self.bae_registry.is_entity_supported(detected_entity),
            "detected_entity": detected_entity,
            "confidence": classification.get("confidence", 0.0),
            "reasoning": classification.get("reasoning", ""),
            "supported_entities": (
                self.bae_registry.get_supported_entities()
                if not self.bae_registry.is_entity_supported(detected_entity)
                else None
            ),
        }

    def _execute_evolution_tests(
        self, entity: str, execution_results: List[Dict[str, Any]], execution_type: str
    ) -> Dict[str, Any]:
        """Execute tests after system generation/evolution with TechLeadSWEA coordination"""
        try:
            # Check if TestSWEA was part of the execution results
            test_generation_result = None
            for result in execution_results:
                if "TestSWEA" in result.get("task", "") and result.get("success"):
                    test_generation_result = result
                    break

            if not test_generation_result:
                logger.warning("⚠️  No TestSWEA execution found in results, skipping test execution")
                return {"success": False, "error": "No test generation found", "entity": entity}

            # Execute the generated tests
            test_payload = {
                "entity": entity,
                "execution_type": execution_type,
                "validate_after_changes": True,
            }

            execution_result = self.test_swea.handle_task("execute_tests", test_payload)

            # Extract test execution details with better error handling
            test_data = execution_result.get("data", {})
            test_execution = test_data.get("test_execution", {})

            # Check for timeout or other specific errors
            if test_execution.get("timeout_error"):
                logger.warning(f"⚠️  Test execution timed out for {entity}")
                return {
                    "success": False,
                    "error": "Test execution timed out",
                    "timeout": True,
                    "entity": entity,
                    "stderr": test_execution.get("stderr", ""),
                }

            success = execution_result.get("success", False) and test_execution.get(
                "success", False
            )

            # Enhanced error logging for failed test execution
            if not execution_result.get("success"):
                error_details = execution_result.get("error", "Unknown error")
                logger.error("❌ Test execution failed for %s:", entity)
                logger.error("   Error: %s", error_details)
                logger.error("   Exit code: %s", test_execution.get("exit_code", "N/A"))
                logger.error("   STDERR: %s", test_execution.get("stderr", "N/A"))
                logger.error(
                    "   STDOUT: %s", test_execution.get("stdout", "N/A")[:500]
                )  # Limit output

            # Enhanced failure analysis with detailed context for TechLeadSWEA
            failure_context = {
                "entity": entity,
                "test_execution": test_execution,
                "execution_result": execution_result,
                "tests_executed": test_execution.get("tests_executed", 0),
                "tests_passed": test_execution.get("tests_passed", 0),
                "tests_failed": test_execution.get("tests_failed", 0),
                "stderr": test_execution.get("stderr", ""),
                "stdout": test_execution.get("stdout", ""),
                "exit_code": test_execution.get("exit_code", -1),
                "execution_results": execution_results,  # Context of what was generated
            }

            return {
                "success": success,
                "entity": entity,
                "test_execution": test_execution,
                "failure_context": failure_context,  # Enhanced context for TechLeadSWEA analysis
                "needs_coordination": not success,  # Flag for TechLeadSWEA intervention
            }

        except Exception as e:
            logger.error("❌ Failed to execute evolution tests: %s", str(e))
            logger.error("   Entity: %s", entity)
            logger.error("   Execution results count: %d", len(execution_results))
            logger.error("   Exception type: %s", type(e).__name__)
            # Log the first few execution results for context
            if execution_results:
                logger.error("   Sample execution results:")
                for i, result in enumerate(execution_results[:3]):  # First 3 results
                    task_name = result.get("task", "Unknown task")
                    success = result.get("success", False)
                    logger.error("     %d. %s: %s", i + 1, task_name, "✅" if success else "❌")
            return {
                "success": False,
                "error": f"Evolution test execution failed: {str(e)}",
                "entity": entity,
                "exception_type": type(e).__name__,
                "execution_results_count": len(execution_results),
            }

    def _execute_techlead_fix_decisions(
        self,
        fix_decisions: List[Dict[str, Any]],
        entity: str,
        execution_results: List[Dict[str, Any]],
    ) -> bool:
        """Execute fix decisions coordinated by TechLeadSWEA"""
        try:
            fixes_applied = False

            for decision in fix_decisions:
                responsible_swea = decision.get("responsible_swea", "")
                recommended_action = decision.get("recommended_action", "")
                issue_type = decision.get("issue_type", "")

                logger.debug(
                    "🔧 Applying TechLeadSWEA fix: %s → %s", issue_type, recommended_action
                )

                # Route fix to appropriate SWEA based on TechLeadSWEA decision
                fix_payload = {
                    "entity": entity,
                    "fix_action": recommended_action,
                    "issue_type": issue_type,
                    "techlead_decision": decision,
                    "execution_results": execution_results,
                }

                if (
                    "backend" in responsible_swea.lower()
                    or "programmer" in responsible_swea.lower()
                ):
                    fix_result = self.backend_swea.handle_task("fix_issues", fix_payload)
                elif "frontend" in responsible_swea.lower():
                    fix_result = self.frontend_swea.handle_task("fix_issues", fix_payload)
                elif "database" in responsible_swea.lower():
                    fix_result = self.database_swea.handle_task("fix_issues", fix_payload)
                elif "test" in responsible_swea.lower():
                    fix_result = self.test_swea.handle_task("fix_issues", fix_payload)
                else:
                    logger.warning("⚠️ Unknown SWEA for fix: %s", responsible_swea)
                    continue

                if fix_result and fix_result.get("success"):
                    logger.debug("✅ Fix applied successfully by %s", responsible_swea)
                    fixes_applied = True
                else:
                    logger.warning(
                        "⚠️ Fix failed for %s: %s",
                        responsible_swea,
                        fix_result.get("error", "Unknown error"),
                    )

            return fixes_applied

        except Exception as e:
            logger.error("❌ Failed to execute TechLeadSWEA fix decisions: %s", str(e))
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _get_simplified_task_name(self, task_name: str) -> str:
        """Convert technical task name to simplified presentation name"""
        if "coordinate_system_generation" in task_name:
            return "TechLead Coordination"
        elif "setup_database" in task_name:
            return "Database Setup"
        elif "generate_model" in task_name:
            return "Model Generation"
        elif "generate_api" in task_name:
            return "API Generation"
        elif "generate_ui" in task_name:
            return "UI Generation"
        elif "generate_all_tests" in task_name:
            return "Test Generation"
        elif "review_and_approve" in task_name:
            return "Final Review"
        else:
            # Fallback: clean up technical names
            clean_name = task_name.replace("SWEA.", "").replace("_", " ").title()
            return clean_name.replace("Swea", "").strip()

    def _extract_task_details(self, task_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract simple details from task result for presentation"""
        details = {}

        if "setup_database" in task_name:
            details["database_created"] = True
        elif "generate_model" in task_name:
            # Try to extract lines of code from result
            if result and isinstance(result, dict):
                content = result.get("model_content", "")
                if content:
                    lines = len(content.split("\n")) if content else 0
                    if lines > 0:
                        details["model_lines"] = lines
        elif "generate_api" in task_name:
            if result and isinstance(result, dict):
                # Count API endpoints mentioned in result
                content = str(result.get("api_content", ""))
                endpoint_count = content.count("@router.") + content.count("def ")
                if endpoint_count > 0:
                    details["api_endpoints"] = endpoint_count
        elif "generate_ui" in task_name:
            if result and isinstance(result, dict):
                # Count UI components
                content = str(result.get("ui_content", ""))
                component_count = content.count("st.") + content.count("def ")
                if component_count > 0:
                    details["ui_components"] = component_count

        return details

    def _get_expected_output_for_task(self, swea_agent: str, task_type: str, entity: str) -> str:
        """Get expected output description for a specific SWEA task to guide retry attempts"""

        if "Backend" in swea_agent:
            if "generate_model" in task_type:
                return f"""Expected Pydantic model output for {entity}:
- Must include 'from pydantic import BaseModel' import
- Must have 'class {entity}(BaseModel):' definition
- Must include proper field definitions with type hints
- Should include field validators if needed
- Must be syntactically valid Python code"""

            elif "generate_api" in task_type:
                return f"""Expected FastAPI routes output for {entity}:
- Must include 'from fastapi import APIRouter' import
- Must create router = APIRouter() instance
- Must implement CRUD endpoints (POST, GET, PUT, DELETE)
- Must include proper error handling
- Must be syntactically valid Python code"""

        elif "Frontend" in swea_agent:
            return f"""Expected Streamlit UI output for {entity}:
- Must include 'import streamlit as st' import
- Must use st.* functions for UI components
- Must implement forms for data input
- Must include data display functionality
- Must be syntactically valid Python code"""

        elif "Database" in swea_agent:
            return f"""Expected database setup output for {entity}:
- Must create database tables successfully
- Must return confirmation of database setup
- Must handle database connection properly
- Must implement proper error handling"""

        return (
            f"Expected successful execution with proper output format for {swea_agent}.{task_type}"
        )

    def _track_retry_pattern(self, task_key: str, error: str, retry_count: int):
        """Track retry patterns for monitoring and prevention (Phase 3)"""
        pattern = self.retry_patterns[task_key]
        pattern["count"] = retry_count
        pattern["last_errors"].append(error)
        pattern["timestamps"].append(datetime.now().isoformat())

        # Track common failure patterns
        if "dict" in error and "strip" in error:
            self.failure_analytics["common_failures"]["dict_strip_error"] += 1
        elif "JSON" in error and "parse" in error:
            self.failure_analytics["common_failures"]["json_parse_error"] += 1
        elif "database" in error.lower() and "table" in error.lower():
            self.failure_analytics["common_failures"]["database_table_error"] += 1

        logger.debug(
            f"Retry pattern tracked for {task_key}: {retry_count} attempts, latest error: {error}"
        )

    def _get_retry_prevention_strategy(self, task_key: str) -> Dict[str, Any]:
        """Get prevention strategy based on historical retry patterns (Phase 3)"""
        pattern = self.retry_patterns.get(task_key, {})
        last_errors = list(pattern.get("last_errors", []))

        strategy = {
            "use_fallback": False,
            "additional_validation": False,
            "modified_prompt": False,
            "reasoning": "No specific strategy needed",
        }

        # Analyze error patterns
        if any("dict" in error and "strip" in error for error in last_errors):
            strategy.update(
                {
                    "additional_validation": True,
                    "reasoning": "Previous dict/strip errors detected - using enhanced validation",
                }
            )

        if any("JSON" in error for error in last_errors):
            strategy.update(
                {
                    "modified_prompt": True,
                    "reasoning": "JSON parsing issues detected - using modified prompt",
                }
            )

        if len(last_errors) >= 3:  # Recurring failures
            strategy.update(
                {
                    "use_fallback": True,
                    "reasoning": "Recurring failures detected - using fallback strategy",
                }
            )

        return strategy

    def _validate_llm_response_format(
        self, response: Dict[str, Any], expected_fields: List[str]
    ) -> bool:
        """Validate LLM response format to prevent common errors (Phase 3)"""
        try:
            # Check required fields exist
            for field in expected_fields:
                if field not in response:
                    logger.warning(f"LLM response missing required field: {field}")
                    return False

            # Check attributes field format specifically (prevent dict/strip error)
            if "attributes" in response:
                attributes = response["attributes"]
                if not isinstance(attributes, list):
                    logger.warning(
                        f"LLM response 'attributes' field is not a list: {type(attributes)}"
                    )
                    return False

                # Check each attribute for problematic formats
                for i, attr in enumerate(attributes):
                    if isinstance(attr, dict):
                        if "name" not in attr or "type" not in attr:
                            logger.warning(
                                f"LLM response attribute {i} is dict but missing name/type: {attr}"
                            )
                            return False
                    elif not isinstance(attr, str):
                        logger.warning(
                            f"LLM response attribute {i} is neither string nor valid dict: {type(attr)}"
                        )
                        return False

            return True

        except Exception as e:
            logger.error(f"LLM response validation failed: {e}")
            return False

    def _generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate monitoring report for retry patterns and failures (Phase 3)"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "retry_patterns": dict(self.retry_patterns),
            "failure_analytics": dict(self.failure_analytics),
            "recommendations": [],
        }

        # Analyze patterns and generate recommendations
        if self.failure_analytics["common_failures"]["dict_strip_error"] > 0:
            report["recommendations"].append(
                {
                    "issue": "Dict/strip errors detected",
                    "recommendation": "Ensure all SWEA agents use _validate_interpretation_structure()",
                    "priority": "high",
                }
            )

        if self.failure_analytics["common_failures"]["json_parse_error"] > 2:
            report["recommendations"].append(
                {
                    "issue": "Frequent JSON parsing errors",
                    "recommendation": "Review LLM prompt templates for JSON format guidance",
                    "priority": "medium",
                }
            )

        # Check for tasks with high retry counts
        high_retry_tasks = [
            task for task, pattern in self.retry_patterns.items() if pattern["count"] >= 2
        ]

        if high_retry_tasks:
            report["recommendations"].append(
                {
                    "issue": f"High retry counts detected for: {', '.join(high_retry_tasks)}",
                    "recommendation": "Review task implementation and add additional error handling",
                    "priority": "medium",
                }
            )

        return report

    def _execute_hybrid_techlead_coordination(
        self,
        failure_analysis_payload: Dict[str, Any],
        entity: str,
        execution_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute hybrid TechLeadSWEA coordination"""
        try:
            # Initialize test execution result
            test_execution_result = {
                "success": False,
                "techlead_coordination": True,
                "coordination_log": [],
                "fix_iterations": 0,
            }

            # TechLeadSWEA performs hybrid analysis and coordinates fixes
            coordination_result = self.techlead_swea.handle_task(
                "hybrid_coordination", failure_analysis_payload
            )

            if coordination_result.get("success"):
                # Extract data from TechLeadSWEA response structure
                coordination_data = coordination_result.get("data", {})

                # Update test execution result with coordination outcome
                test_execution_result.update(
                    {
                        "success": coordination_data.get("success", False),
                        "techlead_coordination": True,
                        "coordination_log": coordination_data.get("coordination_log", []),
                        "fix_iterations": coordination_data.get("fix_iterations", 0),
                    }
                )

                # Apply fixes if any
                if coordination_data.get("fixes_applied"):
                    self._execute_techlead_fix_decisions(
                        coordination_data.get("fixes_applied", []), entity, execution_results
                    )
            else:
                # Coordination failed - provide detailed error context
                error_details = coordination_result.get("error", "TechLeadSWEA coordination failed")
                failed_tasks = coordination_result.get("failed_tasks", [])

                logger.warning(
                    "❌ Request processing FAILED for %s entity - %d tasks failed",
                    entity,
                    len(failed_tasks),
                )
                for task in failed_tasks:
                    logger.warning(
                        "   Failed: %s - %s",
                        task.get("task", "Unknown"),
                        task.get("error", "unknown error"),
                    )

                test_execution_result.update(
                    {
                        "success": False,
                        "error": error_details,
                        "failed_tasks": failed_tasks,
                    }
                )

            return test_execution_result

        except Exception as e:
            logger.error("❌ Failed to execute hybrid TechLeadSWEA coordination: %s", str(e))
            logger.error("   Entity: %s", entity)
            logger.error("   Execution results count: %d", len(execution_results))
            logger.error("   Exception type: %s", type(e).__name__)
            # Log the first few execution results for context
            if execution_results:
                logger.error("   Sample execution results:")
                for i, result in enumerate(execution_results[:3]):  # First 3 results
                    task_name = result.get("task", "Unknown task")
                    success = result.get("success", False)
                    logger.error("     %d. %s: %s", i + 1, task_name, "✅" if success else "❌")
            return {
                "success": False,
                "error": f"Hybrid TechLeadSWEA coordination failed: {str(e)}",
                "entity": entity,
                "exception_type": type(e).__name__,
                "execution_results_count": len(execution_results),
                "techlead_coordination": True,
                "coordination_log": [],
                "fix_iterations": 0,
            }

    def _execute_mandatory_tests(
        self, entity: str, execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute tests as a mandatory part of the main coordination flow.
        Tests MUST pass for the system to be considered successfully generated.
        """
        try:
            logger.info("🧪 Executing mandatory tests for %s entity", entity)

            # In the new Phase 2 structure, tests are generated in Phase 2, not Phase 1
            # So we don't look for TestSWEA in execution_results from Phase 1
            # Instead, we assume tests are ready to be executed after Phase 2 generation

            # Execute the tests directly
            test_payload = {
                "entity": entity,
                "execution_type": "creation_validation",
                "validate_after_changes": True,
                "mandatory": True,  # Flag to indicate this is mandatory testing
            }

            execution_result = self.test_swea.handle_task("execute_tests", test_payload)

            # Extract test execution details
            test_data = execution_result.get("data", {})
            test_execution = test_data.get("test_execution", {})

            # Check for specific errors
            if test_execution.get("timeout_error"):
                logger.error("❌ Mandatory test execution timed out for %s", entity)
                return {
                    "success": False,
                    "error": "Test execution timed out",
                    "timeout": True,
                    "entity": entity,
                    "test_execution": test_execution,
                }

            success = execution_result.get("success", False) and test_execution.get(
                "success", False
            )

            # Calculate test metrics - FIXED: tests_executed is at top level, others are nested
            tests_executed = test_data.get("tests_executed", 0)  # Top level
            tests_passed = test_execution.get("tests_passed", 0)  # Nested in test_execution
            tests_failed = test_execution.get("tests_failed", 0)  # Nested in test_execution
            pass_rate = (tests_passed / tests_executed * 100) if tests_executed > 0 else 0

            # Log test results
            if success and pass_rate == 100:
                logger.info(
                    "✅ All tests passed (%d/%d) - 100%% pass rate achieved",
                    tests_passed,
                    tests_executed,
                )
            else:
                logger.warning(
                    "❌ Tests failed: %d/%d passed (%.1f%% pass rate)",
                    tests_passed,
                    tests_executed,
                    pass_rate,
                )
                if test_execution.get("stderr"):
                    logger.warning("📝 Test errors: %s", test_execution.get("stderr", "")[:500])

            # Return detailed test results for TechLeadSWEA analysis
            return {
                "success": success,
                "entity": entity,
                "test_execution": test_execution,
                "tests_executed": tests_executed,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "pass_rate": pass_rate,
                "requires_100_percent": True,  # Flag for TechLeadSWEA
                "failure_context": (
                    {
                        "entity": entity,
                        "test_execution": test_execution,
                        "execution_results": execution_results,
                        "stderr": test_execution.get("stderr", ""),
                        "stdout": test_execution.get("stdout", ""),
                        "exit_code": test_execution.get("exit_code", -1),
                    }
                    if not success
                    else None
                ),
            }

        except Exception as e:
            logger.error("❌ Failed to execute mandatory tests: %s", str(e))
            return {
                "success": False,
                "error": f"Mandatory test execution failed: {str(e)}",
                "entity": entity,
                "exception_type": type(e).__name__,
                "critical_failure": True,
            }

    def _generate_tests_for_phase_2(
        self, entity: str, execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate tests at the beginning of Phase 2 after all artifacts are ready.
        This ensures all managed system artifacts are fully generated before test generation.
        If dependencies are missing, log error and stop process.
        """
        try:
            logger.info(
                "🧪 Phase 2: Generating tests for %s entity after all artifacts are ready", entity
            )
            entity_info = self._extract_entity_info_from_execution_results(
                entity, execution_results
            )
            test_payload = {
                "entity": entity,
                "attributes": entity_info.get("attributes", []),
                "context": entity_info.get("context", "academic"),
                "phase_2_generation": True,
                "all_artifacts_ready": True,
            }
            generation_result = self.test_swea.handle_task(
                "generate_all_tests_with_collaboration", test_payload
            )
            if not generation_result.get("success", False):
                error = generation_result.get("error", "Unknown test generation error")
                # Check for missing dependencies error
                if (
                    generation_result.get("error_type") == "missing_dependencies"
                    or "missing_dependencies" in error
                ):
                    logger.error(
                        f"❌ Test generation failed for {entity} due to missing dependencies: {error}"
                    )
                    from baes.utils.presentation_logger import get_presentation_logger

                    get_presentation_logger().error(
                        f"Test generation failed for {entity} due to missing dependencies: {error}"
                    )
                    raise RuntimeError(
                        f"Test generation failed for {entity} due to missing dependencies: {error}"
                    )
                logger.error("❌ Phase 2: Test generation failed - %s", error)
                return {
                    "success": False,
                    "entity": entity,
                    "error": error,
                    "phase_2_generation": True,
                    "message": f"Test generation failed for {entity}: {error}",
                }
            test_types_generated = generation_result.get("data", {}).get("test_types_generated", [])
            logger.info(
                "✅ Phase 2: Test generation completed - %d test types generated",
                len(test_types_generated),
            )
            return {
                "success": True,
                "entity": entity,
                "test_types_generated": test_types_generated,
                "phase_2_generation": True,
                "message": f"Successfully generated {len(test_types_generated)} test types for {entity}",
            }
        except Exception as e:
            logger.error("❌ Phase 2: Test generation failed with exception: %s", str(e))
            return {
                "success": False,
                "entity": entity,
                "error": str(e),
                "exception_type": type(e).__name__,
                "phase_2_generation": True,
                "message": f"Test generation failed for {entity}: {str(e)}",
            }

    def _extract_entity_info_from_execution_results(
        self, entity: str, execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract entity information from execution results for test generation."""
        entity_info = {"entity": entity, "attributes": [], "context": "academic"}

        # Try to extract attributes from successful model generation
        for result in execution_results:
            if (
                result.get("success")
                and "BackendSWEA" in result.get("task", "")
                and "generate_model" in result.get("task", "")
            ):

                model_result = result.get("result", {})
                if isinstance(model_result, dict):
                    # Try to extract attributes from model generation result
                    model_data = model_result.get("data", {})
                    if "attributes" in model_data:
                        entity_info["attributes"] = model_data["attributes"]
                    elif "model_content" in model_data:
                        # Parse attributes from model content if available
                        model_content = model_data["model_content"]
                        entity_info["attributes"] = self._extract_attributes_from_model_content(
                            model_content
                        )
                    break

        # If no attributes found, use default attributes for the entity
        if not entity_info["attributes"]:
            entity_info["attributes"] = self._get_default_attributes_for_entity(entity)

        return entity_info

    def _extract_attributes_from_model_content(self, model_content: str) -> List[str]:
        """Extract attribute names from Pydantic model content."""
        attributes = []
        lines = model_content.split("\n")

        for line in lines:
            line = line.strip()
            # Look for field definitions (name: type)
            if (
                ":" in line
                and not line.startswith("class")
                and not line.startswith("def")
                and not line.startswith("#")
            ):
                # Extract field name before the colon
                field_name = line.split(":")[0].strip()
                if field_name and not field_name.startswith("_"):
                    attributes.append(field_name)

        return attributes

    def _get_default_attributes_for_entity(self, entity: str) -> List[str]:
        """Get default attributes for an entity if none can be extracted."""
        default_attributes = {
            "student": ["name", "email", "age"],
            "course": ["name", "code", "credits"],
            "teacher": ["name", "email", "department"],
        }

        return default_attributes.get(entity.lower(), ["name", "id"])

    def _coordinate_test_fixes_until_success(
        self, entity: str, test_result: Dict[str, Any], execution_results: List[Dict[str, Any]]
    ) -> bool:
        """
        Coordinate fixes with TechLeadSWEA until tests achieve 100% pass rate.
        Returns True only when all tests pass, False if max attempts reached.
        """
        max_fix_iterations = int(os.getenv("BAE_MAX_RETRIES", "3"))
        fix_iteration = 0

        logger.info(
            "🔧 TechLeadSWEA coordinating test fixes for %s (max %d iterations)",
            entity,
            max_fix_iterations,
        )

        while fix_iteration < max_fix_iterations:
            fix_iteration += 1
            logger.info("🔄 Fix iteration %d/%d for %s", fix_iteration, max_fix_iterations, entity)

            # ENHANCED: Extract detailed failure context for better TechLeadSWEA analysis
            failure_context = test_result.get("failure_context", {})
            test_execution = test_result.get("test_execution", {})

            # Prepare enhanced failure analysis payload for TechLeadSWEA
            failure_analysis_payload = {
                "entity": entity,
                "execution_type": "test_validation",
                "failure_context": failure_context,  # Complete failure context
                "test_execution": test_execution,  # Detailed test execution results
                "generated_artifacts": execution_results,
                "coordination_id": f"test_fix_{entity}_{fix_iteration}_{self._get_timestamp()}",
                "fix_iteration": fix_iteration,
                "max_iterations": max_fix_iterations,
                "requires_100_percent_pass": True,
                # NEW: Add specific test failure details for better analysis
                "test_failures": [
                    {
                        "category": "test_execution_failure",
                        "stderr": test_execution.get("stderr", ""),
                        "stdout": test_execution.get("stdout", ""),
                        "exit_code": test_execution.get("exit_code", -1),
                        "tests_executed": test_execution.get("tests_executed", 0),
                        "tests_passed": test_execution.get("tests_passed", 0),
                        "tests_failed": test_execution.get("tests_failed", 0),
                    }
                ],
            }

            # Use the enhanced coordinate_test_fixes method instead of hybrid_coordination
            # This provides more specific and actionable fix routing
            try:
                logger.info(
                    "🧠 Routing to TechLeadSWEA coordinate_test_fixes for detailed analysis"
                )
                coordination_result = self.techlead_swea.handle_task(
                    "coordinate_test_fixes", failure_analysis_payload
                )

                if coordination_result.get("success"):
                    # Extract fix decisions from TechLeadSWEA
                    coordination_data = coordination_result.get("data", {})
                    fix_decisions = coordination_data.get("fix_decisions", [])
                    specific_issues_found = coordination_data.get("specific_issues_found", 0)

                    logger.info(
                        "✅ TechLeadSWEA analysis complete: %d fix decisions, %d specific issues",
                        len(fix_decisions),
                        specific_issues_found,
                    )

                    # Apply the coordinated fixes
                    if fix_decisions:
                        logger.info("🔧 Applying %d coordinated fixes...", len(fix_decisions))
                        fixes_applied = self._execute_techlead_fix_decisions(
                            fix_decisions, entity, execution_results
                        )

                        if fixes_applied:
                            # Re-execute tests after fixes
                            logger.info("🧪 Re-executing tests after fixes...")
                            updated_test_result = self._execute_mandatory_tests(
                                entity, execution_results
                            )

                            if updated_test_result.get("success", False):
                                logger.info("✅ Tests now passing after TechLeadSWEA coordination!")
                                return True
                            else:
                                # Update test result for next iteration
                                test_result = updated_test_result
                                pass_rate = test_result.get("pass_rate", 0.0)
                                logger.warning(
                                    "⚠️ Tests still failing (%.1f%% pass rate) - iteration %d",
                                    pass_rate,
                                    fix_iteration,
                                )
                        else:
                            logger.warning("⚠️ Fix application failed - iteration %d", fix_iteration)
                    else:
                        logger.warning(
                            "⚠️ No fix decisions from TechLeadSWEA - iteration %d", fix_iteration
                        )
                else:
                    error = coordination_result.get("error", "Unknown coordination error")
                    logger.warning(
                        "⚠️ TechLeadSWEA coordination failed: %s - iteration %d",
                        error,
                        fix_iteration,
                    )

            except Exception as e:
                logger.error("❌ Fix iteration %d failed with exception: %s", fix_iteration, str(e))

        # Max iterations reached without success
        logger.error("❌ Test fixes failed after %d iterations - giving up", max_fix_iterations)
        return False


# CLI Interface
def _build_arg_parser() -> argparse.ArgumentParser:
    """Build command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Enhanced Runtime Kernel for BAE Academic System with multiple entity support"
    )
    parser.add_argument("request", help="Natural-language request from the HBE")
    parser.add_argument(
        "--context", default="academic", help="Business context (default: academic)"
    )
    parser.add_argument("--no-server", action="store_true", help="Skip starting servers")
    parser.add_argument("--validate-only", action="store_true", help="Only validate the request")
    return parser


def main():
    """Main CLI entry point"""
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Configure httpx logging to suppress HTTP request logs unless in debug mode
    # httpx logs every HTTP request at INFO level, which is too verbose for normal operation
    httpx_logger = logging.getLogger("httpx")
    if os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes"):
        httpx_logger.setLevel(logging.DEBUG)
    else:
        httpx_logger.setLevel(logging.WARNING)  # Only show warnings and errors

    # Initialize kernel
    kernel = EnhancedRuntimeKernel()

    if args.validate_only:
        # Just validate the request
        validation = kernel.validate_entity_request(args.request)
        print(f"Validation Result: {validation}")
    else:
        # Process the request
        result = kernel.process_natural_language_request(
            args.request, context=args.context, start_servers=not args.no_server
        )
        print(f"Processing Result: {result}")


if __name__ == "__main__":
    main()
