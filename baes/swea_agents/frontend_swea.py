from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient
import logging

logger = logging.getLogger(__name__)


class FrontendSWEA(BaseAgent):
    """SWEA responsible for generating Streamlit UI code for domain entities."""

    def __init__(self):
        super().__init__("FrontendSWEA", "UI Generation Agent", "SWEA")
        self.llm_client = OpenAIClient()
        self._managed_system_manager = None  # Lazy initialization

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

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
        method = getattr(self, self._SUPPORTED_TASKS[task])
        try:
            return method(payload)
        except Exception as e:
            return self.create_error_response(task, str(e), "execution_error")

    # ------------------------------------------------------------------
    def _build_prompt(self, entity: str, attributes: List[str], context: str) -> str:
        """Build a direct prompt for Streamlit UI generation without template complications"""
        return f"""
Generate a complete Streamlit UI for {entity} management with the following attributes: {attributes}

Requirements:
1. Create a main() function that contains all UI code
2. Use API endpoint: http://localhost:8000/api/{entity.lower()}s/
3. Include forms for creating and editing {entity.lower()}s
4. Use st.dataframe() with proper column configuration for table display
5. Implement working edit and delete functionality with session state
6. Use st.rerun() for updates (not st.experimental_rerun)
7. Include proper error handling and success messages
8. Generate complete form fields for all attributes: {attributes}

Generate ONLY the complete Python code with imports, main() function, and proper functionality.
No markdown, no explanations, just working Python code.
"""

    def _write_to_managed_system(self, entity: str, code: str) -> str:
        """Write UI code to the managed system instead of the legacy generated directory."""
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()

        # Write the UI artifact to managed system
        file_path = self.managed_system_manager.write_entity_artifact(entity, "ui", code)

        # Update main system files to include new entity
        self.managed_system_manager.update_system_files()

        return file_path

    # -------------------- feedback interpretation methods ------------------------
    def _validate_interpretation_structure(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure interpretation has correct structure with proper data types (Phase 2 standardization)"""
        validated = {
            "attributes": [],
            "ui_improvements": [],
            "layout_changes": [],
            "modifications": [],
            "explanation": interpretation.get("explanation", "No explanation provided")
        }
        
        # Normalize attributes to consistent string format
        raw_attributes = interpretation.get("attributes", [])
        logger.debug(f"FrontendSWEA: Processing {len(raw_attributes)} attributes with types: {[type(attr) for attr in raw_attributes]}")
        
        for attr in raw_attributes:
            if isinstance(attr, dict):
                # Convert dict to "name:type" string format
                name = attr.get("name", "field")
                typ = attr.get("type", "str")
                validated["attributes"].append(f"{name}:{typ}")
                logger.debug(f"FrontendSWEA: Converted dict attribute to string: {name}:{typ}")
            elif isinstance(attr, str):
                validated["attributes"].append(attr)
            else:
                # Fallback - convert to string
                str_attr = str(attr)
                validated["attributes"].append(str_attr)
                logger.warning(f"FrontendSWEA: Converted unexpected attribute type {type(attr)} to string: {str_attr}")
        
        # Ensure other fields are lists of strings
        for field in ["ui_improvements", "layout_changes", "modifications"]:
            raw_list = interpretation.get(field, [])
            validated[field] = [str(item) for item in raw_list if item]
        
        logger.debug(f"FrontendSWEA: Validated interpretation with {len(validated['attributes'])} normalized attributes")
        return validated

    def _interpret_feedback_for_ui_generation(self, feedback: List[str], entity: str, original_attributes: List[str]) -> Dict[str, Any]:
        """
        Generic feedback interpretation using LLM to understand what UI changes are needed.
        This approach can handle any type of feedback without hardcoded conditions.
        """
        if not feedback:
            logger.debug(f"FrontendSWEA: No feedback provided for {entity} UI, using original attributes")
            return {
                "attributes": original_attributes,
                "ui_improvements": [],
                "layout_changes": [],
                "modifications": []
            }

        feedback_text = "\n".join(feedback)
        logger.debug(f"FrontendSWEA: Interpreting feedback for {entity} UI: {feedback_text}")
        
        system_prompt = f"""You are a UI/UX expert helping to interpret feedback for improving Streamlit UI generation.

CONTEXT:
- Entity: {entity}
- Original attributes: {original_attributes}
- Feedback received: {feedback_text}

TASK:
Interpret the feedback and provide specific UI improvements in JSON format.

RESPONSE FORMAT (JSON only):
{{
    "attributes": ["list", "of", "final", "attributes", "with", "types"],
    "ui_improvements": ["specific", "UI", "improvements", "to", "make"],
    "layout_changes": ["layout", "or", "design", "modifications"],
    "modifications": ["changes", "to", "implement"],
    "explanation": "brief explanation of changes made based on feedback"
}}

GUIDELINES:
- Preserve existing attributes unless feedback specifically requests changes
- Add new attributes if feedback suggests missing fields
- Focus on user experience, accessibility, and visual design
- Consider Streamlit best practices and components
- Handle any type of feedback, even unexpected ones
- If feedback is unclear, make reasonable UI/UX assumptions
- Prioritize usability, clarity, and functionality
- ALWAYS return valid JSON in the specified format
- Ensure attributes are simple strings like "name:str" or "email:str"
"""

        user_prompt = f"""Based on the feedback provided, what UI improvements should be made for the {entity} entity's Streamlit interface?

Feedback to interpret:
{feedback_text}

Current attributes:
{original_attributes}

Please provide the JSON response with UI improvements."""

        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            logger.debug(f"FrontendSWEA: Raw LLM response: {response}")
            
            # Try to parse JSON response
            import json
            try:
                interpretation = json.loads(response)
                logger.debug(f"FrontendSWEA: Parsed interpretation: {interpretation}")
                return interpretation
            except json.JSONDecodeError as json_error:
                logger.warning(f"FrontendSWEA could not parse LLM response as JSON: {json_error}")
                logger.warning(f"FrontendSWEA raw response: {response}")
                # Fallback: extract improvements from response text
                return self._extract_ui_improvements_from_text(response, original_attributes)
                
        except Exception as e:
            logger.error(f"FrontendSWEA feedback interpretation failed: {e}")
            # Fallback: return original attributes with error note
            return {
                "attributes": original_attributes,
                "ui_improvements": [],
                "layout_changes": [],
                "modifications": [f"Could not interpret feedback: {str(e)}"],
                "explanation": "Using original attributes due to feedback interpretation error"
            }

    def _extract_ui_improvements_from_text(self, response_text: str, original_attributes: List[str]) -> Dict[str, Any]:
        """Fallback method to extract UI improvements from LLM text response when JSON parsing fails"""
        # Simple text parsing fallback
        attributes = original_attributes.copy()
        ui_improvements = []
        layout_changes = []
        modifications = []
        
        # Look for common patterns in the response
        lines = response_text.lower().split('\n')
        for line in lines:
            if 'add' in line and ('field' in line or 'form' in line or 'button' in line):
                ui_improvements.append(f"Suggested UI addition from text: {line.strip()}")
            elif 'improve' in line or 'enhance' in line:
                ui_improvements.append(f"Suggested UI improvement from text: {line.strip()}")
            elif 'layout' in line or 'design' in line:
                layout_changes.append(f"Layout change from text: {line.strip()}")
        
        return {
            "attributes": attributes,
            "ui_improvements": ui_improvements,
            "layout_changes": layout_changes,
            "modifications": modifications,
            "explanation": "Extracted information from text response (JSON parsing failed)"
        }

    def _apply_ui_improvements(self, interpretation: Dict[str, Any], entity: str, context: str) -> str:
        """Apply the interpreted improvements to the UI code generation"""
        try:
            attributes = interpretation.get("attributes", [])
            ui_improvements = interpretation.get("ui_improvements", [])
            layout_changes = interpretation.get("layout_changes", [])
            
            # Build enhanced prompt with feedback-driven improvements
            base_prompt = self._build_prompt(entity, attributes, context)
            
            # Add improvement instructions to the prompt
            improvement_instructions = ""
            if ui_improvements:
                improvement_instructions = f"\n\nUI IMPROVEMENTS TO IMPLEMENT:\n" + "\n".join(f"- {imp}" for imp in ui_improvements)
            
            if layout_changes:
                improvement_instructions += f"\n\nLAYOUT CHANGES:\n" + "\n".join(f"- {change}" for change in layout_changes)
            
            enhanced_prompt = base_prompt + improvement_instructions
            
            # Generate improved UI code
            code = self.llm_client.generate_code_with_domain_focus(
                enhanced_prompt,
                code_type="Streamlit UI",
                entity_context={
                    "entity": entity,
                    "attributes": attributes,
                    "improvements_applied": interpretation,
                },
            )
            
            return code
            
        except Exception as e:
            # Fallback to basic generation
            return self.llm_client.generate_code_with_domain_focus(
                self._build_prompt(entity, interpretation.get("attributes", []), context),
                code_type="Streamlit UI",
                entity_context={"entity": entity, "attributes": interpretation.get("attributes", [])},
            )

    def _generate_ui(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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
            all_feedback.extend(techlead_feedback if isinstance(techlead_feedback, list) else [techlead_feedback])
        if previous_errors:
            all_feedback.extend(previous_errors if isinstance(previous_errors, list) else [previous_errors])
        if expected_output:
            all_feedback.append(f"Expected output: {expected_output}")

        # Interpret feedback generically using LLM (Phase 2 enhancement)
        interpretation = self._interpret_feedback_for_ui_generation(all_feedback, entity, attributes)
        
        # Validate and normalize interpretation structure (Phase 2 standardization)
        interpretation = self._validate_interpretation_structure(interpretation)
        
        # Apply the interpreted improvements with quality context
        code = self._apply_ui_improvements(interpretation, entity, context)

        file_path = self._write_to_managed_system(entity, code)
        return self.create_success_response(
            "generate_ui", {
                "file_path": file_path, 
                "code": code, 
                "managed_system": True,
                "improvements_applied": interpretation,
                "quality_mode": "standard",
            }
        )

    def _generate_ui_code(self, entity: str, attributes: List[str], context: str) -> Dict[str, Any]:
        """Generate Streamlit UI code for entity management"""
        try:
            # Parse attributes
            parsed_attributes = self._parse_attributes(attributes)
            
            # Generate the UI code
            entity_lower = entity.lower()
            entity_plural = entity_lower + "s"
            
            # Create comprehensive Streamlit UI
            code = self._create_streamlit_ui_code(entity, entity_lower, entity_plural, parsed_attributes, context)
            
            return {
                "success": True,
                "data": {
                    "code": code,
                    "ui_components": self._extract_ui_components(code),
                    "entity": entity,
                    "attributes": parsed_attributes
                }
            }
            
        except Exception as e:
            logger.error(f"❌ FrontendSWEA: Error in UI code generation: {str(e)}")
            return {
                "success": False,
                "error": f"UI code generation failed: {str(e)}",
                "data": {}
            }

    def _fix_frontend_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix frontend issues based on TechLeadSWEA coordination"""
        try:
            entity = payload.get("entity", "Student")
            fix_action = payload.get("fix_action", "")
            issue_type = payload.get("issue_type", "")
            techlead_decision = payload.get("techlead_decision", {})
            
            # Extract detailed context from TechLeadSWEA decision
            detailed_context = techlead_decision.get("detailed_context", {})
            specific_issue = techlead_decision.get("specific_issue", "")
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
                        "Include proper function definitions for all UI operations"
                    ],
                    "fix_focus": "missing_functions"
                }
                return self._generate_ui(enhanced_payload)
                
            elif fix_action in ["fix_ui_interface", "regenerate_ui"]:
                logger.debug("🔧 FrontendSWEA: Fixing UI interface issues")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix UI interface issues: {reasoning}"],
                    "fix_focus": "interface_issues"
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
                logger.debug("🔧 FrontendSWEA: Default fix - regenerating UI with generic improvements")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"General frontend fix needed: {reasoning}"],
                }
                return self._generate_ui(enhanced_payload)
                
        except Exception as e:
            logger.error("❌ FrontendSWEA fix_issues failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "fix_error")
