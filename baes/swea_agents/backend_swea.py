import os
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient


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
        "generate_requirements": "_generate_requirements",
        "fix_dependencies": "_fix_dependencies",
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
    def _interpret_feedback_for_backend_generation(self, feedback: List[str], entity: str, code_type: str, original_attributes: List[str]) -> Dict[str, Any]:
        """
        Generic feedback interpretation using LLM to understand what backend code changes are needed.
        This approach can handle any type of feedback without hardcoded conditions.
        """
        if not feedback:
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "code_improvements": [],
                "modifications": []
            }

        feedback_text = "\n".join(feedback)
        
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
"""

        user_prompt = f"""Based on the feedback provided, what backend code improvements should be made for the {entity} entity's {code_type}?

Feedback to interpret:
{feedback_text}

Current attributes:
{original_attributes}

Please provide the JSON response with backend improvements."""

        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            
            # Try to parse JSON response
            import json
            try:
                interpretation = json.loads(response)
                return interpretation
            except json.JSONDecodeError:
                # Fallback: extract improvements from response text
                return self._extract_improvements_from_text(response, original_attributes)
                
        except Exception as e:
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

        # Interpret feedback generically using LLM
        interpretation = self._interpret_feedback_for_backend_generation(all_feedback, entity, "Pydantic Model", attributes)
        
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

        # Interpret feedback generically using LLM
        interpretation = self._interpret_feedback_for_backend_generation(all_feedback, entity, "FastAPI Routes", attributes)
        
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
        """Generate requirements.txt file with necessary dependencies for the managed system."""
        # entity = payload.get("entity", "Student")  # Currently unused
        fix_context = payload.get("fix_context", {})

        # Analyze what dependencies are needed based on fix context or general requirements
        required_deps = self._analyze_dependencies(payload, fix_context)

        # Generate requirements.txt content
        requirements_content = self._build_requirements_content(required_deps)

        # Write to managed system
        file_path = self._write_requirements_to_managed_system(requirements_content)

        return self.create_success_response(
            "generate_requirements",
            {
                "file_path": file_path,
                "dependencies": required_deps,
                "requirements_content": requirements_content,
                "managed_system": True,
                "fix_applied": bool(fix_context),
            },
        )

    def _fix_dependencies(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix dependency issues identified by TestSWEA."""
        fix_context = payload.get("fix_context", {})
        stderr = fix_context.get("test_stderr", "")

        # Analyze the specific dependency error
        missing_deps = self._extract_missing_dependencies(stderr)

        # Generate updated requirements
        return self._generate_requirements(
            {
                **payload,
                "additional_dependencies": missing_deps,
                "fix_context": fix_context,
            }
        )

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
