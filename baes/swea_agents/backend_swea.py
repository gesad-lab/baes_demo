import logging
import os
from typing import Any, Dict, List
from baes.agents.base_agent import BaseAgent
from baes.llm.openai_client import OpenAIClient
from baes.core.managed_system_manager import ManagedSystemManager
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
        self._managed_system_manager = None  # Lazy initialization

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

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
        
        # Use the proper managed system manager to write route files
        file_path = self.managed_system_manager.write_entity_artifact(entity, "routes", code)
        
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
        
        # Format attributes list for clearer display
        attributes_display = "\n".join([f"- {attr}" for attr in attributes])
        entity_lower = entity.lower()
        
        return f"""
Generate FastAPI router code for the {entity} entity with EXACTLY these attributes and NO OTHERS:
{attributes_display}
Context: {context}{feedback_section}{retry_info}

CRITICAL REQUIREMENTS (ALL MUST BE IMPLEMENTED):
- Use APIRouter with correct prefix: prefix="/api/{entity_lower}s"
- Implement full CRUD endpoints (POST, GET, PUT, DELETE)
- Use ONLY the attributes listed above - DO NOT ADD EXTRA FIELDS
- Router endpoints should be: /, /{{id}}, etc. (not full paths)
- No fallback or placeholder logic
- Raise errors for any missing or invalid data
- Use generic database path: app/database/baes_system.db

CRITICAL ROUTER CONFIGURATION:
- Must use: router = APIRouter(prefix="/api/{entity_lower}s", tags=["{entity}s"])
- Endpoints should be @router.post("/"), @router.get("/"), etc.
- This creates routes like /api/{entity_lower}s/, /api/{entity_lower}s/{{id}}, etc.

CRITICAL PYDANTIC MODELS (ONLY USE SPECIFIED ATTRIBUTES):
- {entity}Create: Only the attributes listed above (no id, no extra fields)
- {entity}Response: Include id plus the attributes listed above (no extra fields)
- {entity}Update: Only the attributes listed above (no id, no extra fields)
- DO NOT add any fields not explicitly specified in the attributes list

MANDATORY CODE QUALITY REQUIREMENTS:
- ALL FUNCTIONS MUST HAVE DETAILED DOCSTRINGS (no exceptions)
- ALL FUNCTIONS MUST HAVE PROPER RETURN TYPE HINTS (no exceptions)
- ALL IMPORTS MUST BE COMPLETE AND CORRECT
- ALL ERROR HANDLING MUST BE COMPREHENSIVE

CRITICAL DATABASE REQUIREMENTS (MANDATORY):
- Must use @contextmanager decorator for database connection function
- Must include database rollback in all exception handlers: db.rollback()
- Must implement proper try/except/finally blocks for all database operations
- Database connections must be properly closed in finally blocks
- Must include comprehensive error handling with HTTPException

CRITICAL API STANDARDS:
- Must implement proper error handling with HTTPException
- Must include all CRUD endpoints: create_, get_, update_, delete_, list_
- DELETE endpoint MUST return Response(status_code=status.HTTP_204_NO_CONTENT)
- POST endpoint MUST use status_code=status.HTTP_201_CREATED in decorator
- Must use proper FastAPI imports: APIRouter, HTTPException, Depends, status, Response
- Must include contextlib import for @contextmanager
- Must include logging import and logger setup

MANDATORY EXCEPTION HANDLING PATTERN (CRITICAL):
Every database operation MUST follow this exact pattern:
```python
try:
    # database operations here
    db.commit()
except HTTPException:
    raise  # Re-raise HTTPException without modification
except Exception as e:
    db.rollback()  # MANDATORY - will be rejected without this
    logger.error(f"Database error: {{e}}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

MANDATORY DOCSTRING REQUIREMENTS:
- Every function MUST have a comprehensive docstring
- Docstrings MUST describe purpose, parameters, and return values
- Use proper docstring format with Args: and Returns: sections

MANDATORY TYPE HINT REQUIREMENTS:
- Every function MUST have complete return type hints
- Use proper typing imports (List, Optional, Dict, etc.)
- All parameters MUST have type hints

MANDATORY DATABASE CONNECTION PATTERN:
```python
from contextlib import contextmanager
import sqlite3
from pathlib import Path

@contextmanager
def get_db_connection():
    \"\"\"Database connection context manager with proper error handling\"\"\"
    db_path = Path("app/database/baes_system.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

EXAMPLE ROUTER STRUCTURE:
```python
from fastapi import APIRouter, HTTPException, Depends, status, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from contextlib import contextmanager
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{entity_lower}s", tags=["{entity}s"])

class {entity}Create(BaseModel):
    # Only the specified attributes, no extra fields
    
class {entity}Response(BaseModel):
    id: int
    # Only the specified attributes, no extra fields

@router.post("/", response_model={entity}Response, status_code=status.HTTP_201_CREATED)
def create_{entity_lower}(data: {entity}Create) -> Dict[str, Any]:
    # Implementation here
```

CRITICAL REMINDER: Use ONLY the attributes specified above. Do not add age, created_at, updated_at, or any other fields unless explicitly listed in the attributes.
"""

 