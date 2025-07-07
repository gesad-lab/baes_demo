import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import os

from baes.core.managed_system_manager import ManagedSystemManager
from baes.domain_entities.base_bae import BaseAgent
from baes.llm.openai_client import OpenAIClient
from baes.utils.llm_request_logger import LLMRequestLogger, RequestType
from config import Config

logger = logging.getLogger(__name__)


# Stage 2 Improvement #8: Feedback Loop Analytics for FrontendSWEA
class FeedbackLoopAnalytics:
    """
    Stage 2 Improvement #8: Feedback Loop Logging and Analytics
    Tracks all feedback interactions between TechLeadSWEA and FrontendSWEA in CSV format.
    """

    def __init__(self):
        # Use tests/.temp for analytics during tests
        if Config.IS_TEST_ENVIRONMENT:
            self.analytics_dir = Path("tests/.temp")
        else:
            self.analytics_dir = Path("logs/feedback_analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.analytics_dir / "frontend_feedback_analytics.csv"
        self._ensure_csv_headers()

    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for pandas DataFrame compatibility"""
        if not self.csv_file.exists():
            headers = [
                "timestamp",
                "session_id",
                "entity",
                "feedback_round",
                "techlead_feedback_count",
                "feedback_categories",
                "frontend_response_time_seconds",
                "feedback_addressed",
                "retry_count",
                "final_success",
                "feedback_text_length",
                "ui_changes_made",
                "improvement_areas",
            ]
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def log_feedback_interaction(
        self,
        session_id: str,
        entity: str,
        feedback_round: int,
        techlead_feedback: List[str],
        frontend_response_time: float,
        feedback_addressed: bool,
        retry_count: int,
        final_success: bool,
        ui_changes_made: List[str] = None,
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
                feedback_round,
                len(techlead_feedback),
                ";".join(feedback_categories),
                round(frontend_response_time, 2),
                feedback_addressed,
                retry_count,
                final_success,
                sum(len(fb) for fb in techlead_feedback),
                ";".join(ui_changes_made or []),
                ";".join(improvement_areas),
            ]

            with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

            logger.info(
                f"\U0001F4CA Frontend feedback analytics logged: {entity} round {feedback_round}"
            )

        except Exception as e:
            logger.warning(f"Failed to log frontend feedback analytics: {e}")

    def _categorize_feedback(self, feedback_list: List[str]) -> List[str]:
        """Categorize feedback for analytics purposes"""
        categories = set()
        feedback_text = " ".join(feedback_list).lower()

        # UI/UX feedback
        if any(term in feedback_text for term in ["ui", "interface", "user", "streamlit", "form"]):
            categories.add("ui_ux")

        # Data display feedback
        if any(
            term in feedback_text
            for term in ["dataframe", "display", "table", "chart", "visualization"]
        ):
            categories.add("data_display")

        # Navigation feedback
        if any(
            term in feedback_text for term in ["navigation", "menu", "sidebar", "page", "routing"]
        ):
            categories.add("navigation")

        # Input/Form feedback
        if any(
            term in feedback_text for term in ["input", "form", "validation", "field", "button"]
        ):
            categories.add("input_forms")

        # Styling feedback
        if any(term in feedback_text for term in ["style", "color", "layout", "design", "css"]):
            categories.add("styling")

        return list(categories) if categories else ["general"]

    def _extract_improvement_areas(self, feedback_list: List[str]) -> List[str]:
        """Extract specific improvement areas from feedback"""
        areas = set()
        feedback_text = " ".join(feedback_list).lower()

        if "usability" in feedback_text:
            areas.add("usability")
        if "accessibility" in feedback_text:
            areas.add("accessibility")
        if "responsive" in feedback_text:
            areas.add("responsive_design")
        if "performance" in feedback_text:
            areas.add("performance")
        if "validation" in feedback_text:
            areas.add("form_validation")

        return list(areas) if areas else ["user_experience"]


class FrontendSWEA(BaseAgent):
    """SWEA responsible for generating Streamlit UI code for domain entities."""

    def __init__(self):
        super().__init__("FrontendSWEA", "UI Generation Agent", "SWEA")
        self.llm_client = OpenAIClient()
        self._managed_system_manager = None  # Lazy initialization
        # Stage 2 Improvement #8: Feedback Loop Analytics
        self.feedback_analytics = FeedbackLoopAnalytics()
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Add LLM request logging
        self.llm_logger = LLMRequestLogger("FrontendSWEA")

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

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

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "generate_ui": "_generate_ui",
        "generate_forms": "_generate_forms",
        "generate_dashboard": "_generate_dashboard",
        "generate_streamlit_app": "_generate_streamlit_app",
        "fix_issues": "_fix_frontend_issues",
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle frontend SWEA tasks. Always use the full attribute list from the payload."""
        attributes = payload.get("attributes")
        if not attributes or not isinstance(attributes, list):
            raise ValueError("FrontendSWEA requires a non-empty attribute list in the payload.")
        for attr in attributes:
            if not isinstance(attr, dict) or "name" not in attr or "type" not in attr:
                raise ValueError(f"Invalid attribute format in FrontendSWEA: {attr}")

        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                f"Unknown task. Supported tasks: {list(self._SUPPORTED_TASKS.keys())}",
                "invalid_task",
            )

        method_name = self._SUPPORTED_TASKS[task]
        method = getattr(self, method_name)
        return method(payload)

    def _build_prompt(self, entity: str, attributes: List[str], context: str) -> str:
        """Build comprehensive prompt for UI generation"""
        # Parse attributes to handle different formats
        parsed_attributes = []
        for attr in attributes:
            if isinstance(attr, str):
                if ":" in attr:
                    name, attr_type = attr.split(":", 1)
                    parsed_attributes.append({"name": name.strip(), "type": attr_type.strip()})
                else:
                    parsed_attributes.append({"name": attr.strip(), "type": "str"})
            elif isinstance(attr, dict):
                parsed_attributes.append(attr)
            else:
                parsed_attributes.append({"name": str(attr), "type": "str"})

        # Build form fields section - exclude 'id' field as it should be auto-generated
        form_fields = []
        for attr in parsed_attributes:
            field_name = attr["name"]
            field_type = attr["type"].lower()

            # Skip the 'id' field - it should be auto-generated, not user-editable
            if field_name.lower() == "id":
                continue

            if field_type in ["email"]:
                form_fields.append(
                    f'    {field_name} = st.text_input("{field_name.title()}", key="{field_name}_input")'
                )
            elif field_type in ["int", "integer"]:
                form_fields.append(
                    f'    {field_name} = st.number_input("{field_name.title()}", min_value=0, key="{field_name}_input")'
                )
            elif field_type in ["date"]:
                form_fields.append(
                    f'    {field_name} = st.date_input("{field_name.title()}", key="{field_name}_input")'
                )
            else:
                form_fields.append(
                    f'    {field_name} = st.text_input("{field_name.title()}", key="{field_name}_input")'
                )

        # Build validation logic - exclude 'id' field
        validation_rules = []
        for attr in parsed_attributes:
            field_name = attr["name"]
            field_type = attr["type"].lower()

            # Skip the 'id' field - it should be auto-generated, not validated by user
            if field_name.lower() == "id":
                continue

            if field_type == "email":
                validation_rules.append(f'    if {field_name} and "@" not in {field_name}:')
                validation_rules.append('        st.error("Please enter a valid email address")')
                validation_rules.append("        return")
            else:
                validation_rules.append(f"    if not {field_name}:")
                validation_rules.append(f'        st.error("{field_name.title()} is required")')
                validation_rules.append("        return")

        # Build data dictionary - exclude 'id' field
        data_dict_parts = []
        for attr in parsed_attributes:
            field_name = attr["name"]
            # Skip the 'id' field - it should be auto-generated, not sent in create requests
            if field_name.lower() == "id":
                continue
            data_dict_parts.append(f'"{field_name}": {field_name}')
        data_dict = "{" + ", ".join(data_dict_parts) + "}"

        # Build display columns
        display_columns = []
        for attr in parsed_attributes:
            field_name = attr["name"]
            display_columns.append(f'st.write(f"**{field_name.title()}:** {{{field_name}}}")')

        # Entity lowercase for API endpoints
        entity_lower = entity.lower()

        # Stage 4 Improvement #1: Get structured feedback injection
        structured_feedback = self._get_structured_feedback_injection(entity, "FrontendSWEA", "generate_ui")

        prompt = f"""
{self._get_do_not_ignore_warning()}

You are a FrontendSWEA agent specialized in generating Streamlit UI code for domain entity management.

{structured_feedback}

CRITICAL REQUIREMENTS - Your code MUST include ALL of the following:

1. **MANDATORY: NO st.set_page_config() in entity pages**
   - Entity pages are imported into the main app, which already has st.set_page_config()
   - Do NOT include st.set_page_config() in entity management pages

2. **MANDATORY: API_BASE_URL configuration**
   - Define: API_BASE_URL = f"http://localhost:{{os.getenv('REALWORLD_FASTAPI_PORT', '8000')}}"
   - Use this constant for all API calls
   - Import os at the top of the file

3. **MANDATORY: Proper error handling with response.raise_for_status()**
   - Add response.raise_for_status() after every API call
   - Wrap all API calls in try/except blocks

4. **MANDATORY: Complete CRUD functionality**
   - Create: POST to /api/{entity_lower}s/ with "Add New {entity}" form
   - Read: GET from /api/{entity_lower}s/ with "List {entity}s" display
   - Update: PUT to /api/{entity_lower}s/{{id}} with "Edit {entity}" form
   - Delete: DELETE to /api/{entity_lower}s/{{id}} with delete buttons

5. **MANDATORY: Form validation and error messages**
   - Validate all required fields
   - Show st.error() messages for validation failures

6. **MANDATORY: Proper imports**
   - import os
   - import streamlit as st
   - import requests
   - from typing import List, Dict, Any, Optional

7. **CRITICAL: ID field handling**
   - NEVER include 'id' field in create/update forms (it's auto-generated)
   - NEVER include 'id' in data dictionaries sent to API
   - Display 'id' as read-only text in edit forms only
   - The 'id' field should NEVER be user-editable

Entity: {entity}
Attributes: {attributes}
Context: {context}

Generate complete Streamlit UI code with CRUD operations:
- List {entity}s tab with requests.get() and display
- Add New {entity} tab with st.form() and requests.post()
- Edit {entity} tab with pre-populated form and requests.put()
- Delete buttons with requests.delete()

CRITICAL OUTPUT FORMAT:
- Return ONLY pure Python code
- DO NOT use markdown code blocks (```python or ```)
- DO NOT include any explanations or comments outside the code
- Start directly with import statements
- Include complete CRUD functionality
- Use proper error handling with response.raise_for_status()
- NEVER include 'id' field in forms or data dictionaries
"""
        return prompt

    def _write_to_managed_system(self, entity: str, code: str) -> str:
        """Write generated UI code to managed system"""
        try:
            file_path = self.managed_system_manager.write_entity_artifact(entity, "ui", code)
            logger.info(f"✅ FrontendSWEA: UI code written to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"❌ FrontendSWEA: Failed to write UI code: {e}")
            raise

    def _validate_interpretation_structure(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize interpretation structure"""
        # Ensure required fields exist
        required_fields = ["ui_improvements", "form_fields", "validation_rules", "api_integration"]
        for field in required_fields:
            if field not in interpretation:
                interpretation[field] = {}

        # Normalize nested structures
        if "ui_improvements" not in interpretation:
            interpretation["ui_improvements"] = {}
        if "form_fields" not in interpretation:
            interpretation["form_fields"] = []
        if "validation_rules" not in interpretation:
            interpretation["validation_rules"] = []
        if "api_integration" not in interpretation:
            interpretation["api_integration"] = {}

        return interpretation

    def _interpret_feedback_for_ui_generation(
        self, feedback: List[str], entity: str, original_attributes: List[str]
    ) -> Dict[str, Any]:
        """
        Interpret TechLeadSWEA feedback for UI generation using LLM.
        This replaces template-based feedback interpretation with LLM-based understanding.
        """
        try:
            # Build comprehensive prompt for feedback interpretation
            # Removed unused variable feedback_text

            prompt = """
{self._get_do_not_ignore_warning()}

You are a FrontendSWEA agent interpreting TechLeadSWEA feedback for UI generation.

Entity: {entity}
Original Attributes: {original_attributes}

TechLeadSWEA Feedback:
{feedback_text}

Your task is to interpret this feedback and provide specific improvements for UI generation.

CRITICAL REQUIREMENTS:
1. **MANDATORY: st.set_page_config() at the beginning of the file**
2. **MANDATORY: API_BASE_URL configuration**
3. **MANDATORY: Proper error handling with response.raise_for_status()**
4. **MANDATORY: Complete CRUD functionality**
5. **MANDATORY: Form validation and error messages**
6. **MANDATORY: Proper imports including typing**

Analyze the feedback and provide specific improvements. Focus on:
- Missing UI components (st.set_page_config, API_BASE_URL, etc.)
- Form validation and error handling
- API integration patterns
- User experience improvements

Return ONLY a JSON object with the following structure:
{{
    "ui_improvements": {{
        "missing_components": ["list of missing UI components"],
        "required_patterns": ["list of required patterns"],
        "user_experience": ["list of UX improvements"]
    }},
    "form_fields": [
        {{"name": "field_name", "type": "field_type", "validation": "validation_rule"}}
    ],
    "validation_rules": [
        "specific validation rules to implement"
    ],
    "api_integration": {{
                        "base_url": "API_BASE_URL = \"http://localhost:8100\"",
        "endpoints": {{
            "list": "/api/{entity.lower()}s/",
            "create": "/api/{entity.lower()}s/",
            "update": "/api/{entity.lower()}s/{{id}}",
            "delete": "/api/{entity.lower()}s/{{id}}"
        }},
        "error_handling": ["specific error handling requirements"]
    }}
}}

CRITICAL: Return ONLY the JSON object, no markdown formatting or explanations.
"""

            # Log the request for debugging and research
            request_id = self.llm_logger.log_request(
                agent_name="FrontendSWEA",
                request_type=RequestType.INTERPRETATION,
                entity=entity,
                task="interpret_feedback",
                prompt=prompt,
                context={
                    "attributes": original_attributes,
                    "feedback": feedback,
                    "entity": entity,
                },
                retry_count=0,
                session_id=self.current_session_id,
            )

            # Use the new JSON enforcement functionality
            json_schema = {
                "ui_improvements": {
                    "missing_components": ["list of missing components"],
                    "required_patterns": ["list of required patterns"],
                    "user_experience": ["list of UX improvements"]
                },
                "form_fields": ["list of form field objects"],
                "validation_rules": ["list of validation rules"],
                "api_integration": {
                    "base_url": "string",
                    "endpoints": {},
                    "error_handling": ["list of error handling patterns"]
                }
            }

            fallback_schema = {
                "ui_improvements": {
                    "missing_components": [],
                    "required_patterns": [],
                    "user_experience": []
                },
                "form_fields": [],
                "validation_rules": [],
                "api_integration": {
                    "base_url": 'API_BASE_URL = "http://localhost:8000"',
                    "endpoints": {},
                    "error_handling": []
                },
                "error": True
            }

            interpretation = self.llm_client.generate_json_response(
                prompt=prompt,
                json_schema=json_schema,
                fallback_schema=fallback_schema
            )

            # Validate and normalize interpretation structure
            interpretation = self._validate_interpretation_structure(interpretation)

            logger.info(f"✅ FrontendSWEA: Feedback interpretation completed for {entity}")
            return interpretation

        except Exception as e:
            logger.error(f"❌ FrontendSWEA: Feedback interpretation failed: {e}")
            # Do not return a fallback. Raise an error to make failure explicit.
            raise FrontendGenerationError(f"Failed to interpret feedback for UI generation: {e}") from e

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
                    f"📤 FrontendSWEA: Retrieved structured feedback for {entity}.{swea_agent}.{task_type}"
                )
                return structured_instructions
            else:
                logger.debug(
                    f"📤 FrontendSWEA: No structured feedback available for {entity}.{swea_agent}.{task_type}"
                )
                return ""
        except Exception as e:
            logger.warning(f"FrontendSWEA: Failed to get structured feedback injection: {str(e)}")
            return ""

    def _extract_ui_improvements_from_text(
        self, response_text: str, original_attributes: List[str]
    ) -> Dict[str, Any]:
        """Extract UI improvements from LLM response text (fallback method)"""
        improvements = {
            "ui_improvements": {
                "missing_components": [],
                "required_patterns": [],
                "user_experience": [],
            },
            "form_fields": [],
            "validation_rules": [],
            "api_integration": {
                "base_url": 'API_BASE_URL = "http://localhost:8000"',
                "endpoints": {},
                "error_handling": [],
            },
        }

        # NOTE: st.set_page_config is NOT required in entity pages as they are imported into main app

        if "API_BASE_URL" not in response_text:
            improvements["ui_improvements"]["missing_components"].append("API_BASE_URL")

        if "raise_for_status" not in response_text:
            improvements["ui_improvements"]["required_patterns"].append("response.raise_for_status")

        return improvements

    def _apply_ui_improvements(
        self, interpretation: Dict[str, Any], entity: str, context: str
    ) -> str:
        """Apply interpreted improvements to generate improved UI code"""
        try:
            # Build improved prompt based on interpretation
            improvements = interpretation.get("ui_improvements", {})
            missing_components = improvements.get("missing_components", [])
            required_patterns = improvements.get("required_patterns", [])

            # Create attributes list for the prompt
            attributes = []
            for field in interpretation.get("form_fields", []):
                if isinstance(field, dict):
                    attributes.append(f"{field.get('name', 'field')}:{field.get('type', 'str')}")
                else:
                    attributes.append(str(field))

            if not attributes:
                # Fallback to basic attributes if none provided
                # attributes = ["name:str", "email:str"]
                # NO FALLBACK: If no attributes are found after interpretation, it's an error.
                raise FrontendGenerationError(
                    "No attributes were found in the feedback interpretation. Cannot generate UI."
                )

            # Build the improved prompt
            prompt = self._build_prompt(entity, attributes, context)

            # Add specific improvement instructions
            if missing_components:
                prompt += "\n\nSPECIFIC IMPROVEMENTS REQUIRED:\n"
                for component in missing_components:
                    prompt += f"- MUST include: {component}\n"

            if required_patterns:
                prompt += "\nREQUIRED PATTERNS:\n"
                for pattern in required_patterns:
                    prompt += f"- MUST implement: {pattern}\n"

            # Log the request for debugging and research
            request_id = self.llm_logger.log_request(
                agent_name="FrontendSWEA",
                request_type=RequestType.CODE_GENERATION,
                entity=entity,
                task="generate_ui_code",
                prompt=prompt,
                context={
                    "attributes": attributes,
                    "entity": entity,
                    "context": context,
                },
                retry_count=0,
                session_id=self.current_session_id,
            )

            # Make LLM request
            response_text = self.llm_client.generate_response(prompt)

            # Log the response
            self.llm_logger.log_response(
                request_id=request_id,
                response_text=response_text,
                success=True,
                response_time_ms=0.0,  # TODO: Add actual timing
                model_used="gpt-4o-mini",
            )

            if not response_text:
                logger.error("❌ FrontendSWEA: LLM request failed - empty response")
                raise FrontendGenerationError("LLM request failed - empty response")

            # Clean LLM response to remove markdown formatting (DRY principle)
            code = self._clean_llm_response(response_text)

            # Sanitize unsupported Streamlit arguments
            code = self._sanitize_ui_code(code)

            # NOTE: st.set_page_config is NOT required in entity pages as they are imported into main app

            if "API_BASE_URL" not in code:
                logger.warning("Generated code missing API_BASE_URL, adding it")
                code = code.replace(
                    "import streamlit as st",
                    'import streamlit as st\n\nAPI_BASE_URL = "http://localhost:8000"',
                )

            logger.info(f"✅ FrontendSWEA: UI code generation completed for {entity}")
            return code

        except Exception as e:
            logger.error(f"❌ FrontendSWEA: UI improvement application failed: {e}")
            raise FrontendGenerationError(f"UI improvement application failed: {e}")

    def _generate_ui(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Streamlit UI code for entity management"""
        try:
            entity = payload.get("entity", "Student")
            attributes = payload.get("attributes", [])
            context = payload.get("context", "academic")

            # CRITICAL: Check for attribute constraints from BAE coordination plan
            use_only_specified = payload.get("use_only_specified_attributes", False)
            do_not_add_extra = payload.get("do_not_add_extra_fields", False)
            attribute_constraints = payload.get("attribute_constraints", {})
            
            logger.info(f"🎯 FrontendSWEA: Processing {entity} UI with {len(attributes)} attributes")
            logger.info(f"🚨 UI constraint mode: use_only_specified={use_only_specified}")
            if use_only_specified:
                logger.info(f"🔒 UI STRICT MODE: Using ONLY the {len(attributes)} user-specified attributes")
                logger.info(f"📝 UI Specified attributes: {[attr.get('name', str(attr)) for attr in attributes]}")

            # Extract feedback information from payload
            techlead_feedback = payload.get("techlead_feedback", [])
            previous_errors = payload.get("previous_errors", [])
            expected_output = payload.get("expected_output", "")

            # Combine all feedback sources
            all_feedback = []
            if techlead_feedback:
                all_feedback.extend(
                    techlead_feedback
                    if isinstance(techlead_feedback, list)
                    else [techlead_feedback]
                )
            if previous_errors:
                all_feedback.extend(
                    previous_errors if isinstance(previous_errors, list) else [previous_errors]
                )
            if expected_output:
                all_feedback.append(f"Expected output: {expected_output}")

            if use_only_specified or attribute_constraints.get("use_only_specified_attributes"):
                # STRICT MODE: Skip LLM feedback interpretation and use exact attributes for UI
                logger.info(f"🔒 UI STRICT MODE: Bypassing LLM feedback interpretation, using exact user attributes")
                
                # Parse attributes to structured list - CRITICAL: Use exact attributes from payload
                parsed_attributes = self._parse_attributes(attributes)
                
                # Validate that we're using the exact attributes provided
                logger.info(f"🔍 FrontendSWEA STRICT: Using exact attributes: {parsed_attributes}")
                
                # Build Streamlit UI code based on exact attributes (DRY template)
                code = self._create_streamlit_ui_code(entity, parsed_attributes, context)

                # Sanitize unsupported Streamlit arguments (template shouldn't produce, but keep safe)
                code = self._sanitize_ui_code(code)
            
            # Check if we have feedback and we're NOT in strict mode
            elif all_feedback:
                logger.info(f"🔧 FrontendSWEA: Interpreting feedback for {entity}")
                interpretation = self._interpret_feedback_for_ui_generation(
                    all_feedback, entity, attributes
                )
                code = self._apply_ui_improvements(interpretation, entity, context)
            else:
                # Generate fresh UI code using internal template generator (deterministic)
                logger.info(
                    f"🎨 FrontendSWEA: Generating fresh UI code for {entity} using template generator"
                )

                # Parse attributes to structured list - CRITICAL: Use exact attributes from payload
                parsed_attributes = self._parse_attributes(attributes)
                
                # Validate that we're using the exact attributes provided
                logger.info(f"🔍 FrontendSWEA: Using exact attributes: {parsed_attributes}")
                
                # Build Streamlit UI code based on attributes (DRY template)
                code = self._create_streamlit_ui_code(entity, parsed_attributes, context)

                # Sanitize unsupported Streamlit arguments (template shouldn't produce, but keep safe)
                code = self._sanitize_ui_code(code)

            # Write the generated code to the managed system
            file_path = self._write_to_managed_system(entity, code)

            return self.create_success_response(
                "generate_ui",
                {
                    "file_path": file_path,
                    "code": code,
                    "managed_system": True,
                    "quality_mode": "template_generated",
                },
            )

        except Exception as e:
            logger.error(f"❌ FrontendSWEA: UI generation failed: {e}")
            return self.create_error_response("generate_ui", str(e), "generation_error")

    def _generate_ui_code(self, entity: str, attributes: List[str], context: str) -> Dict[str, Any]:
        """Generate Streamlit UI code for entity management"""
        try:
            # Parse attributes
            parsed_attributes = self._parse_attributes(attributes)

            # Generate the UI code
            # Removed unused variable entity_lower

            # Create comprehensive Streamlit UI
            code = self._create_streamlit_ui_code(entity, parsed_attributes, context)

            # Sanitize unsupported Streamlit arguments (template shouldn't produce, but keep safe)
            code = self._sanitize_ui_code(code)

            return {
                "success": True,
                "data": {
                    "code": code,
                    "ui_components": self._extract_ui_components(code),
                    "entity": entity,
                    "attributes": parsed_attributes,
                },
            }

        except Exception as e:
            logger.error(f"❌ FrontendSWEA: Error in UI code generation: {str(e)}")
            return {"success": False, "error": f"UI code generation failed: {str(e)}", "data": {}}

    def _fix_frontend_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix frontend issues based on TechLeadSWEA coordination"""
        try:
            entity = payload.get("entity", "Student")
            fix_action = payload.get("fix_action", "")
            issue_type = payload.get("issue_type", "")
            techlead_decision = payload.get("techlead_decision", {})

            # Extract detailed context from TechLeadSWEA decision
            reasoning = techlead_decision.get("reasoning", "")

            logger.info("🔧 FrontendSWEA: Fixing frontend issues for %s", entity)
            logger.info("   🎯 Fix Action: %s", fix_action)
            logger.info("   📋 Issue Type: %s", issue_type)
            logger.info("   💡 Reasoning: %s", reasoning)

            # Handle specific fix actions from TechLeadSWEA
            if fix_action in ["regenerate_ui_with_functions", "add_missing_streamlit_functions"]:
                logger.debug("🔧 FrontendSWEA: Regenerating UI with missing functions")
                # Add specific feedback about missing functions
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [
                        f"Add missing UI functions: {reasoning}",
                        "Ensure all display_, create_, edit_, delete_ functions are implemented",
                        "Include proper function definitions for all UI operations",
                    ],
                    "fix_focus": "missing_functions",
                }
                return self._generate_ui(enhanced_payload)

            elif fix_action in ["fix_ui_interface", "regenerate_ui"]:
                logger.debug("🔧 FrontendSWEA: Fixing UI interface issues")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix UI interface issues: {reasoning}"],
                    "fix_focus": "interface_issues",
                }
                return self._generate_ui(enhanced_payload)

            # Fallback: Handle by issue type (legacy support)
            elif "ui" in issue_type or "interface" in issue_type or "streamlit" in issue_type:
                logger.debug("🔧 FrontendSWEA: Regenerating UI due to interface issues (legacy)")
                return self._generate_ui(payload)
            elif "form" in issue_type or "input" in issue_type:
                logger.debug("🔧 FrontendSWEA: Fixing form/input issues (legacy)")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix form issues: {reasoning}"],
                }
                return self._generate_ui(enhanced_payload)
            elif "display" in issue_type or "layout" in issue_type:
                logger.debug("🔧 FrontendSWEA: Fixing display/layout issues (legacy)")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix layout issues: {reasoning}"],
                }
                return self._generate_ui(enhanced_payload)
            elif "component" in issue_type or "widget" in issue_type:
                logger.debug("🔧 FrontendSWEA: Fixing component/widget issues (legacy)")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix component issues: {reasoning}"],
                }
                return self._generate_ui(enhanced_payload)
            else:
                # Default: regenerate entire UI with generic fix instructions
                logger.debug(
                    "🔧 FrontendSWEA: Default fix - regenerating UI with generic improvements"
                )
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"General frontend fix needed: {reasoning}"],
                }
                return self._generate_ui(enhanced_payload)

        except Exception as e:
            logger.error("❌ FrontendSWEA fix_issues failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "fix_error")

    def _parse_attributes(self, attributes: List[str]) -> List[Dict[str, str]]:
        """Parse attributes to handle different formats and detect foreign keys"""
        parsed_attributes = []
        for attr in attributes:
            if isinstance(attr, str):
                if ":" in attr:
                    name, attr_type = attr.split(":", 1)
                    attr_dict = {"name": name.strip(), "type": attr_type.strip()}
                else:
                    attr_dict = {"name": attr.strip(), "type": "str"}
            elif isinstance(attr, dict):
                # Ensure a copy so we don't mutate original
                attr_dict = {**attr}
            else:
                attr_dict = {"name": str(attr), "type": "str"}

            # Detect foreign key attributes (e.g., course_id)
            name_lower = attr_dict["name"].lower()
            if name_lower != "id" and name_lower.endswith("_id"):
                related_entity = name_lower[:-3]  # strip _id -> course
                attr_dict["is_foreign_key"] = True
                attr_dict["related_entity"] = related_entity
            else:
                attr_dict["is_foreign_key"] = False

            parsed_attributes.append(attr_dict)
        return parsed_attributes

    def _create_streamlit_ui_code(
        self,
        entity: str,
        attributes: List[Dict[str, str]],
        context: str,
    ) -> str:
        """Create comprehensive Streamlit UI code using DRY template patterns"""
        from baes.standards.frontend_standards import FrontendStandards
        
        # Use DRY principle: Create reusable template components
        template_parts = self._build_ui_template_parts(entity, attributes, context)
        
        # Combine template parts into complete UI code
        ui_code = self._assemble_ui_template(template_parts, entity)
        
        return ui_code

    def _generate_ui_code_directly(
        self, entity: str, attributes: List[Dict[str, str]], context: str
    ) -> str:
        """Generate UI code directly using LLM"""
        prompt = self._build_prompt(
            entity, [f"{attr['name']}:{attr['type']}" for attr in attributes], context
        )

        # Log the request for debugging and research
        request_id = self.llm_logger.log_request(
            agent_name="FrontendSWEA",
            request_type=RequestType.CODE_GENERATION,
            entity=entity,
            task="generate_ui_code",
            prompt=prompt,
            context={
                "attributes": attributes,
                "entity": entity,
                "context": context,
            },
            retry_count=0,
            session_id=self.current_session_id,
        )

        # Make LLM request
        response_text = self.llm_client.generate_response(prompt)

        # Log the response
        self.llm_logger.log_response(
            request_id=request_id,
            response_text=response_text,
            success=True,
            response_time_ms=0.0,  # TODO: Add actual timing
            model_used="gpt-4o-mini",
        )

        if not response_text:
            logger.error("❌ FrontendSWEA: LLM request failed - empty response")
            raise FrontendGenerationError("LLM request failed - empty response")

        # Clean LLM response to remove markdown formatting (DRY principle)
        return self._clean_llm_response(response_text)

    def _extract_ui_components(self, code: str) -> List[str]:
        """Extract UI components from generated code"""
        components = []
        if "st.title" in code:
            components.append("title")
        if "st.form" in code:
            components.append("form")
        if "st.dataframe" in code:
            components.append("dataframe")
        if "st.button" in code:
            components.append("button")
        if "st.tabs" in code:
            components.append("tabs")
        return components

    def _build_ui_template_parts(self, entity: str, attributes: List[Dict[str, str]], context: str) -> Dict[str, str]:
        """Build reusable UI template parts following DRY principles"""
        from baes.standards.frontend_standards import FrontendStandards
        
        entity_lower = entity.lower()
        
        # DRY: Reusable template parts
        template_parts = {
            "imports": self._generate_imports_template(),
            "api_config": self._generate_api_config_template(),
            "form_fields": self._generate_form_fields_template(attributes),
            "validation": self._generate_validation_template(attributes),
            "crud_operations": self._generate_crud_operations_template(entity, entity_lower),
            "main_function": self._generate_main_function_template(entity, attributes),
            "attributes": attributes,
        }
        
        return template_parts
    
    def _generate_imports_template(self) -> str:
        """Generate standard imports template (DRY)"""
        return '''import os
import json
import streamlit as st
import requests
from typing import List, Dict, Any, Optional'''
    
    def _generate_api_config_template(self) -> str:
        """Generate API configuration template (DRY)"""
        return '''# API Configuration
API_PORT = os.getenv("REALWORLD_FASTAPI_PORT", "8000")
API_BASE_URL = f"http://localhost:{API_PORT}"'''
    
    def _generate_form_fields_template(self, attributes: List[Dict[str, str]]) -> str:
        """Generate form fields template based on attributes (DRY) - excludes primary id, builds dropdown for foreign keys"""
        form_fields = []
        for attr in attributes:
            field_name = attr["name"]
            field_type = attr.get("type", "str").lower()
            is_fk = attr.get("is_foreign_key", False)
            related_entity = attr.get("related_entity", "")
            descriptive_field = attr.get("descriptive_field", "name")

            # Skip the primary 'id' field - auto-generated
            if field_name.lower() == "id":
                continue

            if is_fk and related_entity:
                related_entity_lower = related_entity.lower()
                form_fields.append(
                    f"        # Foreign key: {related_entity}\n"
                    f"        try:\n"
                    f"            {related_entity_lower}_resp = requests.get(f'{{API_BASE_URL}}/api/{related_entity_lower}s/')\n"
                    f"            {related_entity_lower}_resp.raise_for_status()\n"
                    f"            {related_entity_lower}_data = {related_entity_lower}_resp.json()\n"
                    f"            {related_entity_lower}_options = {{item['id']: item.get('{descriptive_field}', str(item['id'])) for item in {related_entity_lower}_data}}\n"
                    f"        except (requests.exceptions.RequestException, json.JSONDecodeError):\n"
                    f"            {related_entity_lower}_options = {{}}\n"
                    f"            st.error('Failed to load {related_entity} options')\n"
                    f"        {field_name} = st.selectbox(\"{related_entity.title()}\", options=list({related_entity_lower}_options.keys()), format_func=lambda o: {related_entity_lower}_options.get(o, str(o)))\n"
                )
            else:
                if field_type in ["email"]:
                    form_fields.append(
                        f'        {field_name} = st.text_input("{field_name.title()}", key="{field_name}_input")'
                    )
                elif field_type in ["int", "integer"]:
                    form_fields.append(
                        f'        {field_name} = st.number_input("{field_name.title()}", min_value=0, key="{field_name}_input")'
                    )
                elif field_type in ["date"]:
                    form_fields.append(
                        f'        {field_name} = st.date_input("{field_name.title()}", key="{field_name}_input")'
                    )
                else:
                    form_fields.append(
                        f'        {field_name} = st.text_input("{field_name.title()}", key="{field_name}_input")'
                    )
        return '\n'.join(form_fields)
    
    def _generate_validation_template(self, attributes: List[Dict[str, str]]) -> str:
        """Generate validation template based on attributes (DRY) - excludes id field"""
        validation_rules = []
        for attr in attributes:
            field_name = attr["name"]
            field_type = attr.get("type", "str").lower()
            
            # Skip the 'id' field - it should be auto-generated, not validated by user
            if field_name.lower() == "id":
                continue
            
            if field_type == "email":
                validation_rules.append(f'            if {field_name} and "@" not in {field_name}:')
                validation_rules.append('                st.error("Please enter a valid email address")')
                validation_rules.append("                return")
            else:
                validation_rules.append(f"            if not {field_name}:")
                validation_rules.append(f'                st.error("{field_name.title()} is required")')
                validation_rules.append("                return")
        
        return '\n'.join(validation_rules)
    
    def _generate_crud_operations_template(self, entity: str, entity_lower: str) -> str:
        """Generate CRUD operations template (DRY)"""
        return f'''def create_{entity_lower}(data: Dict[str, Any]) -> bool:
    """Create a new {entity}."""
    try:
        response = requests.post(f"{{API_BASE_URL}}/api/{entity_lower}s/", json=data)
        response.raise_for_status()
        if response.status_code == 201:
            st.success(f"{entity} created successfully!")
            return True
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating {entity_lower}: {{e}}")
        return False

def get_{entity_lower}s() -> List[Dict[str, Any]]:
    """Get all {entity}s."""
    try:
        response = requests.get(f"{{API_BASE_URL}}/api/{entity_lower}s/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {entity_lower}s: {{e}}")
        return []

def update_{entity_lower}(id: int, data: Dict[str, Any]) -> bool:
    """Update an existing {entity}."""
    try:
        response = requests.put(f"{{API_BASE_URL}}/api/{entity_lower}s/{{id}}", json=data)
        response.raise_for_status()
        if response.status_code == 200:
            st.success(f"{entity} updated successfully!")
            return True
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating {entity_lower}: {{e}}")
        return False

def delete_{entity_lower}(id: int) -> bool:
    """Delete a {entity}."""
    try:
        response = requests.delete(f"{{API_BASE_URL}}/api/{entity_lower}s/{{id}}")
        response.raise_for_status()
        if response.status_code == 204:
            st.success(f"{entity} deleted successfully!")
            return True
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting {entity_lower}: {{e}}")
        return False'''
    
    def _generate_main_function_template(self, entity: str, attributes: List[Dict[str, str]]) -> str:
        """Generate main function template (DRY)"""
        entity_lower = entity.lower()

        # Find a descriptive attribute for the expander title
        descriptive_attr = "id"
        for attr in attributes:
            attr_name = attr.get("name", "").lower()
            if attr_name == "name":
                descriptive_attr = attr["name"]
                break
            if attr_name == "title":
                descriptive_attr = attr["name"]
            if attr_name == "description" and descriptive_attr == "id":
                descriptive_attr = attr["name"]

        # Generate code to fetch data for all foreign keys
        fk_fetches = []
        for attr in attributes:
            if attr.get("is_foreign_key"):
                related_entity = attr["related_entity"]
                related_entity_lower = related_entity.lower()
                descriptive_field = attr.get("descriptive_field", "name")
                fk_fetches.append(f'''    # Fetch related data for {related_entity}\n    try:\n        {related_entity_lower}_resp = requests.get(f"{{API_BASE_URL}}/api/{related_entity_lower}s/")\n        {related_entity_lower}_resp.raise_for_status()\n        {related_entity_lower}_data = {related_entity_lower}_resp.json()\n        {related_entity_lower}_options = {{item['id']: item.get('{descriptive_field}', str(item['id'])) for item in {related_entity_lower}_data}}\n    except (requests.exceptions.RequestException, json.JSONDecodeError):\n        {related_entity_lower}_options = {{}}\n        st.warning('Failed to load {related_entity} options')''')
        fk_fetch_block = "\n".join(fk_fetches)

        # Generate the item display logic
        item_display_lines = []
        indent = " " * 20  # 16 (col1) + 4
        for attr in attributes:
            attr_name = attr["name"]
            if attr_name.lower() == 'id':
                continue
            if attr.get("is_foreign_key"):
                related_entity = attr["related_entity"]
                related_entity_lower = related_entity.lower()
                options_map_name = f"{related_entity_lower}_options"
                descriptive_field = attr.get("descriptive_field", "name")
                item_display_lines.append(
                    f"{indent}if '{attr_name}' in {entity_lower}:\n{indent}    related_name = {options_map_name}.get({entity_lower}['{attr_name}'], f'ID: {{{entity_lower}['{attr_name}']}}')\n{indent}    st.write(f'**{related_entity.title()}:** {{related_name}}')"
                )
            else:
                item_display_lines.append(
                    f"{indent}if '{attr_name}' in {entity_lower}:\n{indent}    st.write(f'**{attr_name.replace('_', ' ').title()}:** {{{entity_lower}['{attr_name}']}}')"
                )
        item_display_block = "\n".join(item_display_lines)
        if not item_display_block.strip():
            item_display_block = indent + "pass"

        return f'''def main():
    """Main {entity} management interface."""
    st.title("{entity} Management")
    
    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["List {entity}s", "Add {entity}", "Edit {entity}"])
    
    with tab1:
        show_{entity_lower}_list()
    
    with tab2:
        show_{entity_lower}_form()
    
    with tab3:
        show_{entity_lower}_edit()

def show_{entity_lower}_list():
    """Display list of {entity}s."""
    st.header("All {entity}s")
    
    if st.button("Refresh", key="refresh_list"):
        st.rerun()
    
    {fk_fetch_block}
    
    {entity_lower}s = get_{entity_lower}s()
    
    if {entity_lower}s:
        for {entity_lower} in {entity_lower}s:
            with st.expander(f"{entity.title()}: {{{entity_lower}.get('{descriptive_attr}', {entity_lower}.get('id', 'N/A'))}}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
{item_display_block}
                
                with col2:
                    if st.button("Edit", key=f"edit_{{{entity_lower}['id']}}"):
                        st.session_state.edit_{entity_lower}_id = {entity_lower}['id']
                        st.session_state.edit_{entity_lower}_data = {entity_lower}
                        st.rerun()
                
                with col3:
                    if st.button("Delete", key=f"delete_{{{entity_lower}['id']}}"):
                        if delete_{entity_lower}({entity_lower}['id']):
                            st.rerun()
    else:
        st.info("No {entity_lower}s found.")

def show_{entity_lower}_form():
    """Display form to add new {entity}."""
    st.header("Add New {entity}")
    
    with st.form("add_{entity_lower}_form"):
{{form_fields}}
        
        submitted = st.form_submit_button("Add {entity}")
        
        if submitted:
{{validation}}
            
            # Create data dictionary
            data = {{data_dict}}
            
            if create_{entity_lower}(data):
                st.rerun()

def show_{entity_lower}_edit():
    """Display form to edit existing {entity}."""
    st.header("Edit {entity}")
    
    if f"edit_{entity_lower}_id" in st.session_state:
        edit_data = st.session_state.get(f"edit_{entity_lower}_data", {{}})
        
        with st.form("edit_{entity_lower}_form"):
            st.write(f"Editing {entity} ID: {{st.session_state.edit_{entity_lower}_id}}")
            
{{edit_form_fields}}
            
            submitted = st.form_submit_button("Update {entity}")
            
            if submitted:
{{edit_validation}}
                
                # Create data dictionary
                data = {{edit_data_dict}}
                
                if update_{entity_lower}(st.session_state.edit_{entity_lower}_id, data):
                    # Clear edit state
                    if f"edit_{entity_lower}_id" in st.session_state:
                        del st.session_state[f"edit_{entity_lower}_id"]
                    if f"edit_{entity_lower}_data" in st.session_state:
                        del st.session_state[f"edit_{entity_lower}_data"]
                    st.rerun()
        
        if st.button("Cancel Edit"):
            if f"edit_{entity_lower}_id" in st.session_state:
                del st.session_state[f"edit_{entity_lower}_id"]
            if f"edit_{entity_lower}_data" in st.session_state:
                del st.session_state[f"edit_{entity_lower}_data"]
            st.rerun()
    else:
        st.info("Select a {entity_lower} from the list to edit.")

if __name__ == "__main__":
    main()'''
    
    def _assemble_ui_template(self, template_parts: Dict[str, str], entity: str) -> str:
        """Assemble template parts into complete UI code (DRY)"""
        # Retrieve full attribute metadata (name/type)
        attributes_meta = template_parts.get("attributes", [])
        # Fallback to simple name extraction if metadata missing
        if not attributes_meta:
            attributes_names = self._extract_attributes_from_form_fields(template_parts["form_fields"])
            attributes_meta = [{"name": n, "type": "str"} for n in attributes_names]

        # Helper: determine if type represents a list
        def _is_list_type(t: str) -> bool:
            return t.lower().startswith("list") or "[" in t.lower()

        # Build data dictionary for create form – convert list-like fields, exclude 'id' field
        data_dict_parts = []
        for attr in attributes_meta:
            name = attr["name"]
            atype = attr.get("type", "str")
            # Skip the 'id' field - it should be auto-generated, not sent in create requests
            if name.lower() == "id":
                continue
            if _is_list_type(atype):
                data_dict_parts.append(f'"{name}": {name}.split(",")')
            else:
                data_dict_parts.append(f'"{name}": {name}')
        data_dict = "{" + ", ".join(data_dict_parts) + "}"

        # Build edit form fields (pre-populated) - exclude 'id' field from editable fields
        edit_form_fields_lines = []
        # First, display the ID as read-only
        edit_form_fields_lines.append('            st.write(f"**ID:** {st.session_state.edit_' + entity.lower() + '_id}")')
        
        for attr in attributes_meta:
            name = attr["name"]
            is_fk = attr.get("is_foreign_key", False)
            related_entity = attr.get("related_entity", "")
            # Skip the 'id' field - it should be displayed as read-only above, not editable
            if name.lower() == "id":
                continue
            # 12 spaces indentation to align with code inside the "with st.form" block
            if is_fk and related_entity:
                edit_form_fields_lines.append(f"""            # Foreign key: {related_entity}
            try:
                {related_entity}_resp = requests.get(f"{{API_BASE_URL}}/api/{related_entity}s/")
                {related_entity}_resp.raise_for_status()
                {related_entity}_data = {related_entity}_resp.json()
                {related_entity}_options = {{}}
                for item in {related_entity}_data:
                    {related_entity}_options[item['id']] = item.get('name', str(item['id']))
            except requests.exceptions.RequestException:
                {related_entity}_options = {{}}
                st.error("Failed to load {related_entity} options")
            {name}_edit = st.selectbox("{related_entity.title()}", options=list({related_entity}_options.keys()), index=0 if edit_data.get("{name}") is None else list({related_entity}_options.keys()).index(edit_data.get("{name}")), format_func=lambda o: {related_entity}_options.get(o, str(o)))""")
            else:
                edit_form_fields_lines.append(
                    f'            {name}_edit = st.text_input("{name.title().replace("_"," ")}", value=edit_data.get("{name}", ""), key="{name}_edit")'
                )
        edit_form_fields = "\n".join(edit_form_fields_lines)

        # Build edit validation rules - exclude 'id' field
        edit_validation_lines = []
        for attr in attributes_meta:
            name = attr["name"]
            # Skip the 'id' field - it should not be validated as it's not editable
            if name.lower() == "id":
                continue
            # 16 spaces indent to align inside 'if submitted:' block
            edit_validation_lines.append(f'                if not {name}_edit:')
            edit_validation_lines.append(
                f'                    st.error("{name.title().replace("_"," ")} is required")'
            )
            edit_validation_lines.append("                    return")
        edit_validation = "\n".join(edit_validation_lines)

        # Build edit data dict – convert list-like fields, exclude 'id' field
        edit_data_dict_parts = []
        for attr in attributes_meta:
            name = attr["name"]
            atype = attr.get("type", "str")
            # Skip the 'id' field - it should not be sent in update requests
            if name.lower() == "id":
                continue
            if _is_list_type(atype):
                edit_data_dict_parts.append(f'"{name}": {name}_edit.split(",")')
            else:
                edit_data_dict_parts.append(f'"{name}": {name}_edit')
        edit_data_dict = "{" + ", ".join(edit_data_dict_parts) + "}"

        # Assemble complete code
        complete_code = f'''{template_parts["imports"]}

{template_parts["api_config"]}

{template_parts["crud_operations"]}

{template_parts["main_function"]}'''
        
        # Replace placeholders (support both single and double braces)
        replacements = {
            "{form_fields}": template_parts["form_fields"],
            "{validation}": template_parts["validation"],
            "{data_dict}": data_dict,
            "{edit_form_fields}": edit_form_fields,
            "{edit_validation}": edit_validation,
            "{edit_data_dict}": edit_data_dict,
            "{{form_fields}}": template_parts["form_fields"],
            "{{validation}}": template_parts["validation"],
            "{{data_dict}}": data_dict,
            "{{edit_form_fields}}": edit_form_fields,
            "{{edit_validation}}": edit_validation,
            "{{edit_data_dict}}": edit_data_dict,
        }
        for placeholder, value in replacements.items():
            complete_code = complete_code.replace(placeholder, value)
        
        return complete_code
    
    def _extract_attributes_from_form_fields(self, form_fields: str) -> List[str]:
        """Extract attribute names from form fields template"""
        import re
        # Extract variable names from form field assignments
        pattern = r'(\w+)\s*=\s*st\.'
        matches = re.findall(pattern, form_fields)
        return matches

    def _clean_llm_response(self, response_text: str) -> str:
        """
        Clean LLM response to remove markdown formatting and ensure valid Python code.
        
        Following DRY principles: This method handles all LLM response cleaning
        consistently across the FrontendSWEA to prevent syntax errors.
        """
        import re
        
        # Remove markdown code block markers
        code = response_text.strip()
        
        # Remove opening markdown markers
        if code.startswith("```python"):
            code = code[9:].strip()
        elif code.startswith("```"):
            code = code[3:].strip()
        
        # Remove closing markdown markers
        if code.endswith("```"):
            code = code[:-3].strip()
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        # Validate that we have actual Python code
        if not code or not any(line.strip() for line in code.split('\n')):
            logger.warning("⚠️ FrontendSWEA: Cleaned code is empty, using fallback")
            # Return a minimal valid Python file
            return '''import streamlit as st

def main():
    st.title("Entity Management")
    st.write("Generated code was empty. Please regenerate.")

if __name__ == "__main__":
    main()'''
        
        # Log cleaning action for debugging
        if response_text != code:
            logger.info(f"🧹 FrontendSWEA: Cleaned LLM response (removed markdown formatting)")
            logger.debug(f"   Original length: {len(response_text)} chars")
            logger.debug(f"   Cleaned length: {len(code)} chars")
        
        return code

    def _sanitize_ui_code(self, code: str) -> str:
        """Remove Streamlit arguments that are not supported in current version."""
        import re
        # Remove , required=True or required = True occurrences inside function calls
        code = re.sub(r"\s*,\s*required\s*=\s*True", "", code)
        code = re.sub(r"required\s*=\s*True\s*,", "", code)
        return code


# ---------------------------------------------------------------------------
# Custom exception to make failures explicit (no silent fallback)
# ---------------------------------------------------------------------------


class FrontendGenerationError(Exception):
    """Raised when UI generation or feedback interpretation fails"""

    pass
