import logging
import os
from typing import Any, Dict, List
from baes.agents.base_agent import BaseAgent
from baes.llm.openai_client import OpenAIClient
from baes.core.managed_system_manager import ManagedSystemManager
from baes.utils.template_registry import (
    TemplateRegistry,
    TemplateInput,
    EntityType,
    SWEAType,
)
from baes.utils.presentation_logger import get_presentation_logger
from config import Config
from pathlib import Path

logger = logging.getLogger(__name__)
presentation_logger = get_presentation_logger()


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
        self._template_registry = None  # Lazy initialization (Feature 001-performance-optimization)

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    @property
    def template_registry(self):
        """Lazy initialization of TemplateRegistry (Feature 001-performance-optimization)"""
        if self._template_registry is None:
            self._template_registry = TemplateRegistry()
        return self._template_registry

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle backend SWEA tasks. Always use the full attribute list from the payload."""
        attributes = payload.get("attributes")
        if not attributes or not isinstance(attributes, list):
            raise ValueError("BackendSWEA requires a non-empty attribute list in the payload.")
        for attr in attributes:
            if not isinstance(attr, dict) or "name" not in attr or "type" not in attr:
                raise ValueError(f"Invalid attribute format in BackendSWEA: {attr}")
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
        is_evolution: bool = payload.get("is_evolution", False)
        new_attributes: List[str] = payload.get("new_attributes", [])
        
        # CRITICAL: Check for attribute constraints
        use_only_specified = payload.get("use_only_specified_attributes", False)
        do_not_add_extra = payload.get("do_not_add_extra_fields", False)
        attribute_constraints = payload.get("attribute_constraints", {})

        # Template-based generation (Feature 001-performance-optimization)
        if Config.ENABLE_TEMPLATES and not is_evolution and not techlead_feedback:
            # Try template generation for standard CRUD
            entity_type_classification = payload.get("entity_classification", {})
            entity_type_str = entity_type_classification.get("entity_type", "STANDARD")
            entity_type = EntityType.STANDARD if entity_type_str == "STANDARD" else EntityType.CUSTOM

            # Convert attributes to template format
            attr_dict = {}
            for attr in attributes:
                if isinstance(attr, dict):
                    attr_dict[attr["name"]] = attr.get("type", "str")
                elif isinstance(attr, str):
                    parts = attr.split(":")
                    attr_dict[parts[0]] = parts[1] if len(parts) > 1 else "str"

            template_input = TemplateInput(
                entity_name=entity,
                entity_type=entity_type,
                swea_type=SWEAType.BACKEND,
                attributes=attr_dict,
            )

            template_output = self.template_registry.render_template(template_input)

            if template_output.template_used:
                # Template generation successful
                code = template_output.generated_code
                file_path = self.managed_system_manager.write_entity_artifact(entity, "routes", code)
                
                # Log optimization metrics
                presentation_logger.template_selected(
                    "backend",
                    template_output.template_id,
                    template_output.token_estimate
                )
                
                logger.info(
                    "BackendSWEA used template %s for %s (saved ~%d tokens, %.1fms)",
                    template_output.template_id,
                    entity,
                    template_output.token_estimate,
                    template_output.rendering_time_ms
                )
                
                return self.create_success_response(
                    "generate_api",
                    {
                        "file_path": file_path,
                        "code": code,
                        "entity": entity,
                        "attributes": attributes,
                        "template_used": True,
                        "template_id": template_output.template_id,
                        "token_estimate": template_output.token_estimate,
                    },
                )
            else:
                # Template fallback to LLM
                presentation_logger.template_fallback(
                    "backend",
                    template_output.template_id or "backend_routes_crud",
                    template_output.fallback_reason
                )
                logger.info(
                    "BackendSWEA template fallback for %s: %s",
                    entity,
                    template_output.fallback_reason
                )
        
        # Build prompt with evolution-aware instructions and strict attribute constraints
        prompt = self._build_api_prompt(
            entity,
            attributes,
            context,
            techlead_feedback,
            previous_errors,
            retry_count,
            is_evolution,
            new_attributes,
            use_only_specified,
            do_not_add_extra,
            attribute_constraints,
        )
        code = self.llm_client.generate_code_with_domain_focus(
            prompt, code_type="FastAPI Routes", entity_context={"entity": entity, "attributes": attributes}
        )
        if not code or not isinstance(code, str):
            raise RuntimeError(f"LLM did not return valid API code for {entity}.")
        file_path = self.managed_system_manager.write_entity_artifact(entity, "routes", code)
        return self.create_success_response(
            "generate_api",
            {"file_path": file_path, "code": code, "entity": entity, "attributes": attributes, "template_used": False},
        )

    def _build_model_prompt(self, entity: str, attributes: List[str], context: str, 
                           techlead_feedback: List[str] = None, previous_errors: List[str] = None, 
                           retry_count: int = 0, is_evolution: bool = False, new_attributes: List[str] = None) -> str:
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

        # All attributes optional instruction for PoC
        optional_fields_instruction = (
            "\nIMPORTANT: For this proof of concept, EVERY attribute listed below MUST be declared as Optional in the Pydantic model and default to None.\n"
        )
        
        return f"""
Generate a Pydantic model for the {entity} entity with the following attributes (ALL OPTIONAL):
{attributes}
Context: {context}{feedback_section}{retry_info}{optional_fields_instruction}

REQUIREMENTS:
- Use proper type hints and validation
- Declare every field as Optional[<type>] = None
- No fallback or placeholder logic
- Use only the specified attributes
- No extra fields
- Must include 'from pydantic import BaseModel' import
- Must have 'class {entity}(BaseModel):' definition
- Must include proper field definitions with type hints
"""

    def _build_api_prompt(self, entity: str, attributes: List[str], context: str,
                          techlead_feedback: List[str] = None, previous_errors: List[str] = None,
                          retry_count: int = 0, is_evolution: bool = False, new_attributes: List[str] = None,
                          use_only_specified: bool = False, do_not_add_extra: bool = False, 
                          attribute_constraints: Dict[str, Any] = None) -> str:
        if attribute_constraints is None:
            attribute_constraints = {}
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

        # All attributes optional instruction for PoC
        optional_fields_instruction = (
            "\nIMPORTANT: For this proof of concept, EVERY attribute listed below MUST be declared as Optional in the Pydantic models (Create, Update, Response) and default to None.\n"
        )
        
        # Format attributes list for clearer display
        attributes_display = "\n".join([f"- {attr}" for attr in attributes])
        entity_lower = entity.lower()
        
        # Build constraint warnings if specified
        constraint_warning = ""
        if use_only_specified or do_not_add_extra or attribute_constraints.get("use_only_specified_attributes"):
            constraint_warning = f"""
🚨 CRITICAL ATTRIBUTE CONSTRAINTS (VIOLATION WILL CAUSE REJECTION):
- USE ONLY THE {len(attributes)} ATTRIBUTES LISTED ABOVE
- DO NOT ADD ANY EXTRA FIELDS OR ATTRIBUTES
- DO NOT ADD DEFAULT FIELDS LIKE 'created_at', 'updated_at', 'description', 'code', etc.
- USER EXPLICITLY SPECIFIED ONLY THESE ATTRIBUTES: {len(attributes)} attributes
- STRICT COMPLIANCE REQUIRED - ANY EXTRA FIELDS WILL BE REJECTED
- This is user-specified creation - respect their exact requirements

"""
        
        return f"""
Generate FastAPI router code for the {entity} entity with EXACTLY these attributes and NO OTHERS:
{attributes_display}
Context: {context}{constraint_warning}{feedback_section}{retry_info}{optional_fields_instruction}

CRITICAL REQUIREMENTS (ALL MUST BE IMPLEMENTED):
- Use APIRouter with correct prefix: prefix="/api/{entity_lower}s"
- Implement full CRUD endpoints (POST, GET, PUT, DELETE)
- Use ONLY the attributes listed above - DO NOT ADD EXTRA FIELDS
- Router endpoints should be: /, /{{id}}, etc. (not full paths)
- No fallback or placeholder logic
- ALL Pydantic models MUST declare every attribute as Optional[<type>] = None (including Response model)
- Use generic database path: app/database/baes_system.db

CRITICAL ROUTER CONFIGURATION:
- Must use: router = APIRouter(prefix="/api/{entity_lower}s", tags=["{entity}s"])
- Endpoints should be @router.post("/"), @router.get("/"), etc.
- This creates routes like /api/{entity_lower}s/, /api/{entity_lower}s/{{id}}, etc.

CRITICAL PYDANTIC MODELS (ONLY USE SPECIFIED ATTRIBUTES):
- {entity}Create: Only the attributes listed above (NEVER include id field, no extra fields)
- {entity}Update: Only the attributes listed above as Optional fields (NEVER include id field, no extra fields)  
- {entity}Response: All attributes, but new attributes (added during evolution) must be Optional and default to None
- IMPORTANT: The 'id' field is auto-generated by the database and should NEVER be included in Create or Update models
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

🚨 FINAL WARNING: The user explicitly requested ONLY the attributes listed above. Adding ANY extra fields beyond what's specified will violate user requirements. This is a user-constrained creation - respect their exact specification.
"""

 