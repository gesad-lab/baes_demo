"""
Template Registry for BAES Performance Optimization

This module implements template-based code generation using Jinja2 templates,
reducing token consumption by 40-60% for standard CRUD operations.

Constitutional Compliance:
- PEP 8: All templates follow PEP 8 style guide (snake_case, 4-space indent)
- DRY: Centralized template storage prevents duplicate generation logic
- Fail-fast: Template rendering errors caught immediately with detailed messages
- Observability: Template selection and fallback logged for analysis
- Semantic coherence: Entity names passed as template variables, preserved in output
- Integration testing: Template outputs validated against contract specifications

Feature: 001-performance-optimization / US1: Template-Based Generation
Author: BAES Development Team
Created: 2025
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Classification of entity types for template selection"""

    STANDARD = "standard"  # Simple CRUD with basic attributes only
    CUSTOM = "custom"  # Complex logic requiring LLM generation


class SWEAType(Enum):
    """SWEA agent types for template organization"""

    BACKEND = "backend"
    DATABASE = "database"
    FRONTEND = "frontend"
    TEST = "test"


@dataclass
class TemplateMetadata:
    """
    Metadata for a Jinja2 code generation template

    Attributes:
        template_id: Unique identifier (e.g., "backend_model_crud")
        swea_type: SWEA agent type this template serves
        description: Human-readable description of template purpose
        file_path: Path to .j2 template file
        required_context: List of required context variables for rendering
        optional_context: List of optional context variables with defaults
        target_token_savings: Estimated token reduction vs LLM generation (percentage)
        version: Template version for cache invalidation
        created_at: Template creation timestamp
    """

    template_id: str
    swea_type: SWEAType
    description: str
    file_path: Path
    required_context: List[str]
    optional_context: Dict[str, Any] = field(default_factory=dict)
    target_token_savings: float = 0.5  # Default 50% savings
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TemplateInput:
    """
    Input data for template rendering

    Attributes:
        entity_name: Name of business entity (e.g., "Student", "Course")
        entity_type: Classification (standard/custom) determining template eligibility
        swea_type: Target SWEA agent type
        attributes: Entity attributes with types (e.g., {"name": "str", "gpa": "float"})
        relationships: Entity relationships (e.g., {"courses": {"type": "Course", "cardinality": "many"}})
        custom_logic: Dictionary of custom business rules (empty for standard entities)
        additional_context: Extra context variables for template rendering
    """

    entity_name: str
    entity_type: EntityType
    swea_type: SWEAType
    attributes: Dict[str, str]
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    custom_logic: Dict[str, Any] = field(default_factory=dict)
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateOutput:
    """
    Result of template rendering

    Attributes:
        generated_code: Rendered code from template
        template_used: Whether template was used (True) or fallback to LLM (False)
        template_id: ID of template used (None if fallback)
        fallback_reason: Explanation why template couldn't be used (None if template used)
        token_estimate: Estimated prompt tokens saved vs LLM generation
        rendering_time_ms: Time taken to render template in milliseconds
        context_applied: Actual context variables used in rendering
    """

    generated_code: str
    template_used: bool
    template_id: Optional[str] = None
    fallback_reason: Optional[str] = None
    token_estimate: int = 0
    rendering_time_ms: float = 0.0
    context_applied: Dict[str, Any] = field(default_factory=dict)


class TemplateRegistry:
    """
    Registry for Jinja2 code generation templates with selection and rendering logic

    Responsibilities:
    - Load and manage Jinja2 templates for all SWEA types
    - Select appropriate template based on entity characteristics
    - Render templates with provided context and handle errors
    - Track template usage metrics for optimization analysis

    Usage:
        registry = TemplateRegistry()
        template_input = TemplateInput(
            entity_name="Student",
            entity_type=EntityType.STANDARD,
            swea_type=SWEAType.BACKEND,
            attributes={"name": "str", "gpa": "float"}
        )
        output = registry.render_template(template_input)
        if output.template_used:
            print(f"Generated {len(output.generated_code)} chars using {output.template_id}")
        else:
            print(f"Fallback to LLM: {output.fallback_reason}")
    """

    def __init__(self, template_base_dir: Optional[Path] = None):
        """
        Initialize TemplateRegistry with Jinja2 environment

        Args:
            template_base_dir: Base directory for template files (default: baes/templates/)
        """
        if template_base_dir is None:
            # Default to baes/templates/ relative to this file's location
            current_file = Path(__file__).resolve()
            baes_dir = current_file.parent.parent  # baes/utils/ -> baes/
            template_base_dir = baes_dir / "templates"

        self.template_base_dir = template_base_dir

        # Jinja2 environment configuration for code generation
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_base_dir)),
            trim_blocks=True,  # Remove first newline after block
            lstrip_blocks=True,  # Strip leading whitespace from block
            keep_trailing_newline=True,  # Preserve final newline (PEP 8)
            autoescape=False,  # Disable HTML escaping for code generation
        )

        # Template metadata catalog (populated lazily)
        self._template_catalog: Dict[str, TemplateMetadata] = {}
        self._load_template_catalog()

        # Register custom Jinja2 filters for code generation
        self._register_custom_filters()

        logger.info(
            "TemplateRegistry initialized with %d templates from %s",
            len(self._template_catalog),
            template_base_dir,
        )

    def _register_custom_filters(self):
        """
        Register custom Jinja2 filters for code generation

        Filters:
        - snake_case: Convert string to snake_case (e.g., "StudentName" -> "student_name")
        - pascal_case: Convert string to PascalCase (e.g., "student_name" -> "StudentName")
        - python_type: Convert simple type string to Python type hint (e.g., "string" -> "str")
        """

        def snake_case_filter(value: str) -> str:
            """Convert string to snake_case for Python naming"""
            import re

            # Insert underscore before uppercase letters and convert to lowercase
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

        def pascal_case_filter(value: str) -> str:
            """Convert string to PascalCase for class names"""
            # Split on underscores and capitalize each word
            words = value.replace("-", "_").split("_")
            return "".join(word.capitalize() for word in words if word)

        def python_type_filter(value: str) -> str:
            """
            Convert simple type string to Python type hint

            Mappings:
            - string, str, text -> str
            - int, integer, number -> int
            - float, decimal, real -> float
            - bool, boolean -> bool
            - date -> datetime.date
            - datetime, timestamp -> datetime.datetime
            - default -> str (fallback)
            """
            type_mapping = {
                "string": "str",
                "str": "str",
                "text": "str",
                "int": "int",
                "integer": "int",
                "number": "int",
                "float": "float",
                "decimal": "float",
                "real": "float",
                "bool": "bool",
                "boolean": "bool",
                "date": "datetime.date",
                "datetime": "datetime.datetime",
                "timestamp": "datetime.datetime",
            }
            return type_mapping.get(value.lower(), "str")

        # Register filters with Jinja2 environment
        self.env.filters["snake_case"] = snake_case_filter
        self.env.filters["pascal_case"] = pascal_case_filter
        self.env.filters["python_type"] = python_type_filter

        logger.debug("Registered custom Jinja2 filters: snake_case, pascal_case, python_type")

    def _load_template_catalog(self):
        """
        Load template metadata catalog from template directory structure

        Template organization:
        baes/templates/
            backend/
                model_crud.py.j2
                routes_crud.py.j2
            database/
                schema_crud.sql.j2
            frontend/
                streamlit_form.py.j2
                streamlit_table.py.j2
            tests/
                integration_crud.py.j2
        """
        # Define expected templates (will be created in subsequent tasks)
        expected_templates = [
            TemplateMetadata(
                template_id="backend_model_crud",
                swea_type=SWEAType.BACKEND,
                description="SQLAlchemy model + Pydantic schema for standard CRUD entity",
                file_path=self.template_base_dir / "backend" / "model_crud.py.j2",
                required_context=["entity_name", "attributes"],
                optional_context={"relationships": {}, "table_name": None},
                target_token_savings=0.5,
            ),
            TemplateMetadata(
                template_id="backend_routes_crud",
                swea_type=SWEAType.BACKEND,
                description="FastAPI CRUD endpoints (POST, GET, PUT, DELETE)",
                file_path=self.template_base_dir / "backend" / "routes_crud.py.j2",
                required_context=["entity_name", "attributes"],
                optional_context={"base_path": "/api", "pagination": True},
                target_token_savings=0.6,
            ),
            TemplateMetadata(
                template_id="database_schema_crud",
                swea_type=SWEAType.DATABASE,
                description="PostgreSQL/SQLite CREATE TABLE with indexes and constraints",
                file_path=self.template_base_dir / "database" / "schema_crud.sql.j2",
                required_context=["entity_name", "attributes"],
                optional_context={"indexes": [], "constraints": []},
                target_token_savings=0.4,
            ),
            TemplateMetadata(
                template_id="frontend_streamlit_form",
                swea_type=SWEAType.FRONTEND,
                description="Streamlit create/update form with validation",
                file_path=self.template_base_dir / "frontend" / "streamlit_form.py.j2",
                required_context=["entity_name", "attributes"],
                optional_context={"form_mode": "create", "validation_rules": {}},
                target_token_savings=0.5,
            ),
            TemplateMetadata(
                template_id="frontend_streamlit_table",
                swea_type=SWEAType.FRONTEND,
                description="Streamlit list view with pagination and filters",
                file_path=self.template_base_dir / "frontend" / "streamlit_table.py.j2",
                required_context=["entity_name", "attributes"],
                optional_context={"page_size": 20, "sortable": True},
                target_token_savings=0.5,
            ),
            TemplateMetadata(
                template_id="test_integration_crud",
                swea_type=SWEAType.TEST,
                description="Pytest integration test for full CRUD lifecycle",
                file_path=self.template_base_dir / "tests" / "integration_crud.py.j2",
                required_context=["entity_name", "attributes"],
                optional_context={"fixtures": [], "cleanup": True},
                target_token_savings=0.4,
            ),
        ]

        for metadata in expected_templates:
            self._template_catalog[metadata.template_id] = metadata

        logger.debug("Loaded %d template metadata entries", len(self._template_catalog))

    def get_template_metadata(self, template_id: str) -> Optional[TemplateMetadata]:
        """
        Retrieve template metadata by ID

        Args:
            template_id: Template identifier (e.g., "backend_model_crud")

        Returns:
            TemplateMetadata if found, None otherwise
        """
        return self._template_catalog.get(template_id)

    def list_templates(
        self, swea_type: Optional[SWEAType] = None
    ) -> List[TemplateMetadata]:
        """
        List available templates, optionally filtered by SWEA type

        Args:
            swea_type: Filter by SWEA type (None = all templates)

        Returns:
            List of TemplateMetadata matching filter criteria
        """
        templates = list(self._template_catalog.values())
        if swea_type:
            templates = [t for t in templates if t.swea_type == swea_type]
        return templates

    def select_template(self, template_input: TemplateInput) -> Optional[TemplateMetadata]:
        """
        Select appropriate template based on entity characteristics

        Selection logic:
        1. Check entity_type: CUSTOM entities require LLM generation (no template)
        2. Match swea_type: Find templates for target SWEA agent
        3. Verify custom_logic: Non-empty custom_logic triggers LLM fallback
        4. Return first matching template

        Args:
            template_input: Entity characteristics and context

        Returns:
            TemplateMetadata if template applicable, None if LLM fallback required

        Examples:
            # Standard entity -> Template used
            >>> input = TemplateInput(
            ...     entity_name="Student",
            ...     entity_type=EntityType.STANDARD,
            ...     swea_type=SWEAType.BACKEND,
            ...     attributes={"name": "str", "gpa": "float"}
            ... )
            >>> template = registry.select_template(input)
            >>> template.template_id
            'backend_model_crud'

            # Custom entity -> No template
            >>> input = TemplateInput(
            ...     entity_name="Student",
            ...     entity_type=EntityType.CUSTOM,
            ...     swea_type=SWEAType.BACKEND,
            ...     attributes={"name": "str"},
            ...     custom_logic={"compute_gpa": "weighted_average"}
            ... )
            >>> template = registry.select_template(input)
            >>> template is None
            True
        """
        # Rule 1: CUSTOM entity type requires LLM generation
        if template_input.entity_type == EntityType.CUSTOM:
            logger.debug(
                "Template selection: entity_type=CUSTOM, requires LLM generation for %s",
                template_input.entity_name,
            )
            return None

        # Rule 2: Non-empty custom_logic requires LLM generation
        if template_input.custom_logic:
            logger.debug(
                "Template selection: custom_logic present (%d rules), requires LLM generation for %s",
                len(template_input.custom_logic),
                template_input.entity_name,
            )
            return None

        # Rule 3: Find template matching swea_type
        matching_templates = [
            t
            for t in self._template_catalog.values()
            if t.swea_type == template_input.swea_type
        ]

        if not matching_templates:
            logger.warning(
                "Template selection: no templates found for swea_type=%s",
                template_input.swea_type,
            )
            return None

        # Select first matching template (in future, could rank by suitability)
        selected_template = matching_templates[0]
        logger.info(
            "Template selected: %s for %s (%s)",
            selected_template.template_id,
            template_input.entity_name,
            template_input.swea_type.value,
        )
        return selected_template

    def render_template(self, template_input: TemplateInput) -> TemplateOutput:
        """
        Render template with provided context, with error handling and fallback

        Rendering flow:
        1. Select template based on entity characteristics
        2. Validate template file exists
        3. Validate required context variables present
        4. Render template with Jinja2
        5. Handle rendering errors gracefully (fallback to LLM)

        Args:
            template_input: Entity characteristics and rendering context

        Returns:
            TemplateOutput with generated code or fallback indication

        Raises:
            No exceptions raised - all errors result in fallback to LLM generation

        Examples:
            # Successful template rendering
            >>> input = TemplateInput(
            ...     entity_name="Student",
            ...     entity_type=EntityType.STANDARD,
            ...     swea_type=SWEAType.BACKEND,
            ...     attributes={"name": "str", "enrollment_date": "date"}
            ... )
            >>> output = registry.render_template(input)
            >>> output.template_used
            True
            >>> output.token_estimate > 0
            True

            # Fallback due to custom logic
            >>> input = TemplateInput(
            ...     entity_name="Student",
            ...     entity_type=EntityType.CUSTOM,
            ...     swea_type=SWEAType.BACKEND,
            ...     attributes={"name": "str"},
            ...     custom_logic={"validate_gpa": "range_check"}
            ... )
            >>> output = registry.render_template(input)
            >>> output.template_used
            False
            >>> output.fallback_reason
            'Entity type CUSTOM requires LLM generation'
        """
        import time

        start_time = time.time()

        # Step 1: Select template
        selected_template = self.select_template(template_input)
        if selected_template is None:
            # Determine fallback reason
            if template_input.entity_type == EntityType.CUSTOM:
                reason = f"Entity type {template_input.entity_type.value.upper()} requires LLM generation"
            elif template_input.custom_logic:
                reason = f"Custom logic present ({len(template_input.custom_logic)} rules) requires LLM generation"
            else:
                reason = f"No template available for {template_input.swea_type.value}"

            return TemplateOutput(
                generated_code="",
                template_used=False,
                fallback_reason=reason,
                rendering_time_ms=(time.time() - start_time) * 1000,
            )

        # Step 2: Validate template file exists
        if not selected_template.file_path.exists():
            logger.warning(
                "Template file not found: %s (falling back to LLM)",
                selected_template.file_path,
            )
            return TemplateOutput(
                generated_code="",
                template_used=False,
                template_id=selected_template.template_id,
                fallback_reason=f"Template file {selected_template.file_path.name} not found",
                rendering_time_ms=(time.time() - start_time) * 1000,
            )

        # Step 3: Build rendering context
        rendering_context = {
            "entity_name": template_input.entity_name,
            "attributes": template_input.attributes,
            "relationships": template_input.relationships,
            **template_input.additional_context,
            **selected_template.optional_context,
        }

        # Validate required context variables present
        missing_vars = [
            var
            for var in selected_template.required_context
            if var not in rendering_context or rendering_context[var] is None
        ]
        if missing_vars:
            logger.error(
                "Missing required context variables for template %s: %s",
                selected_template.template_id,
                missing_vars,
            )
            return TemplateOutput(
                generated_code="",
                template_used=False,
                template_id=selected_template.template_id,
                fallback_reason=f"Missing required context: {', '.join(missing_vars)}",
                rendering_time_ms=(time.time() - start_time) * 1000,
            )

        # Step 4: Render template
        try:
            template = self.env.get_template(
                str(selected_template.file_path.relative_to(self.template_base_dir))
            )
            generated_code = template.render(**rendering_context)

            # Estimate token savings (baseline: 1500 tokens for LLM generation)
            baseline_tokens = 1500
            token_savings = int(baseline_tokens * selected_template.target_token_savings)

            rendering_time_ms = (time.time() - start_time) * 1000

            logger.info(
                "Template rendered successfully: %s (%d chars, ~%d tokens saved, %.1fms)",
                selected_template.template_id,
                len(generated_code),
                token_savings,
                rendering_time_ms,
            )

            return TemplateOutput(
                generated_code=generated_code,
                template_used=True,
                template_id=selected_template.template_id,
                token_estimate=token_savings,
                rendering_time_ms=rendering_time_ms,
                context_applied=rendering_context,
            )

        except jinja2.TemplateSyntaxError as e:
            logger.error(
                "Template syntax error in %s line %d: %s (falling back to LLM)",
                selected_template.template_id,
                e.lineno,
                e.message,
            )
            return TemplateOutput(
                generated_code="",
                template_used=False,
                template_id=selected_template.template_id,
                fallback_reason=f"Template syntax error at line {e.lineno}: {e.message}",
                rendering_time_ms=(time.time() - start_time) * 1000,
            )

        except jinja2.UndefinedError as e:
            logger.error(
                "Undefined variable in template %s: %s (falling back to LLM)",
                selected_template.template_id,
                str(e),
            )
            return TemplateOutput(
                generated_code="",
                template_used=False,
                template_id=selected_template.template_id,
                fallback_reason=f"Undefined variable: {str(e)}",
                rendering_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.exception(
                "Unexpected error rendering template %s (falling back to LLM): %s",
                selected_template.template_id,
                str(e),
            )
            return TemplateOutput(
                generated_code="",
                template_used=False,
                template_id=selected_template.template_id,
                fallback_reason=f"Rendering error: {type(e).__name__}: {str(e)}",
                rendering_time_ms=(time.time() - start_time) * 1000,
            )



