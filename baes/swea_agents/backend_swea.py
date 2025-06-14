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

    # -------------------- task implementations ------------------------
    def _generate_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        prompt = self._build_prompt(entity, attributes, "Pydantic Model", context)
        code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="Pydantic Model",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "business_rules": payload.get("business_rules", []),
            },
        )

        file_path = self._write_to_managed_system(entity, "model", code)
        return self.create_success_response(
            "generate_model", {"file_path": file_path, "code": code, "managed_system": True}
        )

    def _generate_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entity = payload.get("entity", "Student")
        attributes = payload.get("attributes", [])
        context = payload.get("context", "academic")

        prompt = self._build_prompt(entity, attributes, "FastAPI Routes", context)
        code = self.llm_client.generate_code_with_domain_focus(
            prompt,
            code_type="FastAPI Routes",
            entity_context={
                "entity": entity,
                "attributes": attributes,
                "business_rules": payload.get("business_rules", []),
            },
        )

        file_path = self._write_to_managed_system(entity, "routes", code)
        return self.create_success_response(
            "generate_api", {"file_path": file_path, "code": code, "managed_system": True}
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
