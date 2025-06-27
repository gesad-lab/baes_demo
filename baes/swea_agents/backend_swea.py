import os
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient
import logging

logger = logging.getLogger(__name__)


class BackendSWEA(BaseAgent):
    """
    Software Engineering Autonomous Agent responsible for generating backend code
    (Pydantic model and FastAPI routes) while preserving domain semantics.
    """

    def __init__(self):
        super().__init__("BackendSWEA", "Backend Code Generation Agent", "SWEA")
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
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_prompt(
        self, entity: str, attributes: List[str], code_type: str, context: str
    ) -> str:
        """Load prompt template and format it with runtime values."""
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
            return template.format(
                entity=entity,
                attributes=", ".join(attributes),
                code_type=code_type,
                context=context,
            )
        except KeyError:
            # If template had unexpected placeholders, fall back to simple prompt
            return (
                f"Generate {code_type} for {entity} with attributes: {', '.join(attributes)}. "
                f"Context: {context}. Return ONLY code."
            )

    def _write_to_managed_system(self, entity: str, artifact_type: str, code: str) -> str:
        """Write code to the managed system instead of the legacy generated directory."""
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()

        # Write the artifact to managed system
        file_path = self.managed_system_manager.write_entity_artifact(entity, artifact_type, code)

        # Update main system files to include new entity
        self.managed_system_manager.update_system_files()

        return file_path

    # -------------------- feedback interpretation methods ------------------------
    def _validate_interpretation_structure(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure interpretation has correct structure with proper data types (Phase 2 standardization)"""
        validated = {
            "attributes": [],
            "additional_requirements": [],
            "code_improvements": [],
            "modifications": [],
            "explanation": interpretation.get("explanation", "No explanation provided")
        }
        
        # Normalize attributes to consistent string format
        raw_attributes = interpretation.get("attributes", [])
        logger.debug(f"BackendSWEA: Processing {len(raw_attributes)} attributes with types: {[type(attr) for attr in raw_attributes]}")
        
        for attr in raw_attributes:
            if isinstance(attr, dict):
                # Convert dict to "name:type" string format
                name = attr.get("name", "field")
                typ = attr.get("type", "str")
                validated["attributes"].append(f"{name}:{typ}")
                logger.debug(f"BackendSWEA: Converted dict attribute to string: {name}:{typ}")
            elif isinstance(attr, str):
                validated["attributes"].append(attr)
            else:
                # Fallback - convert to string
                str_attr = str(attr)
                validated["attributes"].append(str_attr)
                logger.warning(f"BackendSWEA: Converted unexpected attribute type {type(attr)} to string: {str_attr}")
        
        # Ensure other fields are lists of strings
        for field in ["additional_requirements", "code_improvements", "modifications"]:
            raw_list = interpretation.get(field, [])
            validated[field] = [str(item) for item in raw_list if item]
        
        logger.debug(f"BackendSWEA: Validated interpretation with {len(validated['attributes'])} normalized attributes")
        return validated

    def _interpret_feedback_for_backend_generation(self, feedback: List[str], entity: str, code_type: str, original_attributes: List[str]) -> Dict[str, Any]:
        """
        Generic feedback interpretation using LLM to understand what backend code changes are needed.
        This approach can handle any type of feedback without hardcoded conditions.
        """
        if not feedback:
            logger.debug(f"BackendSWEA: No feedback provided for {entity} {code_type}, using original attributes")
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "code_improvements": [],
                "modifications": []
            }

        feedback_text = "\n".join(feedback)
        logger.debug(f"BackendSWEA: Interpreting feedback for {entity} {code_type}: {feedback_text}")
        
        system_prompt = f"""You are a backend development expert helping to interpret feedback for improving {code_type} generation.

CONTEXT:
- Entity: {entity}
- Code Type: {code_type}
- Original attributes: {original_attributes}
- Feedback received: {feedback_text}

TASK:
Interpret the feedback and provide specific backend code improvements in JSON format.

RESPONSE FORMAT (JSON only):
{{
    "attributes": ["list", "of", "final", "attributes", "with", "types"],
    "additional_requirements": ["any", "new", "requirements", "identified"],
    "code_improvements": ["specific", "code", "improvements", "to", "make"],
    "modifications": ["changes", "to", "implement"],
    "explanation": "brief explanation of changes made based on feedback"
}}

GUIDELINES:
- Preserve existing attributes unless feedback specifically requests changes
- Add new attributes if feedback suggests missing fields
- Include proper data types (str, int, float, date, bool)
- Consider FastAPI/Pydantic best practices
- Handle any type of feedback, even unexpected ones
- If feedback is unclear, make reasonable backend development assumptions
- Focus on code quality, validation, error handling, and API design
- ALWAYS return valid JSON in the specified format
- Ensure attributes are simple strings like "name:str" or "email:str"
"""

        user_prompt = f"""Based on the feedback provided, what backend code improvements should be made for the {entity} entity's {code_type}?

Feedback to interpret:
{feedback_text}

Current attributes:
{original_attributes}

Please provide the JSON response with backend improvements."""

        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            logger.debug(f"BackendSWEA: Raw LLM response for {code_type}: {response}")
            
            # Try to parse JSON response
            import json
            try:
                interpretation = json.loads(response)
                logger.debug(f"BackendSWEA: Parsed interpretation for {code_type}: {interpretation}")
                return interpretation
            except json.JSONDecodeError as json_error:
                logger.warning(f"BackendSWEA could not parse LLM response as JSON: {json_error}")
                logger.warning(f"BackendSWEA raw response: {response}")
                # Fallback: extract improvements from response text
                return self._extract_improvements_from_text(response, original_attributes)
                
        except Exception as e:
            logger.error(f"BackendSWEA feedback interpretation failed: {e}")
            # Fallback: return original attributes with error note
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "code_improvements": [],
                "modifications": [f"Could not interpret feedback: {str(e)}"],
                "explanation": "Using original attributes due to feedback interpretation error"
            }

    def _extract_improvements_from_text(self, response_text: str, original_attributes: List[str]) -> Dict[str, Any]:
        """Fallback method to extract improvements from LLM text response when JSON parsing fails"""
        # Simple text parsing fallback
        attributes = original_attributes.copy()
        improvements = []
        modifications = []
        
        # Look for common patterns in the response
        lines = response_text.lower().split('\n')
        for line in lines:
            if 'add' in line and ('field' in line or 'attribute' in line or 'validation' in line):
                improvements.append(f"Suggested addition from text: {line.strip()}")
            elif 'improve' in line or 'enhance' in line:
                improvements.append(f"Suggested improvement from text: {line.strip()}")
            elif 'error' in line and 'handling' in line:
                improvements.append(f"Error handling improvement: {line.strip()}")
        
        return {
            "attributes": attributes,
            "additional_requirements": [],
            "code_improvements": improvements,
            "modifications": modifications,
            "explanation": "Extracted information from text response (JSON parsing failed)"
        }

    def _apply_backend_improvements(self, interpretation: Dict[str, Any], entity: str, code_type: str, context: str) -> str:
        """Apply the interpreted improvements to the backend code generation"""
        try:
            attributes = interpretation.get("attributes", [])
            additional_requirements = interpretation.get("additional_requirements", [])
            code_improvements = interpretation.get("code_improvements", [])
            
            # Build enhanced prompt with feedback-driven improvements
            base_prompt = self._build_prompt(entity, attributes, code_type, context)
            
            # Add improvement instructions to the prompt
            improvement_instructions = ""
            if code_improvements:
                improvement_instructions = f"\n\nIMPROVEMENTS TO IMPLEMENT:\n" + "\n".join(f"- {imp}" for imp in code_improvements)
            
            if additional_requirements:
                improvement_instructions += f"\n\nADDITIONAL REQUIREMENTS:\n" + "\n".join(f"- {req}" for req in additional_requirements)
            
            enhanced_prompt = base_prompt + improvement_instructions
            
            # Generate improved code
            code = self.llm_client.generate_code_with_domain_focus(
                enhanced_prompt,
                code_type=code_type,
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
                self._build_prompt(entity, interpretation.get("attributes", []), code_type, context),
                code_type=code_type,
                entity_context={"entity": entity, "attributes": interpretation.get("attributes", [])},
            )

    # -------------------- task implementations ------------------------
    def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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
        interpretation = self._interpret_feedback_for_backend_generation(all_feedback, entity, "Pydantic Model", attributes)
        
        # Validate and normalize interpretation structure (Phase 2 standardization)
        interpretation = self._validate_interpretation_structure(interpretation)
        
        # Apply the interpreted improvements
        code = self._apply_backend_improvements(interpretation, entity, "Pydantic Model", context)

        file_path = self._write_to_managed_system(entity, "model", code)
        return self.create_success_response(
            "generate_model", {
                "file_path": file_path, 
                "code": code, 
                "managed_system": True,
                "improvements_applied": interpretation
            }
        )

    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
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
        interpretation = self._interpret_feedback_for_backend_generation(all_feedback, entity, "FastAPI Routes", attributes)
        
        # Validate and normalize interpretation structure (Phase 2 standardization)
        interpretation = self._validate_interpretation_structure(interpretation)
        
        # Apply the interpreted improvements
        code = self._apply_backend_improvements(interpretation, entity, "FastAPI Routes", context)

        file_path = self._write_to_managed_system(entity, "routes", code)
        return self.create_success_response(
            "generate_api", {
                "file_path": file_path, 
                "code": code, 
                "managed_system": True,
                "improvements_applied": interpretation
            }
        )

    def _generate_requirements(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate requirements.txt file with all necessary dependencies."""
        try:
            entity = payload.get("entity", "Student")
            feedback = payload.get("feedback", [])
            fix_context = payload.get("fix_context", {})

            logger.info(f"🧠 BackendSWEA: Generating requirements.txt for {entity}")

            # Extract dependencies from feedback or fix context
            dependencies = self._analyze_dependencies(payload, fix_context)

            # Add standard dependencies
            if not dependencies:
                dependencies = [
                    "fastapi>=0.104.1",
                    "uvicorn>=0.24.0",
                    "pydantic>=2.5.0",
                    "pydantic[email]>=2.5.0",
                    "python-multipart>=0.0.6",
                    "sqlalchemy>=2.0.23",
                ]

            # Build requirements content
            content = self._build_requirements_content(dependencies)

            # Write to managed system
            file_path = self._write_requirements_to_managed_system(content)

            return self.create_success_response(
                "generate_requirements",
                {
                    "file_path": file_path,
                    "dependencies": dependencies,
                    "lines_generated": len(dependencies),
                },
            )

        except Exception as e:
            logger.error(f"❌ BackendSWEA requirements generation failed: {str(e)}")
            return self.create_error_response("generate_requirements", str(e), "generation_error")

    def _fix_backend_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix backend issues based on TechLeadSWEA coordination"""
        try:
            entity = payload.get("entity", "Student")
            fix_action = payload.get("fix_action", "")
            issue_type = payload.get("issue_type", "")
            techlead_decision = payload.get("techlead_decision", {})
            
            # Extract detailed context from TechLeadSWEA decision
            detailed_context = techlead_decision.get("detailed_context", {})
            specific_issue = techlead_decision.get("specific_issue", "")
            reasoning = techlead_decision.get("reasoning", "")
            
            logger.info("🔧 BackendSWEA: Fixing backend issues for %s", entity)
            logger.info("   🎯 Fix Action: %s", fix_action)
            logger.info("   📋 Issue Type: %s", issue_type)
            logger.info("   💡 Reasoning: %s", reasoning)
            
            # Handle specific fix actions from TechLeadSWEA
            if fix_action in ["fix_imports", "update_dependencies", "fix_import_dependencies"]:
                logger.debug("🔧 BackendSWEA: Handling import/dependency issues")
                return self._generate_requirements(payload)
                
            elif fix_action in ["fix_model_validation", "update_pydantic_models", "fix_pydantic_validation"]:
                logger.debug("🔧 BackendSWEA: Regenerating model due to validation issues")
                return self._generate_model(payload)
                
            elif fix_action in ["fix_api_validation", "update_error_handling", "fix_api_routing", "regenerate_api_endpoints"]:
                logger.debug("🔧 BackendSWEA: Regenerating API due to routing/validation issues")
                return self._generate_api(payload)
                
            elif fix_action in ["fix_syntax_errors", "regenerate_code"]:
                logger.debug("🔧 BackendSWEA: Fixing syntax errors - regenerating both model and API")
                # For syntax issues, regenerate both model and API
                model_result = self._generate_model(payload)
                if model_result.get("success"):
                    api_result = self._generate_api(payload)
                    if api_result.get("success"):
                        return self.create_success_response(
                            "fix_issues",
                            {
                                "fix_applied": True,
                                "fix_type": "syntax_error_fix",
                                "fix_action": fix_action,
                                "model_result": model_result.get("data", {}),
                                "api_result": api_result.get("data", {}),
                            }
                        )
                    else:
                        return api_result
                else:
                    return model_result
                    
            elif fix_action in ["regenerate_model_with_imports"]:
                logger.debug("🔧 BackendSWEA: Regenerating model with proper imports")
                # First generate requirements, then model
                req_result = self._generate_requirements(payload)
                if req_result.get("success"):
                    model_result = self._generate_model(payload)
                    return model_result
                else:
                    return req_result
                    
            # Fallback: Handle by issue type (legacy support)
            elif "dependency" in issue_type or "import" in issue_type or "missing" in issue_type:
                logger.debug("🔧 BackendSWEA: Handling dependency/import issues (legacy)")
                return self._generate_requirements(payload)
            elif "model" in issue_type or "pydantic" in issue_type or "validation" in issue_type:
                logger.debug("🔧 BackendSWEA: Regenerating model due to validation issues (legacy)")
                return self._generate_model(payload)
            elif "api" in issue_type or "route" in issue_type or "endpoint" in issue_type:
                logger.debug("🔧 BackendSWEA: Regenerating API due to route issues (legacy)")
                return self._generate_api(payload)
            elif "syntax" in issue_type or "code" in issue_type:
                logger.debug("🔧 BackendSWEA: Fixing code syntax issues (legacy)")
                # For syntax issues, regenerate both model and API
                model_result = self._generate_model(payload)
                if model_result.get("success"):
                    api_result = self._generate_api(payload)
                    return api_result
                else:
                    return model_result
            else:
                # Default: regenerate all backend components
                logger.debug("🔧 BackendSWEA: Default fix - regenerating all backend components")
                model_result = self._generate_model(payload)
                if model_result.get("success"):
                    api_result = self._generate_api(payload)
                    if api_result.get("success"):
                        return self.create_success_response(
                            "fix_issues",
                            {
                                "fix_applied": True,
                                "fix_type": "complete_backend_regeneration",
                                "fix_action": fix_action or "default_regeneration",
                                "model_result": model_result.get("data", {}),
                                "api_result": api_result.get("data", {}),
                            }
                        )
                    else:
                        return api_result
                else:
                    return model_result
                    
        except Exception as e:
            logger.error("❌ BackendSWEA fix_issues failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "fix_error")

    def _analyze_dependencies(
        self, payload: Dict[str, Any], fix_context: Dict[str, Any]
    ) -> List[str]:
        """Analyze what dependencies are needed for the current system."""
        base_deps = [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "streamlit==1.28.1",
            "pydantic==2.5.0",
            "sqlalchemy==2.0.23",
            "python-multipart",
            "requests==2.31.0",
            "pytest==7.4.3",
        ]

        # Add email validation if needed
        attributes = payload.get("attributes", [])
        if any("email" in str(attr).lower() for attr in attributes):
            base_deps.extend(
                [
                    "pydantic[email]",
                    "email-validator",
                ]
            )

        # Add dependencies based on fix context
        if fix_context:
            stderr = fix_context.get("test_stderr", "").lower()
            if "email-validator" in stderr:
                base_deps.append("email-validator")
            if "pydantic[email]" in stderr:
                base_deps.append("pydantic[email]")

        # Add any additional dependencies from payload
        additional_deps = payload.get("additional_dependencies", [])
        base_deps.extend(additional_deps)

        # Remove duplicates while preserving order
        seen = set()
        unique_deps = []
        for dep in base_deps:
            dep_name = dep.split("==")[0].split("[")[0]
            if dep_name not in seen:
                seen.add(dep_name)
                unique_deps.append(dep)

        return unique_deps

    def _extract_missing_dependencies(self, stderr: str) -> List[str]:
        """Extract missing dependency names from pytest stderr output."""
        missing_deps = []

        # Look for common patterns
        if "email-validator" in stderr:
            missing_deps.append("email-validator")
        if "no module named 'email_validator'" in stderr.lower():
            missing_deps.append("email-validator")
        if "pydantic[email]" in stderr:
            missing_deps.append("pydantic[email]")

        return missing_deps

    def _build_requirements_content(self, dependencies: List[str]) -> str:
        """Build the content for requirements.txt file."""
        header = "# Generated by BackendSWEA for managed system\n# Dependencies for BAE-generated academic management system\n\n"
        deps_content = "\n".join(dependencies)
        footer = "\n\n# Additional dependencies can be added here\n"

        return header + deps_content + footer

    def _write_requirements_to_managed_system(self, content: str) -> str:
        """Write requirements.txt to the managed system root."""
        # Ensure managed system structure exists
        self.managed_system_manager.ensure_managed_system_structure()

        managed_system_path = self.managed_system_manager.managed_system_path
        requirements_file = managed_system_path / "requirements.txt"

        # Write requirements file
        requirements_file.write_text(content)

        return str(requirements_file)
