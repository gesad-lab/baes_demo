from typing import Any, Dict, List
import csv
import logging
from datetime import datetime
from pathlib import Path

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient
# Utility for conditional debug logging
from ..domain_entities.base_bae import is_debug_mode

logger = logging.getLogger(__name__)

# Stage 2 Improvement #8: Feedback Loop Analytics for FrontendSWEA
class FeedbackLoopAnalytics:
    """
    Stage 2 Improvement #8: Feedback Loop Logging and Analytics
    Tracks all feedback interactions between TechLeadSWEA and FrontendSWEA in CSV format.
    """
    
    def __init__(self):
        self.analytics_dir = Path("logs/feedback_analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.analytics_dir / "frontend_feedback_analytics.csv"
        self._ensure_csv_headers()
    
    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for pandas DataFrame compatibility"""
        if not self.csv_file.exists():
            headers = [
                'timestamp',
                'session_id', 
                'entity',
                'feedback_round',
                'techlead_feedback_count',
                'feedback_categories',
                'frontend_response_time_seconds',
                'feedback_addressed',
                'retry_count',
                'final_success',
                'feedback_text_length',
                'ui_changes_made',
                'improvement_areas'
            ]
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_feedback_interaction(self, session_id: str, entity: str, 
                               feedback_round: int, techlead_feedback: List[str],
                               frontend_response_time: float, feedback_addressed: bool,
                               retry_count: int, final_success: bool, 
                               ui_changes_made: List[str] = None):
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
                ';'.join(feedback_categories),
                round(frontend_response_time, 2),
                feedback_addressed,
                retry_count,
                final_success,
                sum(len(fb) for fb in techlead_feedback),
                ';'.join(ui_changes_made or []),
                ';'.join(improvement_areas)
            ]
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                
            logger.info(f"📊 Frontend feedback analytics logged: {entity} round {feedback_round}")
            
        except Exception as e:
            logger.warning(f"Failed to log frontend feedback analytics: {e}")
    
    def _categorize_feedback(self, feedback_list: List[str]) -> List[str]:
        """Categorize feedback for analytics purposes"""
        categories = set()
        feedback_text = ' '.join(feedback_list).lower()
        
        # UI/UX feedback
        if any(term in feedback_text for term in ['ui', 'interface', 'user', 'streamlit', 'form']):
            categories.add('ui_ux')
        
        # Data display feedback  
        if any(term in feedback_text for term in ['dataframe', 'display', 'table', 'chart', 'visualization']):
            categories.add('data_display')
            
        # Navigation feedback
        if any(term in feedback_text for term in ['navigation', 'menu', 'sidebar', 'page', 'routing']):
            categories.add('navigation')
            
        # Input/Form feedback
        if any(term in feedback_text for term in ['input', 'form', 'validation', 'field', 'button']):
            categories.add('input_forms')
            
        # Styling feedback
        if any(term in feedback_text for term in ['style', 'color', 'layout', 'design', 'css']):
            categories.add('styling')
            
        return list(categories) if categories else ['general']
    
    def _extract_improvement_areas(self, feedback_list: List[str]) -> List[str]:
        """Extract specific improvement areas from feedback"""
        areas = set()
        feedback_text = ' '.join(feedback_list).lower()
        
        if 'usability' in feedback_text:
            areas.add('usability')
        if 'accessibility' in feedback_text:
            areas.add('accessibility') 
        if 'responsive' in feedback_text:
            areas.add('responsive_design')
        if 'performance' in feedback_text:
            areas.add('performance')
        if 'validation' in feedback_text:
            areas.add('form_validation')
            
        return list(areas) if areas else ['user_experience']

class FrontendSWEA(BaseAgent):
    """SWEA responsible for generating Streamlit UI code for domain entities."""

    def __init__(self):
        super().__init__("FrontendSWEA", "UI Generation Agent", "SWEA")
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

    def _get_do_not_ignore_warning(self) -> str:
        """
        Generate standard 'Do Not Ignore' warning text for all LLM prompts.
        Stage 1 Improvement #10: Explicit warnings to prevent LLM from ignoring instructions.
        """
        return """
🚨 CRITICAL WARNING: If you ignore ANY of the following instructions, your output will be REJECTED and you will be required to regenerate it. You MUST address EVERY requirement listed below. Failure to comply will result in immediate rejection.

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
        
        # Stage 4 Improvement #1: Get structured feedback for injection
        structured_feedback = self._get_structured_feedback_injection(entity, "FrontendSWEA", "generate_ui")
        
        system_prompt = f"""You are a UI/UX expert helping to interpret feedback for improving Streamlit UI generation.

{self._get_do_not_ignore_warning()}

CONTEXT:
- Entity: {entity}
- Original attributes: {original_attributes}
- Feedback received: {feedback_text}

{structured_feedback}

STAGE 3 IMPROVEMENT #4: PRIORITY-BASED FEEDBACK HANDLING
TechLeadSWEA now provides categorized feedback with priority levels:
- CRITICAL: Issues that prevent system from working (MUST fix immediately)
- REQUIRED: Important functionality issues (MUST fix before approval)  
- OPTIONAL: Nice-to-have improvements (can ignore for now)

You MUST focus on CRITICAL and REQUIRED feedback only. Ignore OPTIONAL suggestions.

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

        # Stage 2 Improvement #8: Track analytics timing
        start_time = datetime.now()

        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            logger.debug(f"FrontendSWEA: Raw LLM response: {response}")
            
            # Try to parse JSON response
            import json
            try:
                interpretation = json.loads(response)
                logger.debug(f"FrontendSWEA: Parsed interpretation: {interpretation}")
                
                # Stage 2 Improvement #8: Log successful feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                ui_changes = interpretation.get("ui_improvements", []) + interpretation.get("layout_changes", [])
                
                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    feedback_round=1,
                    techlead_feedback=feedback,
                    frontend_response_time=response_time,
                    feedback_addressed=True,
                    retry_count=0,
                    final_success=True,
                    ui_changes_made=ui_changes
                )
                
                return interpretation
            except json.JSONDecodeError as json_error:
                error_msg = (
                    f"LLM response for UI feedback interpretation is not valid JSON: {json_error}. "
                    f"Raw response: {response}"
                )
                logger.error(error_msg)
                
                # Stage 2 Improvement #8: Log failed feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    feedback_round=1,
                    techlead_feedback=feedback,
                    frontend_response_time=response_time,
                    feedback_addressed=False,
                    retry_count=0,
                    final_success=False,
                    ui_changes_made=[]
                )
                
                raise FrontendGenerationError(error_msg) from json_error
                
        except Exception as e:
            logger.error(f"FrontendSWEA feedback interpretation failed: {e}")
            
            # Stage 2 Improvement #8: Log failed feedback interaction
            response_time = (datetime.now() - start_time).total_seconds()
            self.feedback_analytics.log_feedback_interaction(
                session_id=self.current_session_id,
                entity=entity,
                feedback_round=1,
                techlead_feedback=feedback,
                frontend_response_time=response_time,
                feedback_addressed=False,
                retry_count=0,
                final_success=False,
                ui_changes_made=[]
            )
            
            raise

    def _get_structured_feedback_injection(self, entity: str, swea_agent: str, task_type: str) -> str:
        """
        Stage 4 Improvement #1: Get structured feedback injection from TechLeadSWEA.
        Returns formatted feedback instructions for prompt injection.
        """
        try:
            # Import TechLeadSWEA to access feedback storage
            from baes.swea_agents.techlead_swea import TechLeadSWEA
            
            # Create temporary TechLeadSWEA instance to access feedback storage
            techlead = TechLeadSWEA()
            structured_instructions = techlead._retrieve_feedback_for_injection(entity, swea_agent, task_type)
            
            if structured_instructions:
                logger.info(f"📤 FrontendSWEA: Retrieved structured feedback for {entity}.{swea_agent}.{task_type}")
                return structured_instructions
            else:
                logger.debug(f"📤 FrontendSWEA: No structured feedback available for {entity}.{swea_agent}.{task_type}")
                return ""
                
        except Exception as e:
            logger.warning(f"FrontendSWEA: Failed to get structured feedback injection: {str(e)}")
            return ""

    def _extract_ui_improvements_from_text(self, response_text: str, original_attributes: List[str]) -> Dict[str, Any]:
        """Fallback method to extract UI improvements from LLM text response when JSON parsing fails"""
        # Type validation – this function should only be used intentionally
        if not isinstance(response_text, str):
            raise FrontendGenerationError(
                f"LLM response expected to be str but got {type(response_text)}"
            )

        if is_debug_mode():
            logger.debug("FrontendSWEA raw fallback text preview: %.120s", repr(response_text))

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
            logger.error(f"FrontendSWEA UI improvement application failed: {e}")
            raise

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


# ---------------------------------------------------------------------------
# Custom exception to make failures explicit (no silent fallback)
# ---------------------------------------------------------------------------


class FrontendGenerationError(Exception):
    """Raised when UI generation or feedback interpretation fails"""
    pass
