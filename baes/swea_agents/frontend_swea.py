import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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

            logger.info(f"\U0001F4CA Frontend feedback analytics logged: {entity} round {feedback_round}")

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

        # Build form fields section
        form_fields = []
        for attr in parsed_attributes:
            field_name = attr["name"]
            field_type = attr["type"].lower()

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

        # Build validation logic
        validation_rules = []
        for attr in parsed_attributes:
            field_name = attr["name"]
            field_type = attr["type"].lower()

            if field_type == "email":
                validation_rules.append(f'    if {field_name} and "@" not in {field_name}:')
                validation_rules.append('        st.error("Please enter a valid email address")')
                validation_rules.append("        return")
            else:
                validation_rules.append(f"    if not {field_name}:")
                validation_rules.append(f'        st.error("{field_name.title()} is required")')
                validation_rules.append("        return")

        # Build data dictionary
        # Removed unused variable data_dict

        # Build display columns
        # Removed unused variable display_columns

        # Removed unused variable entity_lower

        prompt = (
            """
{self._get_do_not_ignore_warning()}

You are a FrontendSWEA agent specialized in generating Streamlit UI code for domain entity management.

CRITICAL REQUIREMENTS - Your code MUST include ALL of the following:

1. **MANDATORY: st.set_page_config() at the beginning of the file**
   - Must be the first Streamlit call in the file
   - Use: st.set_page_config(page_title="{entity} Management", page_icon="📊", layout="wide")

2. **MANDATORY: API_BASE_URL configuration**
   - Define: API_BASE_URL = "http://localhost:8000"
   - Use this constant for all API calls

3. **MANDATORY: Proper error handling with response.raise_for_status()**
   - Add response.raise_for_status() after every API call
   - Wrap all API calls in try/except blocks

4. **MANDATORY: Complete CRUD functionality**
   - Create: POST to /api/{entity_lower}s/
   - Read: GET from /api/{entity_lower}s/
   - Update: PUT to /api/{entity_lower}s/{{id}}
   - Delete: DELETE to /api/{entity_lower}s/{{id}}

5. **MANDATORY: Form validation and error messages**
   - Validate all required fields
   - Show st.error() messages for validation failures

6. **MANDATORY: Proper imports**
   - import streamlit as st
   - import requests
   - from typing import List, Dict, Any, Optional

Entity: {entity}
Attributes: {attributes}
Context: {context}

Generate complete Streamlit UI code that includes:

```python
import streamlit as st
import requests
from typing import List, Dict, Any, Optional

# MANDATORY: Page configuration (must be first)
st.set_page_config(page_title="{entity} Management", page_icon="📊", layout="wide")

# MANDATORY: API base URL
API_BASE_URL = "http://localhost:8000"

def main():
    st.title("{entity} Management System")

    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 List {entity}s", "➕ Add {entity}", "✏️ Edit {entity}"])

    with tab1:
        st.header("All {entity}s")

        # Refresh button
        if st.button("🔄 Refresh", key="refresh_list"):
            st.rerun()

        try:
            response = requests.get(f"{{API_BASE_URL}}/api/{entity_lower}s/")
            response.raise_for_status()  # MANDATORY: Status code validation
            {entity_lower}s = response.json()

            if {entity_lower}s:
                # Convert to DataFrame for better display
                import pandas as pd
                df = pd.DataFrame({entity_lower}s)

                # Display with edit/delete buttons
                for idx, {entity_lower} in enumerate({entity_lower}s):
                    with st.expander(f"{entity} ID: {{{entity_lower}['id']}}"):
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            for key, value in {entity_lower}.items():
                                if key != 'id':
                                    st.write(f"**{{key.title()}}:** {{value}}")

                        with col2:
                            if st.button("✏️ Edit", key=f"edit_{{{entity_lower}['id']}}"):
                                st.session_state.edit_{entity_lower}_id = {entity_lower}['id']
                                st.session_state.edit_{entity_lower}_data = {entity_lower}
                                st.rerun()

                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{{{entity_lower}['id']}}"):
                                try:
                                    delete_response = requests.delete(f"{{API_BASE_URL}}/api/{entity_lower}s/{{{entity_lower}['id']}}")
                                    delete_response.raise_for_status()  # MANDATORY: Status code validation
                                    if delete_response.status_code == 204:
                                        st.success(f"{entity} deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete {entity_lower}")
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Error deleting {entity_lower}: {{e}}")
            else:
                st.info("No {entity_lower}s found.")

        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching {entity_lower}s: {{e}}")

    with tab2:
        st.header("Add New {entity}")

        with st.form("add_{entity_lower}_form"):
{form_fields}

            submitted = st.form_submit_button("➕ Add {entity}")

            if submitted:
{validation_rules}

                # Create data dictionary
                data = {data_dict}

                try:
                    response = requests.post(f"{{API_BASE_URL}}/api/{entity_lower}s/", json=data)
                    response.raise_for_status()  # MANDATORY: Status code validation

                    if response.status_code == 201:
                        st.success(f"{entity} added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add {entity_lower}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error adding {entity_lower}: {{e}}")

    with tab3:
        st.header("Edit {entity}")

        if f"edit_{entity_lower}_id" in st.session_state:
            edit_data = st.session_state.get(f"edit_{entity_lower}_data", {{}})

            with st.form("edit_{entity_lower}_form"):
                st.write(f"Editing {entity} ID: {{st.session_state.edit_{entity_lower}_id}}")

                # Pre-populate form fields with existing data
{form_fields.replace('key="', 'value=edit_data.get("').replace('_input"', '", ""), key="').replace('_input")', '_edit_input")')}

                submitted = st.form_submit_button("💾 Update {entity}")

                if submitted:
{validation_rules.replace('_input', '_edit_input')}

                    # Create data dictionary
                    data = {data_dict.replace('_input', '_edit_input')}

                    try:
                        response = requests.put(
                            f"{{API_BASE_URL}}/api/{entity_lower}s/{{st.session_state.edit_{entity_lower}_id}}",
                            json=data
                        )
                        response.raise_for_status()  # MANDATORY: Status code validation

                        if response.status_code == 200:
                            st.success(f"{entity} updated successfully!")
                            # Clear edit state
                            if f"edit_{entity_lower}_id" in st.session_state:
                                del st.session_state[f"edit_{entity_lower}_id"]
                            if f"edit_{entity_lower}_data" in st.session_state:
                                del st.session_state[f"edit_{entity_lower}_data"]
                            st.rerun()
                        else:
                            st.error("Failed to update {entity_lower}")

                    except requests.exceptions.RequestException as e:
                        st.error(f"Error updating {entity_lower}: {{e}}")

            if st.button("❌ Cancel Edit"):
                if f"edit_{entity_lower}_id" in st.session_state:
                    del st.session_state[f"edit_{entity_lower}_id"]
                if f"edit_{entity_lower}_data" in st.session_state:
                    del st.session_state[f"edit_{entity_lower}_data"]
                st.rerun()

        else:
            st.info("Select a {entity_lower} from the list to edit.")

if __name__ == "__main__":
    main()
```

CRITICAL: Generate ONLY the Python code above, with actual field names and validation logic based on the provided attributes. Do not include any markdown formatting, code block markers, or explanations.
"""
        )

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
        "base_url": "API_BASE_URL = \"http://localhost:8000\"",
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

            # Parse the response
            response_text = response_text

            # Extract JSON from response (handle potential markdown formatting)
            import json
            import re

            # Try to extract JSON from the response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    interpretation = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(
                        "Failed to parse JSON from LLM response, using fallback interpretation"
                    )
                    interpretation = self._extract_ui_improvements_from_text(
                        response_text, original_attributes
                    )
            else:
                logger.warning("No JSON found in LLM response, using fallback interpretation")
                interpretation = self._extract_ui_improvements_from_text(
                    response_text, original_attributes
                )

            # Validate and normalize interpretation structure
            interpretation = self._validate_interpretation_structure(interpretation)

            logger.info(f"✅ FrontendSWEA: Feedback interpretation completed for {entity}")
            return interpretation

        except Exception as e:
            logger.error(f"❌ FrontendSWEA: Feedback interpretation failed: {e}")
            # Return a basic interpretation structure as fallback
            return {
                "ui_improvements": {
                    "missing_components": [
                        "st.set_page_config",
                        "API_BASE_URL",
                        "response.raise_for_status",
                    ],
                    "required_patterns": ["proper error handling", "form validation"],
                    "user_experience": ["clear error messages", "success feedback"],
                },
                "form_fields": [],
                "validation_rules": [],
                "api_integration": {
                    "base_url": 'API_BASE_URL = "http://localhost:8000"',
                    "endpoints": {},
                    "error_handling": ["try/except blocks", "response.raise_for_status"],
                },
            }

    def _get_structured_feedback_injection(
        self, entity: str, swea_agent: str, task_type: str
    ) -> str:
        """Get structured feedback injection for LLM prompts"""
        return """
CRITICAL FEEDBACK CONTEXT:
- Entity: {entity}
- Reviewing Agent: {swea_agent}
- Task Type: {task_type}
- Validation Standards: FrontendStandards compliance required
- Quality Gate: TechLeadSWEA approval mandatory

MANDATORY REQUIREMENTS:
1. st.set_page_config() must be the first Streamlit call
2. API_BASE_URL must be defined as "http://localhost:8000"
3. All API calls must use response.raise_for_status()
4. All forms must have proper validation
5. All input fields must have unique keys
6. Error handling must be comprehensive
"""

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

        # Extract improvements based on common patterns
        if "st.set_page_config" not in response_text:
            improvements["ui_improvements"]["missing_components"].append("st.set_page_config")

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
                attributes = ["name:str", "email:str"]

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

            code = response_text

            # Validate that the generated code includes critical components
            if "st.set_page_config" not in code:
                logger.warning("Generated code missing st.set_page_config, adding it")
                code = (
                    'import streamlit as st\nimport requests\nfrom typing import List, Dict, Any, Optional\n\nst.set_page_config(page_title="Entity Management", page_icon="📊", layout="wide")\n\n'
                    + code
                )

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

            # If we have feedback, interpret it and apply improvements
            if all_feedback:
                logger.info(f"🔧 FrontendSWEA: Interpreting feedback for {entity}")
                interpretation = self._interpret_feedback_for_ui_generation(
                    all_feedback, entity, attributes
                )
                code = self._apply_ui_improvements(interpretation, entity, context)
            else:
                # Generate fresh UI code
                logger.info(f"🎨 FrontendSWEA: Generating fresh UI code for {entity}")
                prompt = self._build_prompt(entity, attributes, context)

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

                code = response_text

            # Write the generated code to the managed system
            file_path = self._write_to_managed_system(entity, code)

            return self.create_success_response(
                "generate_ui",
                {
                    "file_path": file_path,
                    "code": code,
                    "managed_system": True,
                    "quality_mode": "llm_generated",
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
            code = self._create_streamlit_ui_code(
                entity, parsed_attributes, context
            )

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
        """Parse attributes to handle different formats"""
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
        return parsed_attributes

    def _create_streamlit_ui_code(
        self,
        entity: str,
        attributes: List[Dict[str, str]],
        context: str,
    ) -> str:
        """Create comprehensive Streamlit UI code"""
        # This method is now deprecated in favor of LLM-based generation
        # Keeping for backward compatibility
        logger.warning("Using deprecated _create_streamlit_ui_code method")
        return self._generate_ui_code_directly(entity, attributes, context)

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

        return response_text

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

# ---------------------------------------------------------------------------
# Custom exception to make failures explicit (no silent fallback)
# ---------------------------------------------------------------------------

class FrontendGenerationError(Exception):
    """Raised when UI generation or feedback interpretation fails"""

    pass
