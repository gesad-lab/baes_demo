from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from typing import Dict, Any, List
import os

class ProgrammerSWEA(BaseAgent):
    """Software Engineering Autonomous Agent responsible for generating backend code (Pydantic model and FastAPI routes) while preserving domain semantics."""

    def __init__(self):
        super().__init__("ProgrammerSWEA", "Code Generation Agent", "SWEA")
        self.llm_client = OpenAIClient()

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "generate_model": "_generate_model",
        "generate_api": "_generate_api"
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch task to internal generator methods."""
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
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_prompt(self, entity: str, attributes: List[str], code_type: str, context: str) -> str:
        """Load prompt template and format it with runtime values."""
        template_path = os.path.join("llm", "prompts", "backend_gen.txt")
        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            # Fallback prompt if template missing
            template = (
                "You are a SWEA Programmer agent. Generate clean, production-ready Python code for {code_type} "
                "representing the {entity} domain entity. Attributes: {attributes}. "
                "Use business vocabulary and FastAPI/Pydantic best practices. Return ONLY code."
            )
        return template.format(
            entity=entity,
            attributes=", ".join(attributes),
            code_type=code_type,
            context=context
        )

    def _write_file(self, rel_path: str, code: str):
        """Ensure directory exists and write code string to file."""
        abs_path = os.path.join("bae_academic_system", rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(code)
        return abs_path

    # -------------------- task implementations ------------------------
    def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        prompt = self._build_prompt(entity, attributes, "Pydantic Model", context)
        code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="Pydantic Model",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "business_rules": payload.get("business_rules", [])
            },
        )

        file_path = self._write_file(f"generated/models/{entity.lower()}_model.py", code)
        return self.create_success_response(
            "generate_model",
            {"file_path": file_path, "code": code}
        )

    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        prompt = self._build_prompt(entity, attributes, "FastAPI Routes", context)
        code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="FastAPI Routes",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "business_rules": payload.get("business_rules", [])
            },
        )

        file_path = self._write_file(f"generated/routes/{entity.lower()}_routes.py", code)
        return self.create_success_response(
            "generate_api",
            {"file_path": file_path, "code": code}
        ) 