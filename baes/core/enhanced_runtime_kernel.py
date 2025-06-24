import argparse
import importlib
import logging
import os
import subprocess  # nosec B404
import sys
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
from config import Config

load_dotenv()


logger = logging.getLogger(__name__)


class UnknownSWEAAgentError(Exception):
    """Raised when an unknown SWEA agent is requested in coordination plan"""

    def __init__(self, agent_name: str, available_agents: List[str]):
        self.agent_name = agent_name
        self.available_agents = available_agents
        super().__init__(
            f"Unknown SWEA agent '{agent_name}'. Available agents: {', '.join(available_agents)}"
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

        logger.info(
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
        logger.info("📥 Processing request: %s", request)

        # Step 1: Entity Recognition using OpenAI
        entity_classification = self.entity_recognizer.recognize_entity(request)
        detected_entity = entity_classification.get("detected_entity", "unknown")
        confidence = entity_classification.get("confidence", 0.0)

        logger.info("🔍 Entity detection: %s (confidence: %.2f)", detected_entity, confidence)

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
            logger.info("⚙️  Executing coordination plan with %d tasks", len(coordination_plan))
            try:
                execution_results = self._execute_coordination_plan(
                    coordination_plan, target_bae, context
                )
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

        # Step 7: Execute generated tests after any successful generation/modification to validate changes
        if interpretation_result and execution_results:
            # Determine execution type for appropriate test validation
            is_evolution = interpretation_result.get("is_evolution", False)
            execution_type = "evolution_validation" if is_evolution else "creation_validation"

            test_execution_result = self._execute_evolution_tests(
                detected_entity, execution_results
            )
            execution_results.append(
                {
                    "task": f"TestSWEA.execute_{execution_type}_tests",
                    "success": test_execution_result.get("success", False),
                    "result": test_execution_result,
                    "entity": detected_entity,
                }
            )
            if test_execution_result.get("success"):
                action = "evolution" if is_evolution else "creation"
                logger.info(
                    "✅ %s tests executed successfully for %s", action.capitalize(), detected_entity
                )
            else:
                action = "evolution" if is_evolution else "creation"
                logger.warning(
                    "⚠️  %s tests failed for %s: %s",
                    action.capitalize(),
                    detected_entity,
                    test_execution_result.get("error", "Unknown error"),
                )

        # Step 8: Preserve domain knowledge
        self._preserve_domain_knowledge(detected_entity, interpretation_result, context)

        # Step 9: Reload and start servers if requested
        if start_servers and not os.getenv("SKIP_SERVER_START"):
            self._reload_system_components()
            self._start_servers()

        # Step 10: Return comprehensive result
        result = {
            "success": True,
            "entity": detected_entity,
            "confidence": confidence,
            "bae_used": target_bae.name,
            "interpretation": interpretation_result,
            "execution_results": execution_results,
            "language_detected": entity_classification.get("language_detected"),
            "action_intent": entity_classification.get("action_intent"),
            "domain_knowledge_preserved": True,
        }

        logger.info("✅ Request processed successfully for %s entity", detected_entity)
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
        """Execute SWEA coordination plan orchestrated by BAE"""
        results = []

        for task in coordination_plan:
            swea_agent = task.get("swea_agent", "")
            task_type = task.get("task_type", "")
            entity = task.get("entity", coordinating_bae.entity_name)

            logger.info("⚙️  Executing %s.%s for %s entity", swea_agent, task_type, entity)

            # Route to appropriate SWEA agent
            swea_agent_lower = swea_agent.lower()
            if swea_agent_lower in [
                "backend",
                "backendswea",
                "backend_swea",
            ]:
                agent = self.backend_swea
            elif swea_agent_lower in ["frontend", "frontendswea", "frontend_swea"]:
                agent = self.frontend_swea
            elif swea_agent_lower in ["database", "databaseswea", "database_swea"]:
                agent = self.database_swea
            elif swea_agent_lower in ["test", "testswea", "test_swea"]:
                agent = self.test_swea
                # For collaborative testing, use the enhanced task
                if task_type == "generate_all_tests":
                    task_type = "generate_all_tests_with_collaboration"
            elif swea_agent_lower in [
                "techlead",
                "techleadswea",
                "techlead_swea",
                "technical_lead",
            ]:
                agent = self.techlead_swea
            else:
                available_agents = [
                    "BackendSWEA",
                    "FrontendSWEA",
                    "DatabaseSWEA",
                    "TestSWEA",
                    "TechLeadSWEA",
                ]
                logger.error("❌ Unknown SWEA agent: %s", swea_agent)
                raise UnknownSWEAAgentError(swea_agent, available_agents)

            # Execute task with proper payload
            task_payload = task.get("payload", {})
            task_payload.update(
                {"entity": entity, "context": context, "coordinating_bae": coordinating_bae.name}
            )

            try:
                result = agent.handle_task(task_type, task_payload)
                results.append(
                    {
                        "task": f"{swea_agent}.{task_type}",
                        "success": True,
                        "result": result,
                        "entity": entity,
                    }
                )
                logger.info("✅ Task %s.%s completed successfully", swea_agent, task_type)
            except Exception as e:
                error_msg = f"SWEA task execution failed: {str(e)}"
                logger.error("❌ %s", error_msg)
                results.append(
                    {
                        "task": f"{swea_agent}.{task_type}",
                        "success": False,
                        "error": error_msg,
                        "entity": entity,
                    }
                )

        return results

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
            logger.info("🔄 System components reloaded")
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
            logger.info("🚀 Starting servers from managed system at: %s", managed_system_path)

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
                logger.info("🚀 Servers started using managed system startup script")
            else:
                # Fallback to manual server startup with output redirection
                logger.info(
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
                logger.info(
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
                    logger.info(
                        "🎨 Streamlit UI started at http://%s:%s (from managed system)",
                        Config.UI_HOST,
                        Config.UI_PORT,
                    )
                else:
                    logger.warning("⚠️  Managed system UI not found at %s", ui_file)

            # Log managed system information
            info = self.managed_system_manager.get_managed_system_info()
            logger.info(
                "📊 Managed System Info: %d entities, structure complete: %s",
                len(info["entities"]),
                info["structure_complete"],
            )

            # Inform user about log files
            logger.info("📝 Server logs available at: %s", log_dir)

        except Exception as e:
            logger.error("❌ Failed to start servers from managed system: %s", str(e))
            logger.info(
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
        self, entity: str, execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute tests after system generation/evolution to validate changes work correctly"""
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
                "execution_type": "evolution_validation",
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

            result = {
                "success": success,
                "tests_executed": test_data.get("tests_executed", 0),
                "tests_passed": test_execution.get("tests_passed", 0),
                "tests_failed": test_execution.get("tests_failed", 0),
                "execution_time": test_execution.get("execution_time", 0),
                "entity": entity,
                "evolution_validation": True,
            }

            if not success:
                result["error"] = test_execution.get("stderr", "Test execution failed")
                result["stdout"] = test_execution.get("stdout", "")

            return result

        except Exception as e:
            logger.error("❌ Failed to execute evolution tests: %s", str(e))
            return {
                "success": False,
                "error": f"Evolution test execution failed: {str(e)}",
                "entity": entity,
            }

    def _get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().isoformat()


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
