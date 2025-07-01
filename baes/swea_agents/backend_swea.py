import logging
import os
from typing import Any, Dict, List
from baes.agents.base_agent import BaseAgent
from baes.llm.openai_client import OpenAIClient
from pathlib import Path

logger = logging.getLogger(__name__)

class BackendSWEA(BaseAgent):
    """
    SWEA responsible for backend (model and API) code generation for domain entities.
    Strictly no fallback strategies: all errors are raised and surfaced.
    """
    _SUPPORTED_TASKS = {
        "generate_model": "_generate_model",
        "generate_api": "_generate_api",
    }

    def __init__(self):
        super().__init__("BackendSWEA", "Backend Generation Agent", "SWEA")
        self.llm_client = OpenAIClient()

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.error(f"BackendSWEA error in {task}: {e}")
            return self.create_error_response(task, str(e), "generation_error")

    def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Model generation is now a no-op: models are defined in the route file
        return self.create_success_response(
            "generate_model",
            {"file_path": None, "code": None, "entity": payload.get("entity", "Student"), "attributes": payload.get("attributes", [])},
        )

    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")
        techlead_feedback = payload.get("techlead_feedback", [])
        previous_errors = payload.get("previous_errors", [])
        retry_count = payload.get("retry_count", 0)
        prompt = self._build_api_prompt(entity, attributes, context, techlead_feedback, previous_errors, retry_count)
        code = self.llm_client.generate_code_with_domain_focus(
            prompt, code_type="FastAPI Routes", entity_context={"entity": entity, "attributes": attributes}
        )
        if not code or not isinstance(code, str):
            raise RuntimeError(f"LLM did not return valid API code for {entity}.")
        file_path = self._write_to_managed_system(entity, code, "api")
        return self.create_success_response(
            "generate_api",
            {"file_path": file_path, "code": code, "entity": entity, "attributes": attributes},
        )

    def _build_model_prompt(self, entity: str, attributes: List[str], context: str, 
                           techlead_feedback: List[str] = None, previous_errors: List[str] = None, 
                           retry_count: int = 0) -> str:
        feedback_section = ""
        if techlead_feedback or previous_errors:
            feedback_section = "\n\nCRITICAL FEEDBACK TO INCORPORATE:\n"
            if techlead_feedback:
                feedback_section += "TechLeadSWEA feedback:\n"
                for feedback in techlead_feedback:
                    feedback_section += f"- {feedback}\n"
            if previous_errors:
                feedback_section += "Previous errors to fix:\n"
                for error in previous_errors:
                    feedback_section += f"- {error}\n"
            feedback_section += "\nIMPORTANT: Address ALL feedback above in your response.\n"
        
        retry_info = ""
        if retry_count > 0:
            retry_info = f"\nThis is retry attempt #{retry_count}. Please ensure you address the feedback above."
        
        return f"""
Generate a Pydantic model for the {entity} entity with the following attributes:
{attributes}
Context: {context}{feedback_section}{retry_info}

REQUIREMENTS:
- Use proper type hints and validation
- No fallback or placeholder logic
- Raise errors for any missing or invalid data
- Use only the specified attributes
- No extra fields
- Must include 'from pydantic import BaseModel' import
- Must have 'class {entity}(BaseModel):' definition
- Must include proper field definitions with type hints
"""

    def _build_api_prompt(self, entity: str, attributes: List[str], context: str,
                          techlead_feedback: List[str] = None, previous_errors: List[str] = None,
                          retry_count: int = 0) -> str:
        feedback_section = ""
        if techlead_feedback or previous_errors:
            feedback_section = "\n\nCRITICAL FEEDBACK TO INCORPORATE:\n"
            if techlead_feedback:
                feedback_section += "TechLeadSWEA feedback:\n"
                for feedback in techlead_feedback:
                    feedback_section += f"- {feedback}\n"
            if previous_errors:
                feedback_section += "Previous errors to fix:\n"
                for error in previous_errors:
                    feedback_section += f"- {error}\n"
            feedback_section += "\nIMPORTANT: Address ALL feedback above in your response.\n"
        
        retry_info = ""
        if retry_count > 0:
            retry_info = f"\nThis is retry attempt #{retry_count}. Please ensure you address the feedback above."
        
        return f"""
Generate FastAPI router code for the {entity} entity with the following attributes:
{attributes}
Context: {context}{feedback_section}{retry_info}

REQUIREMENTS:
- Use APIRouter, not FastAPI app
- Implement full CRUD endpoints (POST, GET, PUT, DELETE)
- Use only the specified attributes
- No fallback or placeholder logic
- Raise errors for any missing or invalid data
- Use generic database path: app/database/baes_system.db
- No extra fields

CRITICAL API REQUIREMENTS:
- Must include '@contextmanager' decorator for database connection function
- Must implement proper error handling with HTTPException
- Must include all CRUD endpoints: create_, get_, update_, delete_, list_
- DELETE endpoint must return status code 204 (HTTP_204_NO_CONTENT)
- POST endpoint must return status code 201 (HTTP_201_CREATED)
- Must use proper FastAPI imports: APIRouter, HTTPException, Depends, status, Response
- Must include contextlib import for @contextmanager
"""

    def _write_to_managed_system(self, entity: str, code: str, artifact_type: str) -> str:
        # Only write route files; models are included in the route file
        if artifact_type == "api":
            base_path = Path(os.getenv("BAE_MANAGED_SYSTEM_PATH", "../managed_system/app/routes"))
            base_path.mkdir(parents=True, exist_ok=True)
            file_path = base_path / f"{entity.lower()}_routes.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            return str(file_path)
        return None 