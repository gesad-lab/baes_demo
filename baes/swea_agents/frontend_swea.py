from ..agents.base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient
from ..core.managed_system_manager import ManagedSystemManager
from typing import Dict, Any, List
import os

class FrontendSWEA(BaseAgent):
    """SWEA responsible for generating Streamlit UI code for domain entities."""

    def __init__(self):
        super().__init__("FrontendSWEA", "UI Generation Agent", "SWEA")
        self.llm_client = OpenAIClient()
        self.managed_system_manager = ManagedSystemManager()

    _SUPPORTED_TASKS = {
        "generate_ui": "_generate_ui"
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                f"Unknown task. Supported tasks: {list(self._SUPPORTED_TASKS.keys())}",
                "invalid_task"
            )
        method = getattr(self, self._SUPPORTED_TASKS[task])
        try:
            return method(payload)
        except Exception as e:
            return self.create_error_response(task, str(e), "execution_error")

    # ------------------------------------------------------------------
    def _build_prompt(self, entity: str, attributes: List[str], context: str) -> str:
        template_path = os.path.join("llm", "prompts", "frontend_gen.txt")
        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            template = (
                "You are a SWEA Frontend agent. Generate a Streamlit UI for managing {entity} data. "
                "Attributes: {attributes}. Use proper widgets, call the FastAPI backend at /{entity_lower}s. "
                "Return ONLY the code."
            )
        return template.format(
            entity=entity,
            entity_lower=entity.lower(),
            attributes=", ".join(attributes),
            context=context
        )

    def _write_to_managed_system(self, entity: str, code: str) -> str:
        """Write UI code to the managed system instead of the legacy generated directory."""
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()
        
        # Write the UI artifact to managed system
        file_path = self.managed_system_manager.write_entity_artifact(entity, "ui", code)
        
        # Update main system files to include new entity
        self.managed_system_manager.update_system_files()
        
        return file_path

    def _generate_ui(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        prompt = self._build_prompt(entity, attributes, context)
        code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="Streamlit UI",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "business_rules": payload.get("business_rules", [])
            },
        )

        file_path = self._write_to_managed_system(entity, code)
        return self.create_success_response("generate_ui", {"file_path": file_path, "code": code, "managed_system": True}) 