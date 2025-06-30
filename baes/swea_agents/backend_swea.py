import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from baes.core.managed_system_manager import ManagedSystemManager
from baes.domain_entities.base_bae import BaseAgent
from baes.llm.openai_client import OpenAIClient
from baes.utils.llm_response_validator import parse_llm_json_response
from config import Config

# Utility for conditional debug logging

logger = logging.getLogger(__name__)


# Add analytics tracking for feedback loops
class FeedbackLoopAnalytics:
    """
    Stage 2 Improvement #8: Feedback Loop Logging and Analytics
    Tracks all feedback interactions between TechLeadSWEA and BackendSWEA in CSV format.
    """

    def __init__(self):
        # Use tests/.temp for analytics during tests
        if Config.IS_TEST_ENVIRONMENT:
            self.analytics_dir = Path("tests/.temp")
        else:
            self.analytics_dir = Path("logs/feedback_analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.analytics_dir / "feedback_loop_analytics.csv"
        self._ensure_csv_headers()

    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for pandas DataFrame compatibility"""
        if not self.csv_file.exists():
            headers = [
                "timestamp",
                "session_id",
                "entity",
                "code_type",
                "feedback_round",
                "techlead_feedback_count",
                "feedback_categories",
                "backend_response_time_seconds",
                "feedback_addressed",
                "retry_count",
                "final_success",
                "feedback_text_length",
                "code_changes_made",
                "improvement_areas",
            ]
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def log_feedback_interaction(
        self,
        session_id: str,
        entity: str,
        code_type: str,
        feedback_round: int,
        techlead_feedback: List[str],
        backend_response_time: float,
        feedback_addressed: bool,
        retry_count: int,
        final_success: bool,
        code_changes_made: List[str] = None,
    ):
        """Log feedback loop interaction to CSV for analytics"""
        try:
            # Categorize feedback for analytics
            feedback_categories = self._categorize_feedback(techlead_feedback)
            improvement_areas = self._extract_improvement_areas(techlead_feedback)
            row_data = [
                datetime.now().isoformat(),
                session_id,
                entity,
                code_type,
                feedback_round,
                len(techlead_feedback),
                ";".join(feedback_categories),
                round(backend_response_time, 2),
                feedback_addressed,
                retry_count,
                final_success,
                sum(len(fb) for fb in techlead_feedback),
                ";".join(code_changes_made or []),
                ";".join(improvement_areas),
            ]
            with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            logger.info(
                f"📊 Feedback analytics logged: {entity}.{code_type} round {feedback_round}"
            )
        except Exception as e:
            logger.warning(f"Failed to log feedback analytics: {e}")

    def _categorize_feedback(self, feedback_list: List[str]) -> List[str]:
        """Categorize feedback for analytics purposes"""
        categories = set()
        feedback_text = " ".join(feedback_list).lower()
        # Database-related feedback
        if any(
            term in feedback_text
            for term in ["database", "connection", "context manager", "sqlite"]
        ):
            categories.add("database")
        # API/Endpoint feedback
        if any(term in feedback_text for term in ["endpoint", "api", "route", "http", "status"]):
            categories.add("api")
        # Code structure feedback
        if any(
            term in feedback_text for term in ["import", "syntax", "structure", "class", "function"]
        ):
            categories.add("code_structure")
        # Error handling feedback
        if any(
            term in feedback_text for term in ["error", "exception", "try", "catch", "handling"]
        ):
            categories.add("error_handling")
        # Validation feedback
        if any(term in feedback_text for term in ["validation", "validate", "check", "verify"]):
            categories.add("validation")
        return list(categories) if categories else ["general"]

    def _extract_improvement_areas(self, feedback_list: List[str]) -> List[str]:
        """Extract specific improvement areas from feedback"""
        areas = set()
        feedback_text = " ".join(feedback_list).lower()
        if "performance" in feedback_text:
            areas.add("performance")
        if "security" in feedback_text:
            areas.add("security")
        if "maintainability" in feedback_text:
            areas.add("maintainability")
        if "documentation" in feedback_text:
            areas.add("documentation")
        if "testing" in feedback_text:
            areas.add("testing")
        return list(areas) if areas else ["code_quality"]


class BackendGenerationError(Exception):
    """Custom exception for backend generation failures"""

    pass


class BackendSWEA(BaseAgent):
    """
    Software Engineering Autonomous Agent responsible for generating backend code
    (Pydantic model and FastAPI routes) while preserving domain semantics.
    """

    def __init__(self):
        super().__init__("BackendSWEA", "Backend Code Generation Agent", "SWEA")
        self.llm_client = OpenAIClient()
        self._managed_system_manager = None  # Lazy initialization
        # Stage 2 Improvement #8: Feedback Loop Analytics
        self.feedback_analytics = FeedbackLoopAnalytics()
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "generate_model": "_generate_model",
        "generate_api": "_generate_api",
        "generate_crud": "_generate_crud",
        "generate_routes": "_generate_routes",
        "generate_dependencies": "_generate_dependencies",
        "generate_requirements": "_generate_requirements",
        "fix_issues": "_fix_backend_issues",
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch task to internal generator methods."""
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
    # Core validation and type safety methods
    # ------------------------------------------------------------------
    def _validate_entity_parameter(self, entity: Any) -> str:
        """
        Validate and normalize entity parameter to ensure it's a string.
        This is the root cause fix for the 'str' object has no attribute 'lower()' error.
        """
        if entity is None:
            raise BackendGenerationError("Entity parameter cannot be None")
        if not isinstance(entity, str):
            raise BackendGenerationError(
                f"Entity parameter must be a string, received {type(entity)}: {entity}"
            )
        # Ensure it's not empty
        if not entity.strip():
            raise BackendGenerationError("Entity parameter cannot be empty or whitespace")
        return entity.strip()

    def _validate_attributes_parameter(self, attributes: Any) -> List[str]:
        """
        Validate and normalize attributes parameter to ensure it's a list of strings.
        """
        if attributes is None:
            return []
        if not isinstance(attributes, list):
            raise BackendGenerationError(
                f"Attributes parameter must be a list, received {type(attributes)}"
            )
        # Convert all items to strings and filter out None/empty values
        normalized_attributes = []
        for i, attr in enumerate(attributes):
            if attr is None:
                continue
            try:
                attr_str = str(attr).strip()
                if attr_str:
                    normalized_attributes.append(attr_str)
            except Exception as e:
                logger.warning(
                    f"BackendSWEA: Skipping invalid attribute at index {i}: {attr} (error: {e})"
                )
        return normalized_attributes

    def _validate_payload_structure(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize the entire payload structure.
        This ensures all required fields are present and properly typed.
        """
        if not isinstance(payload, dict):
            raise BackendGenerationError(f"Payload must be a dictionary, received {type(payload)}")
        # Extract and validate core parameters
        entity = self._validate_entity_parameter(payload.get("entity"))
        attributes = self._validate_attributes_parameter(payload.get("attributes"))
        context = str(payload.get("context", "academic")).strip()
        # Validate optional parameters
        techlead_feedback = self._validate_feedback_parameter(payload.get("techlead_feedback"))
        previous_errors = self._validate_feedback_parameter(payload.get("previous_errors"))
        expected_output = str(payload.get("expected_output", "")).strip()
        return {
            "entity": entity,
            "attributes": attributes,
            "context": context,
            "techlead_feedback": techlead_feedback,
            "previous_errors": previous_errors,
            "expected_output": expected_output,
        }

    def _validate_feedback_parameter(self, feedback: Any) -> List[str]:
        """
        Validate and normalize feedback parameters to ensure they're lists of strings.
        """
        if feedback is None:
            return []
        if isinstance(feedback, str):
            return [feedback.strip()] if feedback.strip() else []
        if isinstance(feedback, list):
            normalized_feedback = []
            for item in feedback:
                if item is not None:
                    try:
                        item_str = str(item).strip()
                        if item_str:
                            normalized_feedback.append(item_str)
                    except Exception:
                        continue
            return normalized_feedback
        # Try to convert to string if it's some other type
        try:
            feedback_str = str(feedback).strip()
            return [feedback_str] if feedback_str else []
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Generic attribute management methods
    # ------------------------------------------------------------------
    def _get_default_attributes(self, entity: str) -> List[str]:
        """Get default attributes for an entity when none provided"""
        # CRITICAL FIX: Use the centralized validation method to prevent 'str' object has no attribute 'lower()' error
        try:
            entity = self._validate_entity_parameter(entity)
        except BackendGenerationError as e:
            logger.warning(
                f"BackendSWEA: Entity validation failed in _get_default_attributes: {e}, using generic defaults"
            )
            return ["name: str", "description: str", "created_at: str"]
        entity_lower = entity.lower()
        if entity_lower == "student":
            return ["name: str", "email: str", "age: int"]
        elif entity_lower == "course":
            return ["name: str", "code: str", "credits: int"]
        elif entity_lower == "teacher":
            return ["name: str", "email: str", "department: str"]
        else:
            # GENERIC FALLBACK: Works for any entity type
            return ["name: str", "description: str", "created_at: str"]

    # ------------------------------------------------------------------
    # Prompt building and template management
    # ------------------------------------------------------------------
    def _build_prompt(
        self,
        entity: str,
        attributes: List[str],
        code_type: str,
        context: str,
        feedback_section: str = "",
    ) -> str:
        """Load prompt template and format it with runtime values."""
        # CRITICAL FIX: Ensure entity is a valid string before template formatting
        try:
            entity = self._validate_entity_parameter(entity)
        except BackendGenerationError as e:
            logger.error(f"BackendSWEA: Entity validation failed in _build_prompt: {e}")
            # Use a safe fallback entity name
            entity = "Entity"
        attributes = self._validate_attributes_parameter(attributes)
        # Ensure all elements in attributes are strings
        for i, attr in enumerate(attributes):
            if not isinstance(attr, str):
                logger.error(
                    f"BackendSWEA: Attribute at index {i} is not a string: {attr} (type: {type(attr)})"
                )
                attributes[i] = str(attr)
        code_type = str(code_type).strip()
        context = str(context).strip()
        template_path = os.path.join("baes", "llm", "prompts", "backend_gen.txt")
        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            # Fallback prompt if template missing
            template = (
                "You are a BackendSWEA agent. Generate clean, production-ready Python code for {code_type} "
                "representing the {entity} domain entity. Attributes: {attributes}. "
                "Use business vocabulary and FastAPI/Pydantic best practices. Return ONLY code."
            )
        try:
            # CRITICAL FIX: Precompute all required template variables
            safe_entity = str(entity).strip()
            safe_entity_lower = safe_entity.lower()
            safe_Entity = safe_entity.capitalize()
            safe_attributes = ", ".join([str(attr).strip() for attr in attributes])
            safe_code_type = str(code_type).strip()
            safe_context = str(context).strip()
            safe_feedback_section = str(feedback_section)
            return template.format(
                entity=safe_entity,
                entity_lower=safe_entity_lower,
                entity_name_lower=safe_entity_lower,
                entity_name_lower_data=f"{safe_entity_lower}_data",
                Entity=safe_Entity,
                attributes=safe_attributes,
                code_type=safe_code_type,
                context=safe_context,
                feedback_section=safe_feedback_section,
            )
        except (KeyError, AttributeError) as e:
            # CRITICAL: Remove silent fallback - raise explicit error for debugging
            logger.error(f"BackendSWEA: Template formatting failed with error: {e}")
            logger.error(f"BackendSWEA: Error type: {type(e)}")
            logger.error(f"BackendSWEA: Error args: {e.args}")
            logger.error(
                f"BackendSWEA: Template variables - entity: {entity} (type: {type(entity)})"
            )
            logger.error(
                f"BackendSWEA: Template variables - attributes: {attributes} (type: {type(attributes)})"
            )
            logger.error(
                f"BackendSWEA: Template variables - code_type: {code_type} (type: {type(code_type)})"
            )
            logger.error(
                f"BackendSWEA: Template variables - context: {context} (type: {type(context)})"
            )
            logger.error(
                f"BackendSWEA: Template variables - feedback_section: {feedback_section} (type: {type(feedback_section)})"
            )
            logger.error(f"BackendSWEA: Template content (first 500 chars): {template[:500]}")
            raise BackendGenerationError(
                f"Template formatting failed: {e}. This indicates a critical issue with the prompt template or variable types."
            )

    def _write_to_managed_system(self, entity: str, artifact_type: str, code: str) -> str:
        """Write code to the managed system instead of the legacy generated directory."""
        # Validate parameters
        entity = self._validate_entity_parameter(entity)
        artifact_type = str(artifact_type).strip()
        if not code or not isinstance(code, str):
            raise BackendGenerationError(f"Code must be a non-empty string, received {type(code)}")
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()
        # Write the artifact to managed system
        file_path = self.managed_system_manager.write_entity_artifact(entity, artifact_type, code)
        # Update main system files to include new entity
        self.managed_system_manager.update_system_files()
        return file_path

    # ------------------------------------------------------------------
    # Feedback interpretation methods
    # ------------------------------------------------------------------
    def _validate_interpretation_structure(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure interpretation has correct structure with proper data types."""
        if not isinstance(interpretation, dict):
            raise BackendGenerationError(
                f"Interpretation must be a dictionary, received {type(interpretation)}"
            )
        validated = {
            "attributes": [],
            "additional_requirements": [],
            "code_improvements": [],
            "modifications": [],
            "explanation": str(interpretation.get("explanation", "No explanation provided")),
        }
        # Normalize attributes to consistent string format
        raw_attributes = interpretation.get("attributes", [])
        if not isinstance(raw_attributes, list):
            raise BackendGenerationError(
                f"Attributes must be a list, received {type(raw_attributes)}"
            )
        logger.debug(
            f"BackendSWEA: Processing {len(raw_attributes)} attributes with types: {[type(attr) for attr in raw_attributes]}"
        )
        for attr in raw_attributes:
            if isinstance(attr, dict):
                # Convert dict to "name:type" string format
                name = str(attr.get("name", "field")).strip()
                typ = str(attr.get("type", "str")).strip()
                validated["attributes"].append(f"{name}:{typ}")
                logger.debug(f"BackendSWEA: Converted dict attribute to string: {name}:{typ}")
            elif isinstance(attr, str):
                validated["attributes"].append(attr.strip())
            else:
                # Convert to string
                str_attr = str(attr).strip()
                validated["attributes"].append(str_attr)
                logger.warning(
                    f"BackendSWEA: Converted unexpected attribute type {type(attr)} to string: {str_attr}"
                )
        # Ensure other fields are lists of strings
        for field in ["additional_requirements", "code_improvements", "modifications"]:
            raw_list = interpretation.get(field, [])
            if not isinstance(raw_list, list):
                raw_list = []
            validated[field] = [str(item).strip() for item in raw_list if item is not None]
        logger.debug(
            f"BackendSWEA: Validated interpretation with {len(validated['attributes'])} normalized attributes"
        )
        return validated

    def _interpret_feedback_for_backend_generation(
        self, feedback: List[str], entity: str, code_type: str, original_attributes: List[str]
    ) -> Dict[str, Any]:
        """
        Enhanced feedback interpretation using LLM to understand what backend code changes are needed.
        This approach specifically handles TechLeadSWEA's detailed, actionable feedback.
        """
        # CRITICAL FIX: Use centralized validation to prevent 'str' object has no attribute 'lower()' error
        try:
            entity = self._validate_entity_parameter(entity)
            code_type = (
                str(code_type).strip()
                if code_type
                else "Complete FastAPI Routes with Pydantic Models"
            )
            original_attributes = self._validate_attributes_parameter(original_attributes)
            feedback = self._validate_feedback_parameter(feedback)
        except BackendGenerationError as e:
            logger.error(
                f"BackendSWEA: Parameter validation failed in _interpret_feedback_for_backend_generation: {e}"
            )
            raise
        if not feedback:
            logger.debug(
                f"BackendSWEA: No feedback provided for {entity} {code_type}, using original attributes"
            )
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "code_improvements": [],
                "modifications": [],
                "feedback_section": "",
            }
        feedback_text = "\n".join(feedback)
        logger.debug(
            f"BackendSWEA: Interpreting feedback for {entity} {code_type}: {feedback_text}"
        )
        # Stage 4 Improvement #1: Get structured feedback for injection
        # structured_feedback = self._get_structured_feedback_injection(entity, "BackendSWEA", code_type)
        system_prompt = """You are a BackendSWEA (
            Software Engineering Autonomous Agent) specializing in backend code generation.
You MUST focus on CRITICAL and REQUIRED feedback only. Ignore OPTIONAL suggestions.

TASK:
Interpret the TechLeadSWEA feedback and provide specific backend code improvements in JSON format.
TechLeadSWEA provides detailed, actionable suggestions that you must implement precisely.

RESPONSE FORMAT (JSON only):
{{
    "attributes": ["list", "of", "final", "attributes", "with", "types"],
    "additional_requirements": ["any", "new", "requirements", "identified"],
    "code_improvements": ["specific", "code", "improvements", "to", "make"],
    "modifications": ["changes", "to", "implement"],
    "feedback_section": "structured feedback for prompt template",
    "explanation": "brief explanation of changes made based on feedback"
}}

FEEDBACK ANALYSIS GUIDELINES:
PRIORITY-BASED PROCESSING:
1. **CRITICAL Issues** (Handle Immediately):
   - "[CRITICAL]" tagged feedback items
   - Database connection leaks, security vulnerabilities
   - Syntax errors, import failures, runtime crashes
   - Empty classes/functions, missing core implementation

2. **REQUIRED Issues** (Handle Before Approval):
   - "[REQUIRED]" tagged feedback items
   - Missing error handling, incomplete CRUD operations
   - Incorrect HTTP status codes, missing validation
   - Performance issues, resource management problems

3. **OPTIONAL Issues** (IGNORE for now):
   - "[OPTIONAL]" tagged feedback items
   - Code style improvements, additional logging
   - Performance optimizations, UX enhancements
   - Non-essential features, convenience methods

SPECIFIC ISSUE PATTERNS:
- **Database Connection Issues**: If feedback mentions "context manager",
     "connection leaks",
     or "proper connection handling",
     add database connection management improvements
- **Error Handling Issues**: If feedback mentions "error handling",
     "HTTP status codes",
     or "validation errors",
     add comprehensive error handling requirements
- **Code Structure Issues**: If feedback mentions "missing endpoints",
     "naming conventions",
     or "import statements",
     add structural improvements
- **Data Validation Issues**: If feedback mentions "field validation",
     "type hints",
     or "data conversion",
     add validation requirements
- **API Design Issues**: If feedback mentions "RESTful design",
     "response models",
     or "request validation",
     add API design improvements

FEEDBACK_SECTION FORMAT:
Create a structured feedback section that includes:
- Specific issues identified by TechLeadSWEA
- Exact fixes to implement
- Code patterns to follow
- Quality requirements to meet

Example feedback_section:
"TECHLEAD FEEDBACK TO IMPLEMENT:
1. Database Connection Management: Use context managers for all database operations
2. Error Handling: Add comprehensive try/except blocks with proper HTTP status codes
3. API Structure: Ensure all CRUD endpoints are implemented with correct naming
4. Data Validation: Add Pydantic validators for all input fields
5. Response Models: Use proper Pydantic response models with from_attributes=True"

GUIDELINES:
- Preserve existing attributes unless feedback specifically requests changes
- Add new attributes if feedback suggests missing fields
- Include proper data types (str, int, float, date, bool)
- Consider FastAPI/Pydantic best practices
- Handle any type of feedback, even unexpected ones
- If feedback is unclear, make reasonable backend development assumptions
- ALWAYS include a structured feedback_section for the prompt template
"""
        user_prompt = (
            f"Based on the feedback provided, what backend code improvements should be made "
            f"for the {entity} entity's {code_type}?\n"
            f"Feedback to interpret (contains specific fix suggestions):\n"
            f"{feedback_text}\n"
            f"Current attributes:\n"
            f"{original_attributes}\n"
            f"Please provide the JSON response with backend improvements, implementing the specific fixes suggested in the feedback."
        )
        # Stage 2 Improvement #8: Track analytics timing
        start_time = datetime.now()
        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            logger.debug(f"BackendSWEA: Raw LLM response for {code_type}: {response}")
            # Use utility to parse JSON response with markdown code block handling
            try:
                interpretation = parse_llm_json_response(response, "backend", original_attributes)
                logger.debug(
                    f"BackendSWEA: Parsed interpretation for {code_type}: {interpretation}"
                )
                # Stage 2 Improvement #8: Log successful feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                code_changes = interpretation.get("code_improvements", []) + interpretation.get(
                    "modifications", []
                )
                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    code_type=code_type,
                    feedback_round=1,  # Default to 1, can be enhanced later
                    techlead_feedback=feedback,
                    backend_response_time=response_time,
                    feedback_addressed=True,
                    retry_count=0,  # Default to 0, can be enhanced later
                    final_success=True,
                    code_changes_made=code_changes,
                )
                return interpretation
            except Exception as json_error:
                # Raising explicit error instead of silent fallback to avoid masking issues
                error_msg = (
                    f"LLM response for feedback interpretation is not valid JSON: {json_error}. "
                    f"Raw response: {response}"
                )
                logger.error(error_msg)
                # Stage 2 Improvement #8: Log failed feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    code_type=code_type,
                    feedback_round=1,
                    techlead_feedback=feedback,
                    backend_response_time=response_time,
                    feedback_addressed=False,
                    retry_count=0,
                    final_success=False,
                    code_changes_made=[],
                )
                raise BackendGenerationError(error_msg) from json_error
        except Exception as e:
            # Propagate detailed error – no silent fallback
            logger.error(
                f"BackendSWEA: Failed to interpret feedback for {entity} {code_type}: {str(e)}"
            )
            # Stage 2 Improvement #8: Log failed feedback interaction
            response_time = (datetime.now() - start_time).total_seconds()
            self.feedback_analytics.log_feedback_interaction(
                session_id=self.current_session_id,
                entity=entity,
                code_type=code_type,
                feedback_round=1,
                techlead_feedback=feedback,
                backend_response_time=response_time,
                feedback_addressed=False,
                retry_count=0,
                final_success=False,
                code_changes_made=[],
            )
            raise

    def _get_structured_feedback_injection(
        self, entity: str, swea_agent: str, task_type: str
    ) -> str:
        """
        Stage 4 Improvement #1: Get structured feedback injection from TechLeadSWEA.
        Returns formatted feedback instructions for prompt injection.
        """
        try:
            # Import TechLeadSWEA to access feedback storage
            from baes.swea_agents.techlead_swea import TechLeadSWEA

            # Create temporary TechLeadSWEA instance to access feedback storage
            techlead = TechLeadSWEA()
            structured_instructions = techlead._retrieve_feedback_for_injection(
                entity, swea_agent, task_type
            )
            if structured_instructions:
                logger.info(
                    f"📤 BackendSWEA: Retrieved structured feedback for {entity}.{swea_agent}.{task_type}"
                )
                return structured_instructions
            else:
                logger.debug(
                    f"📤 BackendSWEA: No structured feedback available for {entity}.{swea_agent}.{task_type}"
                )
                return ""
        except Exception as e:
            logger.warning(f"BackendSWEA: Failed to get structured feedback injection: {str(e)}")
            return ""

    # ------------------------------------------------------------------
    # Task implementations
    # ------------------------------------------------------------------
    def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        DEPRECATED: Model generation is now handled by _generate_api().
        This method is kept for backward compatibility but delegates to API generation.
        """
        logger.warning(
            "⚠️  BackendSWEA: _generate_model() is deprecated. Use _generate_api() instead."
        )
        return self._generate_api(payload)

    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete FastAPI routes with embedded Pydantic models.
        This replaces the separate model generation to ensure consistency.
        """
        # CRITICAL FIX: Use centralized validation to prevent 'str' object has no attribute 'lower()' error
        try:
            validated_payload = self._validate_payload_structure(payload)
            entity = validated_payload["entity"]
            attributes = validated_payload["attributes"]
            context = validated_payload["context"]
            techlead_feedback = validated_payload["techlead_feedback"]
            previous_errors = validated_payload["previous_errors"]
            expected_output = validated_payload["expected_output"]
        except BackendGenerationError as e:
            logger.error(f"BackendSWEA: Payload validation failed in _generate_api: {e}")
            raise
        # CRITICAL FIX: Ensure we have valid attributes
        if not attributes:
            logger.warning(f"🚨 BackendSWEA: No attributes provided for {entity}, using defaults")
            attributes = self._get_default_attributes(entity)
        # Combine all feedback sources
        all_feedback = []
        if techlead_feedback:
            all_feedback.extend(techlead_feedback)
        if previous_errors:
            all_feedback.extend(previous_errors)
        if expected_output:
            all_feedback.append(f"Expected output: {expected_output}")
        # ------------------------------------------------------------------
        # 1) Main generation pipeline
        # ------------------------------------------------------------------
        try:
            interpretation = self._interpret_feedback_for_backend_generation(
                all_feedback,
                entity,
                "Complete FastAPI Routes with Pydantic Models",
                attributes,
            )
            interpretation = self._validate_interpretation_structure(interpretation)
            # Always validate attributes from interpretation
            attributes = interpretation.get("attributes", [])
            if not isinstance(attributes, list):
                logger.error(
                    f"BackendSWEA: attributes after interpretation is not a list: {attributes} (type: {type(attributes)})"
                )
                attributes = []
            attributes = self._validate_attributes_parameter(attributes)
            code = self._apply_backend_improvements(
                interpretation,
                entity,
                "Complete FastAPI Routes with Pydantic Models",
                context,
            )
        except Exception as e:
            # Early failure – either interpretation or LLM call broke
            logger.error("❌ BackendSWEA.main_pipeline failure for %s: %s", entity, str(e))
            if os.getenv("BAE_ALLOW_FALLBACK", "1").lower() in ("1", "true", "yes", "on"):
                logger.info("🔄 BackendSWEA: Falling back due to BAE_ALLOW_FALLBACK flag")
                code = self._generate_fallback_api_code(entity, attributes, context, all_feedback)
            else:
                raise BackendGenerationError(
                    f"Main backend generation pipeline failed for {entity}: {e}"
                ) from e
        # ------------------------------------------------------------------
        # 2) Sanity check of produced code
        # ------------------------------------------------------------------
        if (
            not code
            or len(code.strip()) < 200
            or not self._verify_api_code_completeness(code, entity)
        ):
            msg = f"Generated API code for {entity} failed sanity check (missing CRUD endpoints or too short)"
            if os.getenv("BAE_ALLOW_FALLBACK", "1").lower() in ("1", "true", "yes", "on"):
                logger.warning("🚨 %s – falling back due to flag", msg)
                code = self._generate_fallback_api_code(entity, attributes, context, all_feedback)
                if (
                    not code
                    or len(code.strip()) < 200
                    or not self._verify_api_code_completeness(code, entity)
                ):
                    # Even fallback failed → raise
                    raise BackendGenerationError(msg + " – fallback also failed")
            else:
                raise BackendGenerationError(msg)
        # Write to routes file (this is the single source of truth)
        file_path = self._write_to_managed_system(entity, "routes", code)
        logger.info(
            f"✅ BackendSWEA: Generated complete API with models for {entity} at {file_path}"
        )
        return self.create_success_response(
            "generate_api",
            {
                "file_path": file_path,
                "code": code,
                "managed_system": True,
                "improvements_applied": {"fallback_used": len(code.strip()) > 0},
                "generation_type": "complete_api_with_models",
                "lines_generated": len(code.split("\n")),
            },
        )

    def _generate_fallback_api_code(
        self, entity: str, attributes: List[str], context: str, feedback: List[str]
    ) -> str:
        """
        Generate robust fallback API code when complex pipeline fails.
        This ensures we always have working CRUD endpoints.
        """
        # CRITICAL FIX: Use centralized validation to prevent 'str' object has no attribute 'lower()' error
        try:
            entity = self._validate_entity_parameter(entity)
            attributes = self._validate_attributes_parameter(attributes)
            context = str(context).strip() if context else "academic"
            feedback = self._validate_feedback_parameter(feedback)
        except BackendGenerationError as e:
            logger.error(
                f"BackendSWEA: Parameter validation failed in _generate_fallback_api_code: {e}"
            )
            raise
        try:
            # Build a simple, direct prompt for reliable code generation
            simple_prompt = f"""Generate a complete FastAPI routes file for {entity} entity with these requirements:
ENTITY: {entity}
ATTRIBUTES: {', '.join(attributes)}
CONTEXT: {context}
REQUIRED COMPONENTS:
1. Pydantic models (Base, Create, Update, Response)
2. Complete CRUD endpoints (POST, GET, PUT, DELETE, LIST)
3. Proper error handling with HTTPException
4. Database integration with dependency injection
5. Proper HTTP status codes (201, 200, 404, 500)
FEEDBACK TO ADDRESS: {'; '.join(feedback) if feedback else 'Generate complete working CRUD API'}
Generate ONLY Python code for a complete FastAPI router file with:
- All imports at the top
- Pydantic models embedded in same file
- All 5 CRUD endpoints implemented
- Proper error handling
- Database dependency injection
- No TODO comments or placeholders
Example structure for {entity}:
```python
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sqlite3
from pathlib import Path
# Database dependency
def get_db():
    ...
# Pydantic Models
class {entity}Base(BaseModel):
    ...
class {entity}Create({entity}Base):
    pass
class {entity}Update(BaseModel):
    ...
class {entity}Response({entity}Base):
    id: int
    class Config:
        from_attributes = True
# Router
router = APIRouter(prefix="/{entity.lower()}s", tags=["{entity.lower()}s"])
@router.post("/", response_model={entity}Response, status_code=status.HTTP_201_CREATED)
async def create_{entity.lower()}(...):
    ...
@router.get("/", response_model=List[{entity}Response])
async def list_{entity.lower()}s(...):
    ...
@router.get("/{{id}}", response_model={entity}Response)
async def get_{entity.lower()}(...):
    ...
@router.put("/{{id}}", response_model={entity}Response)
async def update_{entity.lower()}(...):
    ...
@router.delete("/{{id}}")
async def delete_{entity.lower()}(...):
    ...
```
Generate the complete implementation now:"""
            # Use direct LLM generation without complex interpretation
            code = self.llm_client.generate_code_with_domain_focus(
                simple_prompt,
                code_type="Complete FastAPI Routes with Pydantic Models",
                entity_context={
                    "entity": entity,
                    "attributes": attributes,
                    "fallback_generation": True,
                },
            )
            # Validate generated code
            if not isinstance(code, str):
                raise BackendGenerationError(
                    f"Fallback code generation failed: expected string, got {type(code)}"
                )
            # Verify the fallback code has basic requirements
            if not self._verify_api_code_completeness(code, entity):
                logger.warning(
                    f"🚨 BackendSWEA: Fallback code incomplete for {entity}, using template"
                )
                code = self._generate_template_api_code(entity, attributes)
            return code
        except Exception as e:
            logger.error(f"❌ BackendSWEA: Fallback generation failed for {entity}: {str(e)}")
            # Last resort: use hardcoded template
            return self._generate_template_api_code(entity, attributes)

    def _verify_api_code_completeness(self, code: str, entity: str) -> bool:
        """Verify that generated API code has minimum required components"""
        # CRITICAL FIX: Use centralized validation to prevent 'str' object has no attribute 'lower()' error
        if not isinstance(code, str):
            return False
        try:
            entity = self._validate_entity_parameter(entity)
        except BackendGenerationError as e:
            logger.warning(
                f"BackendSWEA: Entity validation failed in _verify_api_code_completeness: {e}"
            )
            return False
        if not code or len(code.strip()) < 200:
            return False
        required_patterns = [
            "from fastapi import",
            "APIRouter",
            f"class {entity}",
            "def create_",
            "def get_",
            "def update_",
            "def delete_",
            "def list_",
            "@router.post",
            "@router.get",
            "@router.put",
            "@router.delete",
        ]
        for pattern in required_patterns:
            if pattern not in code:
                logger.debug(f"Missing required pattern in API code: {pattern}")
                return False
        return True

    def _generate_template_api_code(self, entity: str, attributes: List[str]) -> str:
        """Generate standards-compliant template API code using BackendStandards"""
        # Import the standards
        from baes.standards.backend_standards import BackendStandards

        # CRITICAL FIX: Use centralized validation to prevent 'str' object has no attribute 'lower()' error
        try:
            entity = self._validate_entity_parameter(entity)
            attributes = self._validate_attributes_parameter(attributes)
        except BackendGenerationError as e:
            logger.error(
                f"BackendSWEA: Parameter validation failed in _generate_template_api_code: {e}"
            )
            raise

        entity_lower = entity.lower()
        entity_plural = f"{entity_lower}s"

        # Parse attributes to create model fields
        model_fields = []
        for attr in attributes:
            if ":" in attr:
                field_name, field_type = attr.split(":", 1)
                field_name = field_name.strip()
                field_type = field_type.strip()
                model_fields.append(f"    {field_name}: {field_type}")
            else:
                # Fallback for malformed attributes
                model_fields.append(f"    {attr.strip()}: str")
        fields_str = "\n".join(model_fields)

        # Get standards-compliant imports
        standards = BackendStandards()
        required_imports = [
            standards.REQUIRED_IMPORTS["fastapi_core"],
            standards.REQUIRED_IMPORTS["pydantic"],
            standards.REQUIRED_IMPORTS["typing"],
            standards.REQUIRED_IMPORTS["database"],
            standards.REQUIRED_IMPORTS["pathlib"],
            standards.REQUIRED_IMPORTS["context_manager"],
            standards.REQUIRED_IMPORTS["logging"],
        ]
        imports_section = "\n".join(required_imports)

        # Generate standards-compliant database connection patterns
        db_patterns = standards.DATABASE_PATTERNS
        context_manager_code = f"""
# Database connection with context manager pattern (BackendStandards compliant)
{db_patterns['context_manager_decorator']}
def get_db_connection():
    \"\"\"Database connection context manager for proper resource management\"\"\"
    {db_patterns['connection_setup'][0]}
    {db_patterns['connection_setup'][1]}
    {db_patterns['connection_setup'][2]}
    {db_patterns['connection_setup'][3]}
    {db_patterns['exception_handling'][0]}
        {db_patterns['exception_handling'][1]}
    {db_patterns['exception_handling'][2]}
        {db_patterns['exception_handling'][3]}
        {db_patterns['exception_handling'][4]}
    {db_patterns['exception_handling'][5]}
        {db_patterns['exception_handling'][6]}

# Database dependency for FastAPI
def get_db():
    \"\"\"FastAPI dependency for database connection\"\"\"
    {db_patterns['dependency_function'][1]}
        {db_patterns['dependency_function'][2]}
"""

        # Generate standards-compliant HTTP status codes
        status_codes = standards.HTTP_STATUS_CODES
        delete_decorator = status_codes["DELETE"]["usage"]
        delete_return = status_codes["DELETE"]["return_pattern"]

        # Generate standards-compliant error handling
        error_patterns = standards.ERROR_HANDLING["database_operations"]["pattern"]
        error_handling_create = f"""
        {error_patterns[0]}
            cursor = db.cursor()
            # Extract fields for insertion
            fields = {entity_lower}_data.dict()
            field_names = ', '.join(fields.keys())
            placeholders = ', '.join(['?' for _ in fields])
            values = list(fields.values())
            
            cursor.execute(
                f"INSERT INTO {entity_plural} (" + field_names + ") VALUES (" + placeholders + ")",
                values
            )
            {error_patterns[2]}
            
            # Get the created record
            {entity_lower}_id = cursor.lastrowid
            cursor.execute(f"SELECT * FROM {entity_plural} WHERE id = ?", ({entity_lower}_id,))
            row = cursor.fetchone()
            
            return {entity}Response(id={entity_lower}_id, **dict(row))
            
        {error_patterns[3]}
            {error_patterns[4]}
        {error_patterns[5]}
            {error_patterns[6]}
            {error_patterns[7]}
            {error_patterns[8]}"""

        # Generate complete standards-compliant code
        template_code = f'''{imports_section}

logger = logging.getLogger(__name__)
{context_manager_code}

# Pydantic Models (BackendStandards compliant)
class {entity}Base(BaseModel):
{fields_str}

class {entity}Create({entity}Base):
    pass

class {entity}Update(BaseModel):
{fields_str}

class {entity}Response({entity}Base):
    id: int
    
    class Config:
        from_attributes = True

# Router
router = APIRouter(prefix="/{entity_plural}", tags=["{entity_plural}"])

@router.post("/", response_model={entity}Response, status_code=status.HTTP_201_CREATED)
async def create_{entity_lower}(
    {entity_lower}_data: {entity}Create, db: sqlite3.Connection = Depends(get_db)) -> {entity}Response:
    """Create a new {entity_lower}"""
{error_handling_create}

@router.get("/", response_model=List[{entity}Response])
async def list_{entity_plural}(db: sqlite3.Connection = Depends(get_db)) -> List[{entity}Response]:
    """List all {entity_plural}"""
    try:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {entity_plural}")
        rows = cursor.fetchall()
        return [{entity}Response(**dict(row)) for row in rows]
        
    except Exception as e:
        logger.error(f"Error listing {entity_plural}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Failed to list {entity_plural}")

@router.get("/{{id}}", response_model={entity}Response)
async def get_{entity_lower}(id: int, db: sqlite3.Connection = Depends(get_db)) -> {entity}Response:
    """Get a specific {entity_lower} by ID"""
    try:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {entity_plural} WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"{entity} not found")
            
        return {entity}Response(**dict(row))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {entity_lower} {{id}}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Failed to get {entity_lower}")

@router.put("/{{id}}", response_model={entity}Response)
async def update_{entity_lower}(
    id: int, {entity_lower}_data: {entity}Update, db: sqlite3.Connection = Depends(get_db)) -> {entity}Response:
    """Update a {entity_lower}"""
    try:
        cursor = db.cursor()
        
        # Check if {entity_lower} exists
        cursor.execute(f"SELECT * FROM {entity_plural} WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"{entity} not found")
        
        # Update fields
        fields = {entity_lower}_data.dict(exclude_unset=True)
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        set_clause = ", ".join([f"{{field}} = ?" for field in fields.keys()])
        values = list(fields.values()) + [id]
        
        cursor.execute(
            f"UPDATE {entity_plural} SET {{set_clause}} WHERE id = ?",
            values
        )
        db.commit()
        
        # Get updated record
        cursor.execute(f"SELECT * FROM {entity_plural} WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        return {entity}Response(**dict(row))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating {entity_lower} {{id}}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Failed to update {entity_lower}")

{delete_decorator}
async def delete_{entity_lower}(id: int, db: sqlite3.Connection = Depends(get_db)) -> Response:
    """Delete a {entity_lower}"""
    try:
        cursor = db.cursor()
        
        # Check if {entity_lower} exists
        cursor.execute(f"SELECT * FROM {entity_plural} WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"{entity} not found")
        
        cursor.execute(f"DELETE FROM {entity_plural} WHERE id = ?", (id,))
        db.commit()
        
        # Return 204 No Content status (BackendStandards requirement)
        {delete_return}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting {entity_lower} {{id}}: {{e}}")
        raise HTTPException(status_code=500, detail=f"Failed to delete {entity_lower}")
'''

        # Validate generated code against standards before returning
        validation_result = BackendStandards.get_backend_validation(template_code, entity)
        if not validation_result["is_valid"]:
            logger.error(f"Generated template code for {entity} failed standards validation:")
            for issue in validation_result["issues"]:
                logger.error(f"  - {issue}")
            # Still return the code, but log the issues for debugging

        return template_code

    # ------------------------------------------------------------------
    # Additional task implementations
    # ------------------------------------------------------------------
    def _generate_requirements(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate requirements.txt for the managed system"""
        try:
            # Validate payload
            if not isinstance(payload, dict):
                raise BackendGenerationError(
                    f"Payload must be a dictionary, received {type(payload)}"
                )
            # Standard requirements for FastAPI + Streamlit system
            requirements_content = """fastapi==0.104.1
uvicorn==0.24.0
streamlit==1.28.1
pydantic==2.5.0
python-dotenv==1.0.0
requests==2.31.0
sqlalchemy==2.0.23
pandas==2.1.4
numpy==1.24.3
"""
            file_path = self._write_requirements_to_managed_system(requirements_content)
            return self.create_success_response(
                "generate_requirements",
                {
                    "file_path": file_path,
                    "requirements": requirements_content,
                    "managed_system": True,
                },
            )
        except Exception as e:
            return self.create_error_response("generate_requirements", str(e), "execution_error")

    def _fix_backend_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix backend issues based on error analysis"""
        try:
            # Validate payload
            if not isinstance(payload, dict):
                raise BackendGenerationError(
                    f"Payload must be a dictionary, received {type(payload)}"
                )
            error_analysis = payload.get("error_analysis", {})
            if not isinstance(error_analysis, dict):
                raise BackendGenerationError(
                    f"Error analysis must be a dictionary, received {type(error_analysis)}"
                )
            # Analyze the error and determine fix strategy
            fix_context = self._analyze_dependencies(payload, error_analysis)
            # Apply fixes based on analysis
            if fix_context.get("missing_dependencies"):
                # Generate requirements if dependencies are missing
                return self._generate_requirements(payload)
            elif fix_context.get("api_issues"):
                # Regenerate API if there are API-related issues
                return self._generate_api(payload)
            else:
                # Default to API regeneration
                return self._generate_api(payload)
        except Exception as e:
            return self.create_error_response("fix_backend_issues", str(e), "execution_error")

    def _analyze_dependencies(
        self, payload: Dict[str, Any], fix_context: Dict[str, Any]
    ) -> List[str]:
        """Analyze dependencies and return missing ones"""
        try:
            # Validate parameters
            if not isinstance(payload, dict):
                raise BackendGenerationError(
                    f"Payload must be a dictionary, received {type(payload)}"
                )
            if not isinstance(fix_context, dict):
                raise BackendGenerationError(
                    f"Fix context must be a dictionary, received {type(fix_context)}"
                )
            stderr = fix_context.get("stderr", "")
            if not isinstance(stderr, str):
                stderr = str(stderr)
            return self._extract_missing_dependencies(stderr)
        except Exception as e:
            logger.error(f"BackendSWEA: Failed to analyze dependencies: {str(e)}")
            return []

    def _extract_missing_dependencies(self, stderr: str) -> List[str]:
        """Extract missing dependencies from stderr output"""
        if not isinstance(stderr, str):
            return []
        missing_deps = []
        stderr_lower = stderr.lower()
        # Common dependency patterns
        dependency_patterns = {
            "fastapi": "fastapi",
            "uvicorn": "uvicorn",
            "pydantic": "pydantic",
            "sqlalchemy": "sqlalchemy",
            "pandas": "pandas",
            "numpy": "numpy",
            "streamlit": "streamlit",
        }
        for pattern, dep in dependency_patterns.items():
            if (
                f"no module named '{pattern}'" in stderr_lower
                or f"import {pattern}" in stderr_lower
            ):
                missing_deps.append(dep)
        return missing_deps

    def _build_requirements_content(self, dependencies: List[str]) -> str:
        """Build requirements.txt content from dependency list"""
        if not isinstance(dependencies, list):
            dependencies = []
        # Default requirements
        default_requirements = [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "streamlit==1.28.1",
            "pydantic==2.5.0",
            "python-dotenv==1.0.0",
            "requests==2.31.0",
            "sqlalchemy==2.0.23",
        ]
        # Add any additional dependencies
        for dep in dependencies:
            if dep not in [req.split("==")[0] for req in default_requirements]:
                default_requirements.append(f"{dep}==latest")
        return "\n".join(default_requirements)

    def _write_requirements_to_managed_system(self, content: str) -> str:
        """Write requirements.txt to managed system"""
        if not isinstance(content, str):
            raise BackendGenerationError(f"Content must be a string, received {type(content)}")
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()
        # Write requirements.txt
        requirements_path = self.managed_system_manager.managed_system_path / "requirements.txt"
        requirements_path.write_text(content)
        return str(requirements_path)

    def _apply_backend_improvements(
        self, interpretation: Dict[str, Any], entity: str, code_type: str, context: str
    ) -> str:
        """Apply the interpreted improvements to the backend code generation"""
        # CRITICAL FIX: Ensure entity is a valid string before any operations
        try:
            entity = self._validate_entity_parameter(entity)
        except BackendGenerationError as e:
            logger.error(
                f"BackendSWEA: Entity validation failed in _apply_backend_improvements: {e}"
            )
            raise BackendGenerationError(f"Invalid entity parameter: {e}")
        code_type = str(code_type).strip()
        context = str(context).strip()
        if not isinstance(interpretation, dict):
            logger.error(
                f"BackendSWEA: Interpretation must be a dictionary, received {type(interpretation)}"
            )
            raise BackendGenerationError(f"Invalid interpretation type: {type(interpretation)}")
        # Extract feedback section for prompt template
        feedback_section = interpretation.get("feedback_section", "")
        if not feedback_section:
            # Create a basic feedback section if none provided
            feedback_section = "Generate complete, working FastAPI routes with proper error handling and database integration."
        # Extract attributes from interpretation
        attributes = interpretation.get("attributes", [])
        if not isinstance(attributes, list):
            logger.error(f"BackendSWEA: attributes must be a list, received {type(attributes)}")
            attributes = []
        # Validate attributes
        try:
            attributes = self._validate_attributes_parameter(attributes)
        except BackendGenerationError as e:
            logger.error(f"BackendSWEA: Attribute validation failed: {e}")
            raise
        # Build enhanced prompt with structured feedback
        prompt = self._build_prompt(
            entity=entity,
            attributes=attributes,
            code_type=code_type,
            context=context,
            feedback_section=feedback_section,
        )
        logger.debug(
            f"BackendSWEA: Generating {code_type} for {entity} with {len(attributes)} attributes and feedback integration"
        )
        try:
            # Generate code using LLM with enhanced prompt
            response = self.llm_client.generate_response(
                prompt=prompt,
                system_prompt=f"You are a BackendSWEA agent generating {code_type} for {entity}. Implement ALL TechLeadSWEA feedback exactly as specified.\n\n{self._get_do_not_ignore_warning()}",
            )
            if not response or len(response.strip()) < 100:
                raise BackendGenerationError(f"Generated code too short or empty for {entity}")
            # Extract code from response (remove any markdown formatting)
            code = self._extract_code_from_response(response)
            if not code or len(code.strip()) < 100:
                raise BackendGenerationError(f"Extracted code too short for {entity}")
            logger.info(
                f"✅ BackendSWEA: Successfully generated {code_type} for {entity} with feedback integration"
            )
            return code
        except Exception as e:
            logger.error(f"❌ BackendSWEA: Failed to generate {code_type} for {entity}: {str(e)}")
            raise BackendGenerationError(f"Code generation failed for {entity}: {str(e)}") from e

    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from LLM response, removing markdown formatting and explanations."""
        if not response or not isinstance(response, str):
            return ""
        # Remove markdown code blocks
        lines = response.split("\n")
        code_lines = []
        in_code_block = False
        for line in lines:
            # Check for code block markers
            if line.strip().startswith("```"):
                if "python" in line.lower():
                    in_code_block = True
                else:
                    in_code_block = not in_code_block
                continue
            # If we're in a code block or the line looks like code, include it
            if in_code_block or (line.strip() and not line.strip().startswith("#")):
                code_lines.append(line)
        # If no code block found, assume the entire response is code
        if not code_lines:
            code_lines = [
                line for line in lines if line.strip() and not line.strip().startswith("#")
            ]
        return "\n".join(code_lines).strip()

    def _get_do_not_ignore_warning(self) -> str:
        """
        Generate standard 'Do Not Ignore' warning text for all LLM prompts.
        Stage 1 Improvement #10: Explicit warnings to prevent LLM from ignoring instructions.
        """
        return """
🚨 CRITICAL WARNING: If you ignore ANY of the following instructions,
     your output will be REJECTED and you will be required to regenerate it. You MUST address EVERY requirement listed below. Failure to comply will result in immediate rejection.
⚠️  DO NOT IGNORE ANY INSTRUCTIONS - Your response will be validated against ALL requirements.
⚠️  DO NOT SKIP ANY STEPS - Every instruction must be implemented exactly as specified.
⚠️  DO NOT USE PLACEHOLDERS - Generate complete, working code with no TODO comments.
⚠️  DO NOT OMIT ERROR HANDLING - Implement comprehensive error handling as required.
⚠️  DO NOT IGNORE FEEDBACK - Implement ALL TechLeadSWEA feedback exactly as provided.
COMPLIANCE IS MANDATORY - Non-compliance will result in immediate rejection and retry.
"""
