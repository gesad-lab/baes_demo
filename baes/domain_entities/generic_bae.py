import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..agents.base_agent import BaseAgent
from ..llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class GenericBae(BaseAgent):
    """
    Generic Business Autonomous Entity that can adapt to represent different domain entities.
    Provides core BAE functionality while maintaining semantic coherence and supporting
    dynamic entity adaptation based on business requests.
    """

    def __init__(self, primary_entity: str = "Entity", name: Optional[str] = None):
        """
        Initialize Generic BAE with a primary entity focus but dynamic adaptation capability

        Args:
            primary_entity: The primary domain entity this BAE represents (e.g., "Student", "Book", "Course")
            name: Optional custom name for the BAE instance
        """
        bae_name = name or f"{primary_entity}BAE"
        super().__init__(bae_name, "Domain Entity Representative", "BAE")

        self.primary_entity = primary_entity
        self.current_entity = primary_entity  # Can adapt dynamically
        self.llm_client = OpenAIClient()

        # Entity-agnostic business vocabulary and domain knowledge
        self.business_vocabulary = self._initialize_business_vocabulary()
        self.domain_knowledge = {}
        self.current_schema = {}
        self.context_configurations = {}

        # Initialize with core domain knowledge
        self._initialize_domain_knowledge()
        logger.debug(
            f"{bae_name} initialized as {primary_entity} entity representative with dynamic adaptation"
        )

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle domain entity tasks while maintaining semantic coherence

        Supported tasks:
        - interpret_business_request: Parse natural language business requirements
        - generate_schema: Create Pydantic model for current entity
        - evolve_schema: Modify existing schema while preserving domain knowledge
        - configure_context: Adapt entity for different organizational contexts
        - coordinate_swea: Create coordination plan for SWEA agents
        - validate_domain_coherence: Ensure semantic consistency
        - adapt_entity: Change the current entity focus dynamically
        """

        task_handlers = {
            "interpret_business_request": self._interpret_business_request,
            "generate_schema": self._generate_schema,
            "evolve_schema": self._evolve_schema,
            "configure_context": self._configure_context,
            "coordinate_swea": self._coordinate_swea,
            "validate_domain_coherence": self._validate_domain_coherence,
            "validate_domain_rules": self._validate_domain_rules,  # Alias for coherence
            "get_domain_knowledge": self._get_domain_knowledge,
            "update_business_vocabulary": self._update_business_vocabulary,
            "adapt_entity": self._adapt_entity,
        }

        if task not in task_handlers:
            error_response = self.create_error_response(
                task, f"Unknown task. Supported tasks: {list(task_handlers.keys())}", "invalid_task"
            )
            error_response["supported_tasks"] = list(task_handlers.keys())
            return error_response

        try:
            start_time = datetime.now()
            result = task_handlers[task](payload)
            duration = (datetime.now() - start_time).total_seconds()

            # Add performance metrics
            if isinstance(result, dict) and result.get("success", False):
                result["performance"] = {
                    "duration_seconds": duration,
                    "task": task,
                    "timestamp": datetime.now().isoformat(),
                }

            return result

        except Exception as e:
            error_msg = f"Error executing task '{task}': {str(e)}"
            logger.error(f"{self.name}: {error_msg}")
            return self.create_error_response(task, error_msg, "execution_error")

    def _interpret_business_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret natural language business request with dynamic entity adaptation
        """
        # Validate required payload
        validation = self.validate_task_payload("interpret_business_request", payload, ["request"])
        if not validation["valid"]:
            return self.create_error_response("interpret_business_request", validation["error"])

        business_request = payload["request"]
        context = payload.get("context", "academic")

        logger.debug(f"{self.name} interpreting business request: {business_request}")

        # Use OpenAI to interpret the business request
        interpretation = self.llm_client.interpret_business_request(business_request, context)

        if interpretation.get("intent") == "parse_error":
            return self.create_error_response(
                "interpret_business_request",
                interpretation.get("error", "Failed to parse business request"),
            )

        # Dynamic entity adaptation based on interpretation
        detected_entity = interpretation.get("entity_focus", self.primary_entity)
        if detected_entity and detected_entity != self.current_entity:
            logger.debug(
                f"{self.name} adapting from {self.current_entity} to {detected_entity} entity"
            )
            self.current_entity = detected_entity

        # Extract attributes and create domain-focused plan
        attributes = interpretation.get("attributes_mentioned", self._get_default_attributes())
        business_vocab = interpretation.get("business_vocabulary", self.business_vocabulary)

        # Create SWEA coordination plan with correct entity focus
        coordination_plan = self._create_initial_generation_plan(
            attributes, context, business_vocab, self.current_entity
        )

        result_data = {
            "interpreted_intent": interpretation.get(
                "intent", f"manage_{self.current_entity.lower()}"
            ),
            "domain_operations": interpretation.get(
                "requested_operations", ["create", "read", "update", "delete"]
            ),
            "swea_coordination": coordination_plan,
            "business_vocabulary": business_vocab,
            "domain_attributes": attributes,
            "coordination_plan": coordination_plan,
            "entity_focus": self.current_entity,  # Use adapted entity
            "primary_entity": self.primary_entity,  # Original entity
            "context": context,
            "interpretation": interpretation,
            "entity_adapted": detected_entity != self.primary_entity,
        }

        # Update domain knowledge
        self._update_domain_knowledge_from_request(business_request, attributes, context)

        response = self.create_success_response("interpret_business_request", result_data)
        # Return result_data directly for test compatibility
        if response.get("success"):
            result_data.update(response.get("data", {}))
            return result_data
        return response

    def _adapt_entity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically adapt the BAE to represent a different entity"""
        new_entity = payload.get("entity")
        if not new_entity:
            return self.create_error_response("adapt_entity", "entity parameter is required")

        old_entity = self.current_entity
        self.current_entity = new_entity

        logger.debug(f"{self.name} adapted from {old_entity} to {new_entity}")

        return self.create_success_response(
            "adapt_entity",
            {
                "old_entity": old_entity,
                "new_entity": new_entity,
                "adaptation_timestamp": datetime.now().isoformat(),
            },
        )

    def _create_initial_generation_plan(
        self, attributes: List[str], context: str, business_vocab: List[str], entity: str
    ) -> List[Dict[str, Any]]:
        """Create SWEA coordination plan with correct entity focus"""

        entity_lower = entity.lower()
        entity_plural = self._pluralize_entity(entity_lower)

        plan = [
            {
                "step": 1,
                "agent": self.name,
                "task": "generate_schema",
                "payload": {
                    "attributes": attributes,
                    "context": context,
                    "business_vocabulary": business_vocab,
                    "entity": entity,
                },
                "description": f"Generate {entity} domain entity schema with semantic coherence",
                "domain_focus": True,
            },
            {
                "step": 2,
                "agent": "BackendSWEA",
                "task": "generate_api",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "business_vocabulary": business_vocab,
                    "domain_operations": ["create", "read", "update", "delete", "list"],
                },
                "description": f"Generate FastAPI backend with {entity} entity operations",
                "depends_on": [f"{self.name}.generate_schema"],
            },
            {
                "step": 3,
                "agent": "DatabaseSWEA",
                "task": "setup_database",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "persistence_requirements": ["durability", "consistency", "domain_integrity"],
                },
                "description": f"Create database schema for {entity} with business rule preservation",
                "depends_on": [f"{self.name}.generate_schema"],
            },
            {
                "step": 4,
                "agent": "FrontendSWEA",
                "task": "generate_ui",
                "payload": {
                    "entity": entity,
                    "attributes": attributes,
                    "context": context,
                    "business_vocabulary": business_vocab,
                    "user_workflows": [
                        f"create_{entity_lower}",
                        f"view_{entity_plural}",
                        f"edit_{entity_lower}",
                        f"remove_{entity_lower}",
                    ],
                },
                "description": f"Generate Streamlit UI for {entity} with business vocabulary",
                "depends_on": ["BackendSWEA.generate_api"],
            },
        ]

        return plan

    def _pluralize_entity(self, entity: str) -> str:
        """Simple pluralization for common entities"""
        if entity.endswith("y"):
            return entity[:-1] + "ies"
        elif entity.endswith(("s", "sh", "ch", "x", "z")):
            return entity + "es"
        else:
            return entity + "s"

    def _get_default_attributes(self) -> List[str]:
        """Get default attributes based on current entity"""
        entity_defaults = {
            "Student": ["name: str", "registration_number: str", "course: str"],
            "Book": ["title: str", "author: str", "ISBN: str"],
            "Course": ["name: str", "code: str", "credits: int"],
            "Teacher": ["name: str", "department: str", "email: str"],
        }
        return entity_defaults.get(self.current_entity, ["name: str", "id: str"])

    def _initialize_business_vocabulary(self) -> List[str]:
        """Initialize entity-agnostic business vocabulary"""
        return [
            "entity",
            "domain",
            "business",
            "academic",
            "management",
            "system",
            "operations",
            "data",
            "information",
        ]

    def _initialize_domain_knowledge(self):
        """Initialize domain knowledge for the entity"""
        self.domain_knowledge = {
            self.primary_entity: {
                "core_attributes": self._get_default_attributes(),
                "business_rules": [],
                "context": "academic",
                "initialized_timestamp": datetime.now().isoformat(),
            }
        }

    # Placeholder methods that specialized BAEs can override
    def _generate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate schema - to be implemented by specialized BAEs or use generic approach"""
        raise NotImplementedError("Specialized BAE should implement _generate_schema")

    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve schema - to be implemented by specialized BAEs"""
        raise NotImplementedError("Specialized BAE should implement _evolve_schema")

    def _configure_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Configure context - to be implemented by specialized BAEs"""
        raise NotImplementedError("Specialized BAE should implement _configure_context")

    def _coordinate_swea(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate SWEA - to be implemented by specialized BAEs"""
        raise NotImplementedError("Specialized BAE should implement _coordinate_swea")

    def _validate_domain_coherence(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate domain coherence - to be implemented by specialized BAEs"""
        raise NotImplementedError("Specialized BAE should implement _validate_domain_coherence")

    def _validate_domain_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate domain rules - to be implemented by specialized BAEs"""
        return self._validate_domain_coherence(payload)

    def _get_domain_knowledge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get domain knowledge - generic implementation"""
        context = payload.get("context", None)

        if context:
            knowledge = self.domain_knowledge.get(context, {})
        else:
            knowledge = self.domain_knowledge

        return self.create_success_response(
            "get_domain_knowledge",
            {
                "domain_knowledge": knowledge,
                "current_entity": self.current_entity,
                "primary_entity": self.primary_entity,
            },
        )

    def _update_business_vocabulary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update business vocabulary - generic implementation"""
        new_terms = payload.get("terms", [])
        self.business_vocabulary.extend(new_terms)
        self.business_vocabulary = list(set(self.business_vocabulary))  # Remove duplicates

        return self.create_success_response(
            "update_business_vocabulary",
            {"updated_vocabulary": self.business_vocabulary, "added_terms": new_terms},
        )

    def _update_domain_knowledge_from_request(
        self, request: str, attributes: List[str], context: str
    ):
        """Update domain knowledge based on business request"""
        if self.current_entity not in self.domain_knowledge:
            self.domain_knowledge[self.current_entity] = {}

        self.domain_knowledge[self.current_entity].update(
            {
                "last_request": request,
                "attributes": attributes,
                "context": context,
                "last_updated": datetime.now().isoformat(),
            }
        )
