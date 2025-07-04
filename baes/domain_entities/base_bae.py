import json
import logging
import os
import re
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.context_store import ContextStore
from ..llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


def is_debug_mode():
    """Check if debug mode is enabled"""
    return os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes")


class BaseBae(BaseAgent):
    """
    Base class for all Business Autonomous Entities (BAEs).

    BAEs represent domain entities as living, autonomous agents within the system,
    maintaining semantic coherence between business vocabulary and technical artifacts.
    This base class provides common functionality for all domain entity representatives.
    """

    def __init__(self, entity_name: str, domain_keywords: List[str]):
        super().__init__(f"{entity_name}BAE", "Domain Entity Representative", "BAE")
        self.llm = OpenAIClient()
        self.entity_name = entity_name
        self.domain_keywords = domain_keywords

        # Domain entity state
        self.current_schema = {}
        self.domain_knowledge = {}
        self.context_configurations = {}
        self.business_rules = []

        # Initialize domain-specific attributes
        self._initialize_domain_knowledge()

        # Load previously stored schema if available (for evolution detection after restart)
        self._load_stored_schema()

        logger.debug(f"{self.entity_name}BAE initialized with domain keywords: {domain_keywords}")

    def _load_stored_schema(self):
        """Load previously stored schema from persistent memory for evolution detection"""
        # Try to load from agent memory first
        stored_schema = self.get_memory("current_schema")
        if stored_schema:
            self.current_schema = stored_schema
            logger.debug(
                f"📥 Loaded stored schema for {self.entity_name} with "
                f"{len(stored_schema.get('attributes', []))} attributes: {stored_schema.get('attributes', [])}"
            )
            return

        # Try to load from context store agent memory
        context_store_path = os.environ.get(
            "BAE_CONTEXT_STORE_PATH", "database/context_store.json"
        )
        context_store = ContextStore(context_store_path)

        # Check for stored agent memory
        agent_memory = context_store.get_agent_memory(self.name)
        if agent_memory and isinstance(agent_memory, dict):
            # Context store memory has direct structure, but BaseAgent expects wrapped structure
            # Convert context store format to BaseAgent format
            for key, value in agent_memory.items():
                if key == "current_schema" and value:
                    # Found schema in context store, update our current schema directly
                    self.current_schema = value
                    # Also update memory in the BaseAgent format
                    self.update_memory("current_schema", value)
                    logger.debug(
                        f"📥 Restored schema for {self.entity_name} from context store with "
                        f"{len(value.get('attributes', []))} attributes: {value.get('attributes', [])}"
                    )
                    return

        # If no schema in memory, check context store for domain knowledge
        domain_knowledge = context_store.get_domain_knowledge(self.entity_name.lower())
        if domain_knowledge and isinstance(domain_knowledge, dict):
            interpretation = domain_knowledge.get("interpretation", {})
            if interpretation and interpretation.get("extracted_attributes"):
                stored_schema = {
                    "entity": self.entity_name,
                    "attributes": interpretation.get("extracted_attributes", []),
                    "context": domain_knowledge.get("context", "academic"),
                    "generated_at": domain_knowledge.get("timestamp", "unknown"),
                    "business_rules": interpretation.get("business_vocabulary", []),
                    "code": "",
                }
                self.current_schema = stored_schema
                self.update_memory("current_schema", stored_schema)
                logger.debug(
                    f"📥 Reconstructed schema for {self.entity_name} from domain knowledge with "
                    f"{len(stored_schema['attributes'])} attributes: {stored_schema['attributes']}"
                )
                return

        # No stored schema found - this is normal for fresh starts
        logger.debug(
            f"🆕 No stored schema found for {self.entity_name}, starting with empty schema"
        )
        self.current_schema = None

    @abstractmethod
    def _initialize_domain_knowledge(self):
        """Initialize domain-specific knowledge - must be implemented by concrete BAEs"""
        pass

    @abstractmethod
    def _get_business_rules(self) -> List[str]:
        """Get business rules for this domain entity - must be implemented by concrete BAEs"""
        pass

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain entity tasks - backward compatibility method"""
        return self.handle(task, payload)

    def handle(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain entity tasks maintaining semantic coherence"""
        task_handlers = {
            "interpret_business_request": self._interpret_business_request,
            "generate_schema": self._generate_schema,
            "evolve_schema": self._evolve_schema,
            "configure_context": self._configure_context,
            "coordinate_swea": self._coordinate_swea,
            "validate_domain_rules": self._validate_domain_rules,
            "get_domain_info": self._get_domain_info,
        }

        if task in task_handlers:
            try:
                result = task_handlers[task](payload)
                self.log_interaction(task, payload, result)
                logger.debug(f"{self.entity_name}BAE handled task: {task}")
                return result
            except Exception as e:
                error_result = {
                    "error": f"Failed to execute task {task}",
                    "details": str(e),
                    "entity": self.entity_name,
                }
                logger.error(f"{self.entity_name}BAE task failed: {task} - {str(e)}")
                return error_result
        else:
            return {
                "error": f"Unknown task: {task}",
                "supported_tasks": list(task_handlers.keys()),
                "entity": self.entity_name,
            }

    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract JSON from markdown code blocks"""
        # Remove markdown code blocks
        if "```json" in response:
            # Extract content between ```json and ```
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in response:
            # Extract content between ``` blocks
            pattern = r"```\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()

        return response.strip()

    def _detect_relationship_request(self, request: str) -> Dict[str, Any]:
        """Detect if this is a relationship creation request rather than entity creation/evolution"""
        request_lower = request.lower()
        
        # Relationship detection patterns
        relationship_patterns = [
            ("add a", "to", "entity"),
            ("add", "to the", "entity"),
            ("connect", "to", ""),
            ("link", "to", ""),
            ("relate", "to", ""),
            ("associate", "with", ""),
            ("assign", "to", ""),
        ]
        
        for pattern in relationship_patterns:
            if all(p in request_lower for p in pattern if p):
                # Extract entities involved in the relationship
                target_entity = None
                related_entity = None
                
                # Pattern: "Add a [course] to the [student] entity"
                if "add a" in request_lower and "to the" in request_lower and "entity" in request_lower:
                    import re
                    match = re.search(r'add a (\w+) to the (\w+) entity', request_lower)
                    if match:
                        related_entity = match.group(1)
                        target_entity = match.group(2)
                        
                        return {
                            "is_relationship": True,
                            "target_entity": target_entity.capitalize(),
                            "related_entity": related_entity.capitalize(),
                            "relationship_type": "foreign_key",
                            "description": f"Add {related_entity}_id foreign key to {target_entity} table"
                        }
        
        return {
            "is_relationship": False,
            "target_entity": None,
            "related_entity": None,
            "relationship_type": None,
            "description": None
        }

    def _handle_relationship_request(self, request: str, context: str, relationship_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle relationship creation request with proper DatabaseSWEA coordination"""
        target_entity = relationship_info["target_entity"]
        related_entity = relationship_info["related_entity"]
        
        logger.info(f"🔗 {self.entity_name}BAE: Handling relationship creation - {related_entity} -> {target_entity}")
        
        # For relationship creation, we don't change attributes of the entity
        # We just add a foreign key relationship
        existing_attributes_raw: List[Any] = []
        if self.current_schema and self.current_schema.get("attributes"):
            existing_attributes_raw = self.current_schema["attributes"]
        else:
            # If no current schema, try to load it or use default attributes
            self._load_stored_schema()
            if self.current_schema and self.current_schema.get("attributes"):
                existing_attributes_raw = self.current_schema["attributes"]
            else:
                existing_attributes_raw = self._get_default_attributes()

        existing_attributes = self._normalize_attributes(existing_attributes_raw)
        # ------------------------------------------------------------------
        # 🔗 Include foreign-key attribute so Backend/Frontend SWEAs generate
        #     proper models, API fields and form inputs.  Without this the UI
        #     will miss the relationship field even though the DB column
        #     exists (issue reported by user).
        # ------------------------------------------------------------------
        foreign_key_attr_name = f"{related_entity.lower()}_id"
        foreign_key_attr = {
            "name": foreign_key_attr_name,
            "type": "int",
            "is_foreign_key": True,
            "related_entity": related_entity.capitalize(),
            "descriptive_field": "name",  # Default assumption
        }


        # Ensure we do not duplicate if attribute already present
        if not any(attr.get("name") == foreign_key_attr_name for attr in existing_attributes):
            updated_attributes = existing_attributes + [foreign_key_attr]
        else:
            updated_attributes = existing_attributes
        
        # The relationship will be added by DatabaseSWEA._create_relationships
        # but the entity attributes should remain the same
        interpretation = {
            "entity": self.entity_name,
            "domain": getattr(self, 'domain', 'academic'),
            "attributes": updated_attributes,  # Include FK attribute for code generation
            "extracted_attributes": updated_attributes,
            "is_evolution": False,  # This is relationship creation, not evolution
            "request_type": "relationship",
            "business_context": request,
            "semantic_coherence": True,
            "domain_knowledge_preserved": True,
            "interpreted_intent": f"create_relationship_{related_entity.lower()}_to_{target_entity.lower()}",
            "domain_operations": ["create_relationship"],
            "business_vocabulary": self._extract_business_vocabulary(),
            "entity_focus": self.entity_name,
            "relationship_info": relationship_info,
        }
        
        # Create relationship-specific coordination plan
        interpretation["swea_coordination"] = [
            {
                "swea_agent": "TechLeadSWEA", 
                "task_type": "coordinate_system_generation",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": updated_attributes,
                    "context": request,
                    "is_evolution": False,
                    "is_relationship": True,
                    "relationship_info": relationship_info,
                    "business_requirements": {
                        "domain_focus": True,
                        "semantic_coherence": True,
                        "quality_gates": True,
                        "technical_governance": True,
                    },
                },
            },
            {
                "swea_agent": "DatabaseSWEA",
                "task_type": "create_relationships",  # Use relationship creation task
                "payload": {
                    "entity": self.entity_name,
                    "attributes": updated_attributes,
                    "context": request,
                    "relationships": [
                        {
                            "target_entity": relationship_info["related_entity"],
                            "relationship_type": relationship_info["relationship_type"],
                        }
                    ],
                    "preserve_data": True,
                },
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_api",  # Update API to include relationship
                "payload": {
                    "entity": self.entity_name,
                    "attributes": updated_attributes,
                    "context": request,
                    "relationship_update": True,
                    "relationships": [relationship_info],
                    "business_vocabulary": True,
                    "domain_focus": True,
                    "semantic_coherence": True,
                },
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": updated_attributes,
                    "context": request,
                    "relationship_update": True,
                    "relationships": [relationship_info],
                    "ui_framework": "streamlit",
                    "features": ["crud_operations", "data_visualization", "user_friendly"],
                },
            },
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "review_and_approve",
                "payload": {
                    "entity": self.entity_name,
                    "context": request,
                    "system_components": ["database", "backend", "frontend"],
                    "phase": "phase_1_complete",
                    "final_review": True,
                    "relationship_creation": True,
                },
            },
        ]
        
        return interpretation

    def _build_interpretation_prompt(self, request: str, context: str) -> str:
        """Builds a prompt for the LLM to interpret the business request."""
        return f"""
        As a BAE (Business Autonomous Entity), analyze the following request in the context of '{context}':

        Request: "{request}"

        Identify the main entity, its attributes (with types), and the requested operations (create, read, update, delete).
        Return a JSON object with the following structure:
        {{
            "entity_focus": "EntityName",
            "attributes_mentioned": [
                {{"name": "attribute_name", "type": "attribute_type"}}
            ],
            "requested_operations": ["operation1", "operation2"],
            "business_vocabulary": ["term1", "term2"],
            "is_evolution_request": false
        }}
        """

    def _interpret_business_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret business request and create SWEA coordination plan with TechLeadSWEA governance"""
        try:
            request = payload.get("request", "")
            context = payload.get("context", "academic")

            # First, check if this is a relationship creation request
            relationship_info = self._detect_relationship_request(request)

            if relationship_info["is_relationship"]:
                logger.info(
                    f"🔗 {self.entity_name}BAE: Detected relationship request - {relationship_info['description']}"
                )
                return self._handle_relationship_request(request, context, relationship_info)

            # Determine if this is evolution or new generation
            is_evolution = self._is_evolution_request(request)

            # Handle evolution requests differently than initial generation
            if is_evolution:
                # For evolution, we need to preserve existing attributes
                # Load current schema if available
                if self.current_schema:
                    current_schema = self.current_schema
                    if is_debug_mode():
                        logger.info(
                            f"🔍 {self.entity_name}BAE: Using cached schema with {len(current_schema.get('attributes', []))} attributes: {current_schema.get('attributes', [])}"
                        )
                else:
                    # Try to load from memory/context store
                    logger.info(f"🔍 {self.entity_name}BAE: Loading stored schema for evolution...")
                    self._load_stored_schema()
                    current_schema = self.current_schema or {"attributes": []}
                    if is_debug_mode():
                        logger.info(
                            f"🔍 {self.entity_name}BAE: Loaded schema with {len(current_schema.get('attributes', []))} attributes: {current_schema.get('attributes', [])}"
                        )

                # Use specialized evolution handling
                evolution_result = self._handle_evolution_request(
                    request, context, current_schema
                )

                if evolution_result:
                    # Use the evolution result which properly preserves existing attributes
                    extracted_attributes = evolution_result.get("extracted_attributes", [])
                    interpretation = {
                        "entity": self.entity_name,
                        "domain": getattr(self, "domain", "academic"),
                        "attributes": extracted_attributes,
                        "extracted_attributes": extracted_attributes,  # Add for consistency
                        "is_evolution": True,
                        "request_type": "evolution",
                        "business_context": request,
                        "semantic_coherence": True,
                        "domain_knowledge_preserved": True,
                        "interpreted_intent": evolution_result.get(
                            "interpreted_intent",
                            f"evolve_{self.entity_name.lower()}_management_system",
                        ),
                        "domain_operations": evolution_result.get(
                            "domain_operations", ["evolve_entity", "update_schema"]
                        ),
                        "business_vocabulary": self._extract_business_vocabulary(),
                        "entity_focus": self.entity_name,
                        # Include evolution-specific metadata
                        "new_attributes": evolution_result.get("new_attributes", []),
                        "existing_attributes": evolution_result.get("existing_attributes", []),
                        "evolution_type": evolution_result.get("evolution_type", "addition"),
                    }
                else:
                    # Fallback if evolution handling fails
                    extracted_attributes = self._extract_attributes_from_request(request)
                    interpretation = {
                        "entity": self.entity_name,
                        "domain": getattr(self, "domain", "academic"),
                        "attributes": extracted_attributes,
                        "extracted_attributes": extracted_attributes,  # Add for consistency
                        "is_evolution": True,
                        "request_type": "evolution",
                        "business_context": request,
                        "semantic_coherence": True,
                        "domain_knowledge_preserved": True,
                        "interpreted_intent": f"evolve_{self.entity_name.lower()}_management_system",
                        "domain_operations": ["evolve_entity", "update_schema"],
                        "business_vocabulary": self._extract_business_vocabulary(),
                        "entity_focus": self.entity_name,
                    }
            else:
                # This is for initial generation from business request
                prompt = self._build_interpretation_prompt(request, context)
                interpretation_str = self.llm.generate_response(prompt)

                try:
                    interpretation = json.loads(self._clean_json_response(interpretation_str))
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from LLM response: {interpretation_str}")
                    # Create a fallback interpretation
                    interpretation = {
                        "entity_focus": self.entity_name,
                        "attributes_mentioned": self._get_default_attributes(),
                        "requested_operations": ["create", "read", "update", "delete"],
                        "business_vocabulary": [],
                        "is_evolution_request": False,
                    }

                # Get attributes, with fallback to default
                raw_attributes = interpretation.get("attributes_mentioned")
                if not raw_attributes:
                    raw_attributes = self._get_default_attributes()
                attributes = self._normalize_attributes(raw_attributes)
                extracted_attributes = attributes

                # Store the latest schema after successful interpretation
                self.current_schema = {
                    "entity": self.entity_name,
                    "attributes": attributes,
                    "context": context,
                    "generated_at": datetime.now().isoformat(),
                    "business_rules": self._get_business_rules(),
                    "is_evolution": is_evolution,
                    "interpretation": interpretation,  # Store full interpretation for debugging
                }

            # Create comprehensive coordination plan with TechLeadSWEA governance
            interpretation["swea_coordination"] = [
                {
                    "swea_agent": "TechLeadSWEA",
                    "task_type": "coordinate_system_generation",
                    "payload": {
                        "entity": self.entity_name,
                        "attributes": extracted_attributes,
                        "context": request,
                        "is_evolution": is_evolution,
                        "business_requirements": {
                            "domain_focus": True,
                            "semantic_coherence": True,
                            "quality_gates": True,
                            "technical_governance": True,
                        },
                    },
                },
                {
                    "swea_agent": "DatabaseSWEA",
                    "task_type": "migrate_schema" if is_evolution else "setup_database",
                    "payload": {
                        "entity": self.entity_name,
                        "attributes": extracted_attributes,
                        "context": request,
                        "preserve_data": is_evolution,
                        "business_rules": True,
                    },
                },
                {
                    "swea_agent": "BackendSWEA",
                    "task_type": "generate_model",
                    "payload": {
                        "entity": self.entity_name,
                        "attributes": extracted_attributes,
                        "context": request,
                        "business_vocabulary": True,
                        "domain_focus": True,
                        "semantic_coherence": True,
                    },
                },
                {
                    "swea_agent": "BackendSWEA",
                    "task_type": "generate_api",
                    "payload": {
                        "entity": self.entity_name,
                        "attributes": extracted_attributes,
                        "context": request,
                        "crud_operations": True,
                        "business_vocabulary": True,
                        "domain_focus": True,
                        "semantic_coherence": True,
                    },
                },
                {
                    "swea_agent": "FrontendSWEA",
                    "task_type": "generate_ui",
                    "payload": {
                        "entity": self.entity_name,
                        "attributes": extracted_attributes,
                        "context": request,
                        "ui_framework": "streamlit",
                        "features": ["crud_operations", "data_visualization", "user_friendly"],
                    },
                },
                {
                    "swea_agent": "TechLeadSWEA",
                    "task_type": "review_and_approve",
                    "payload": {
                        "entity": self.entity_name,
                        "context": request,
                        "system_components": ["database", "backend", "frontend"],
                        "phase": "phase_1_complete",
                        "final_review": True,
                    },
                },
            ]

            # Validate coordination plan before returning
            validation_errors = self._validate_coordination_plan(
                interpretation["swea_coordination"]
            )
            if validation_errors:
                logger.error(
                    f"❌ {self.entity_name}BAE: Coordination plan validation failed: {validation_errors}"
                )
                return {
                    "error": f"Coordination plan validation failed: {validation_errors}",
                    "entity": self.entity_name,
                    "validation_errors": validation_errors,
                }

            # Preserve domain knowledge for reusability
            self._update_domain_knowledge(context, extracted_attributes)
            
            # CRITICAL: Update current schema with the latest attributes for future evolution requests
            # This ensures the next evolution request can access the current attributes
            updated_schema = {
                "entity": self.entity_name,
                "attributes": extracted_attributes,
                "context": context,
                "generated_at": datetime.now().isoformat(),
                "business_rules": self._get_business_rules(),
                "is_evolution": is_evolution,
                "interpretation": interpretation,  # Store full interpretation for debugging
            }
            
            # Save to both current_schema and memory
            self.current_schema = updated_schema
            self.update_memory("current_schema", updated_schema)
            
            # Also save to context store for persistence across BAE instances
            try:
                context_store_path = os.environ.get(
                    "BAE_CONTEXT_STORE_PATH", "database/context_store.json"
                )
                context_store = ContextStore(context_store_path)
                
                # Preserve domain knowledge with updated attributes
                domain_knowledge_data = {
                    "entity": self.entity_name,
                    "context": context,
                    "timestamp": datetime.now().isoformat(),
                    "interpretation": interpretation,
                    "current_attributes": extracted_attributes,
                }
                context_store.preserve_domain_knowledge(
                    self.entity_name.lower(), domain_knowledge_data
                )
                
                # Also update agent memory in context store
                context_store.update_agent_memory_key(self.name, "current_schema", updated_schema)
                
                if is_debug_mode():
                    logger.info(
                        f"💾 {self.entity_name}BAE: Saved schema with {len(extracted_attributes)} attributes to context store"
                    )
                    
            except Exception as e:
                logger.warning(f"⚠️  {self.entity_name}BAE: Could not save to context store: {str(e)}")

            if is_debug_mode():
                logger.info(
                    f"✅ {self.entity_name}BAE: Interpreted request with {len(extracted_attributes)} attributes "
                    f"and {len(interpretation['swea_coordination'])} SWEA tasks"
                )
                logger.info(f"🔍 Current attributes: {extracted_attributes}")

            return interpretation

        except Exception as e:
            logger.error(f"❌ {self.entity_name}BAE: Error interpreting business request: {str(e)}")
            return {
                "error": f"Failed to interpret business request: {str(e)}",
                "entity": self.entity_name,
                "details": str(e),
            }

    def _validate_coordination_plan(self, coordination_plan: List[Dict[str, Any]]) -> List[str]:
        """
        Validate that coordination plan has all mandatory attributes.
        Returns list of validation errors, empty if valid.
        """
        errors = []

        if not coordination_plan:
            errors.append("Coordination plan is empty")
            return errors

        for i, task in enumerate(coordination_plan):
            task_prefix = f"Task {i+1}"

            # Check mandatory attributes
            if not task.get("swea_agent"):
                errors.append(f"{task_prefix}: Missing 'swea_agent'")
            elif not task.get("swea_agent").strip():
                errors.append(f"{task_prefix}: 'swea_agent' cannot be empty")

            if not task.get("task_type"):
                errors.append(f"{task_prefix}: Missing 'task_type'")
            elif not task.get("task_type").strip():
                errors.append(f"{task_prefix}: 'task_type' cannot be empty")

            if "payload" not in task:
                errors.append(f"{task_prefix}: Missing 'payload'")
            elif not isinstance(task.get("payload"), dict):
                errors.append(f"{task_prefix}: 'payload' must be a dictionary")
            else:
                # Validate payload content for entity-related tasks
                payload = task.get("payload", {})
                task_type = task.get("task_type", "")

                if task_type in [
                    "generate_model",
                    "generate_api",
                    "generate_ui",
                    "setup_database",
                    "migrate_schema",
                ]:
                    if not payload.get("entity") and not payload.get("entity_name"):
                        errors.append(
                            f"{task_prefix}: Entity-related task '{task_type}' missing entity information in payload"
                        )

        return errors

    def _handle_evolution_request(
        self, business_request: str, context: str, current_attributes: List[str]
    ) -> Dict[str, Any]:
        """Handle evolution requests that modify existing entities"""
        current_attributes = current_schema.get("attributes", [])
        request_lower = business_request.lower()

        # Handle different types of evolution
        if any(
            keyword in request_lower
            for keyword in [
                "add",
                "include",
                "extend",
                "additional",
                "new",
                "create",
                "insert",
            ]
        ):
            return self._handle_addition_evolution(business_request, context, current_attributes)
        
        elif any(
            keyword in request_lower
            for keyword in [
                "remove",
                "delete",
                "drop",
                "eliminate",
            ]
        ):
            return self._handle_removal_evolution(business_request, context, current_attributes)
        
        elif any(
            keyword in request_lower
            for keyword in [
                "modify",
                "update",
                "change",
                "alter",
                "rename",
            ]
        ):
            return self._handle_modification_evolution(business_request, context, current_attributes)
        
        else:
            # Handle complex operations or fallback to addition
            # Check if it might be a complex request with multiple operations
            has_multiple_ops = (
                sum(1 for keyword in ["add", "remove", "modify", "change", "update", "delete"] 
                    if keyword in request_lower) > 1
            )
            
            if has_multiple_ops:
                return self._handle_complex_evolution(business_request, context, current_attributes)
            else:
                # Default to addition evolution for unclear requests
                return self._handle_addition_evolution(business_request, context, current_attributes)

    def _handle_addition_evolution(
        self, business_request: str, context: str, current_attributes: List[str]
    ) -> Dict[str, Any]:
        """Handle adding new attributes to existing entity"""
        logger.info(f"🔍 {self.entity_name}BAE: Adding attributes to existing entity")
        logger.info(f"📋 Current attributes: {current_attributes}")
        logger.info(f"📝 Request: {business_request}")
        prompt = f"""
        As the {self.entity_name} BAE, analyze this attribute addition request:

        Request: "{business_request}"
        Current {self.entity_name} attributes: {current_attributes}

        Extract ONLY the NEW attributes that should be ADDED to the existing entity.
        Look for field names like:
        - "email" or "email address" -> "email: str"
        - "age" -> "age: int"
        - "birth date" -> "birth_date: date"
        - "phone" or "phone number" -> "phone: str"

        Return a simple JSON list of new attributes to add:
        ["new_attribute1: type", "new_attribute2: type"]

        For example, if the request is "add email address", return: ["email: str"]
        """
        response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        cleaned_response = self._clean_json_response(response)
        new_attributes = json.loads(cleaned_response)
        if not isinstance(new_attributes, list):
            raise ValueError(f"LLM did not return a list of new attributes: {new_attributes}")
        # Filter out attributes that already exist
        existing_attr_names = [attr.split(":")[0].strip() for attr in current_attributes]
        new_attributes = [attr for attr in new_attributes if attr.split(":")[0].strip() not in existing_attr_names]
        all_attributes = current_attributes + new_attributes
        logger.info(f"✅ {self.entity_name}BAE: Addition evolution result:")
        logger.info(f"   📋 Existing attributes: {current_attributes}")
        logger.info(f"   🆕 New attributes: {new_attributes}")
        logger.info(f"   🔄 Combined attributes: {all_attributes}")
        return {
            "entity": self.entity_name,
            "interpreted_intent": f"Add attributes to existing {self.entity_name} entity: {', '.join(new_attributes)}",
            "extracted_attributes": all_attributes,
            "new_attributes": new_attributes,
            "existing_attributes": current_attributes,
            "domain_operations": ["evolve_entity"],
            "is_evolution": True,
            "evolution_type": "addition",
            "request_type": "evolution",
            "swea_coordination": self._create_evolution_coordination_plan(all_attributes),
            "business_vocabulary": [self.entity_name.lower()]
            + [attr.split(":")[0].strip() for attr in new_attributes],
            "entity_focus": self.entity_name,
        }

    def _handle_removal_evolution(
        self, business_request: str, context: str, current_attributes: List[str]
    ) -> Dict[str, Any]:
        """Handle removing attributes from existing entity"""
        prompt = f"""
        As the {self.entity_name} BAE, analyze this attribute removal request:

        Request: "{business_request}"
        Current {self.entity_name} attributes: {current_attributes}

        Identify which attributes should be REMOVED from the entity.
        Return a simple JSON list of attribute names (without types) to remove:
        ["attribute_name1", "attribute_name2"]

        For example, if the request is "remove age attribute", return: ["age"]
        If the request is "remove age and course", return: ["age", "course"]
        """

        response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        cleaned_response = self._clean_json_response(response)

        try:
            attributes_to_remove = json.loads(cleaned_response)
            if not isinstance(attributes_to_remove, list):
                attributes_to_remove = []
        except json.JSONDecodeError:
            # Extract attributes manually as fallback
            attributes_to_remove = []
            for attr in current_attributes:
                attr_name = attr.split(":")[0].strip()
                if attr_name.lower() in business_request.lower():
                    attributes_to_remove.append(attr_name)

        # Remove specified attributes
        remaining_attributes = []
        removed_attributes = []

        for attr in current_attributes:
            attr_name = attr.split(":")[0].strip()
            if attr_name not in attributes_to_remove:
                remaining_attributes.append(attr)
            else:
                removed_attributes.append(attr)

        return {
            "entity": self.entity_name,
            "interpreted_intent": (
                f"Remove attributes from {self.entity_name} entity: {', '.join(attributes_to_remove)}"
            ),
            "extracted_attributes": remaining_attributes,
            "removed_attributes": removed_attributes,
            "existing_attributes": current_attributes,
            "domain_operations": ["evolve_entity"],
            "is_evolution": True,
            "evolution_type": "removal",
            "request_type": "evolution",
            "swea_coordination": self._create_evolution_coordination_plan(remaining_attributes),
            "business_vocabulary": [self.entity_name.lower()],
            "entity_focus": self.entity_name,
        }

    def _handle_modification_evolution(
        self, business_request: str, context: str, current_attributes: List[str]
    ) -> Dict[str, Any]:
        """Handle modifying existing attributes"""
        prompt = f"""
        As the {self.entity_name} BAE, analyze this attribute modification request:

        Request: "{business_request}"
        Current {self.entity_name} attributes: {current_attributes}

        Identify what modifications should be made to existing attributes.
        Return a JSON object with the modifications:
        {{
            "modifications": [
                {{"old": "attribute_name: old_type", "new": "attribute_name: new_type", "change": "description"}},
                {{"old": "old_name: type", "new": "new_name: type", "change": "rename"}}
            ]
        }}

        For example:
        - "change age from int to str" -> {{"old": "age: int", "new": "age: str", "change": "type_change"}}
        - "rename registration_number to student_id" -> {{"old": "registration_number: str",
             "new": "student_id: str",
             "change": "rename"}}
        """

        response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        cleaned_response = self._clean_json_response(response)

        try:
            modification_data = json.loads(cleaned_response)
            modifications = modification_data.get("modifications", [])
        except json.JSONDecodeError:
            # Extract modifications manually as fallback
            modifications = []
            request_lower = business_request.lower()

            # Handle common modification patterns
            for attr in current_attributes:
                attr_name = attr.split(":")[0].strip()
                attr_type = attr.split(":")[1].strip() if ":" in attr else "str"

                if f"change {attr_name}" in request_lower or f"modify {attr_name}" in request_lower:
                    if "to str" in request_lower:
                        modifications.append(
                            {"old": attr, "new": f"{attr_name}: str", "change": "type_change"}
                        )
                    elif "to int" in request_lower:
                        modifications.append(
                            {"old": attr, "new": f"{attr_name}: int", "change": "type_change"}
                        )
                elif f"rename {attr_name}" in request_lower:
                    # Extract new name (simplified)
                    if "to " in request_lower:
                        new_name = request_lower.split("to ")[1].split()[0]
                        modifications.append(
                            {"old": attr, "new": f"{new_name}: {attr_type}", "change": "rename"}
                        )

        # Apply modifications
        modified_attributes = current_attributes.copy()
        modification_summary = []

        for mod in modifications:
            old_attr = mod.get("old", "")
            new_attr = mod.get("new", "")
            change = mod.get("change", "")

            if old_attr in modified_attributes:
                idx = modified_attributes.index(old_attr)
                modified_attributes[idx] = new_attr
                modification_summary.append(f"{change}: {old_attr} -> {new_attr}")

        return {
            "entity": self.entity_name,
            "interpreted_intent": (
                f"Modify attributes in {self.entity_name} entity: {'; '.join(modification_summary)}"
            ),
            "extracted_attributes": modified_attributes,
            "modifications": modifications,
            "existing_attributes": current_attributes,
            "domain_operations": ["evolve_entity"],
            "is_evolution": True,
            "evolution_type": "modification",
            "swea_coordination": self._create_evolution_coordination_plan(modified_attributes),
            "business_vocabulary": [self.entity_name.lower()],
            "entity_focus": self.entity_name,
        }

    def _extract_attributes_from_request(self, request: str) -> List[str]:
        """Extract attributes from natural language request"""
        import re
        common_attributes = {
            "name": "name: str",
            "email": "email: str",
            "age": "age: int",
            "phone": "phone: str",
            "address": "address: str",
            "birth": "birth_date: date",
            "grade": "grade_point_average: float",
            "registration": "registration_number: str",
            "course": "course: str",
            "enrollment": "enrollment_date: date",
        }
        extracted = []
        request_lower = request.lower()
        for keyword, attribute in common_attributes.items():
            # Use word boundary matching to avoid false positives (e.g., "age" in "manage")
            if re.search(r'\b' + re.escape(keyword) + r'\b', request_lower):
                extracted.append(attribute)
        
        # Always add 'id' if not present - it's required for database operations
        if not any(attr.startswith("id:") for attr in extracted):
            extracted.insert(0, "id: int")
        
        if not extracted or len(extracted) == 1:  # Only id was added
            # For initial generation, use ONLY the basic attributes when none are specified
            if not self._is_evolution_request(request):
                logger.info(f"{self.entity_name}BAE: No specific attributes found in request, using minimal default attributes")
                # Return only basic entity attributes - don't assume extra fields
                if self.entity_name.lower() == "student":
                    return ["id: int", "name: str"]  # Minimal student attributes
                elif self.entity_name.lower() == "course":
                    return ["id: int", "name: str"]  # Minimal course attributes  
                elif self.entity_name.lower() == "teacher":
                    return ["id: int", "name: str"]  # Minimal teacher attributes
                else:
                    return ["id: int", "name: str"]  # Minimal generic attributes
            else:
                raise ValueError(f"No attributes could be extracted from request: {request}")
        return extracted

    def _is_evolution_request(self, request: str) -> bool:
        """Determine if this is an evolution request"""
        request_lower = request.lower()

        # Check for attribute evolution keywords
        evolution_keywords = [
            "modify",
            "update",
            "change",
            "remove",
            "delete",
            "extend",
            "enhance",
            "alter",
            "rename",
        ]

        # Check for attribute addition patterns (evolution)
        attribute_addition_patterns = [
            "add attribute",
            "add field",
            "add property",
            "include attribute",
            "include field",
            "add email to",
            "add phone to",
            "add address to",
        ]
        
        # Check for "add X as attribute" patterns (more flexible matching)
        add_as_attribute_patterns = [
            "as attribute",
            "as field", 
            "as property",
        ]

        # Check for basic "add" + attribute keywords
        has_add = "add" in request_lower
        has_attribute_keyword = any(attr_word in request_lower for attr_word in ["attribute", "field", "property", "column"])

        # Additional heuristic: detect "include" statements that mention an attribute/field even if the
        # exact phrase "include attribute" is not present (e.g. "include the \"email\" attribute").
        has_include = "include" in request_lower

        # Check for evolution patterns (broadened to catch more natural-language variants)
        return (
            any(keyword in request_lower for keyword in evolution_keywords)
            or any(pattern in request_lower for pattern in attribute_addition_patterns)
            or any(pattern in request_lower for pattern in add_as_attribute_patterns)
            or (has_add and has_attribute_keyword)
            or (has_include and has_attribute_keyword)
        )

    def _get_default_attributes(self) -> List[Any]:
        """
        Get default attributes for this domain entity.
        Must be implemented by concrete BAEs.
        """
        # Use entity-specific BAE implementation if available, otherwise use minimal defaults
        if hasattr(self, '_get_entity_specific_defaults'):
            return self._get_entity_specific_defaults()
        
        # Fallback to minimal attributes - don't assume extra fields
        if self.entity_name.lower() == "student":
            return ["name: str", "email: str"]  # Removed age - only include if explicitly requested
        elif self.entity_name.lower() == "course":
            return ["name: str", "code: str"]
        elif self.entity_name.lower() == "teacher":
            return ["name: str", "email: str"]
        else:
            return ["name: str", "description: str"]

    def _handle_complex_evolution(
        self, business_request: str, context: str, current_attributes: List[str]
    ) -> Dict[str, Any]:
        """Handle complex evolution requests with multiple operations"""
        prompt = f"""
        As the {self.entity_name} BAE, analyze this complex evolution request that contains multiple operations:

        Request: "{business_request}"
        Current {self.entity_name} attributes: {current_attributes}

        This request contains multiple operations. Analyze and return a JSON object with:
        {{
            "operations": [
                {{"type": "add", "attributes": ["new_attr: type"]}},
                {{"type": "remove", "attributes": ["attr_name"]}},
                {{"type": "modify", "old": "old_attr: old_type", "new": "new_attr: new_type"}}
            ]
        }}

        Identify all operations in the request and list them separately.
        """

        response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        cleaned_response = self._clean_json_response(response)

        try:
            operation_data = json.loads(cleaned_response)
            operations = operation_data.get("operations", [])
        except json.JSONDecodeError:
            # Fallback: parse manually
            operations = []
            request_lower = business_request.lower()

            # Simple pattern matching for complex requests
            if "add" in request_lower and "remove" in request_lower:
                # Extract add operations
                if "email" in request_lower:
                    operations.append({"type": "add", "attributes": ["email: str"]})
                # Extract remove operations
                if "age" in request_lower and "remove" in request_lower:
                    operations.append({"type": "remove", "attributes": ["age"]})
                # Extract modify operations
                if (
                    "change" in request_lower
                    and "course" in request_lower
                    and "program" in request_lower
                ):
                    operations.append(
                        {"type": "modify", "old": "course: str", "new": "program: str"}
                    )

        # Apply operations in sequence
        result_attributes = current_attributes.copy()
        operation_summary = []

        for op in operations:
            op_type = op.get("type", "")

            if op_type == "add":
                new_attrs = op.get("attributes", [])
                result_attributes.extend(new_attrs)
                operation_summary.append(f"Added: {', '.join(new_attrs)}")

            elif op_type == "remove":
                attrs_to_remove = op.get("attributes", [])
                for attr_name in attrs_to_remove:
                    result_attributes = [
                        attr
                        for attr in result_attributes
                        if not attr.split(":")[0].strip() == attr_name
                    ]
                operation_summary.append(f"Removed: {', '.join(attrs_to_remove)}")

            elif op_type == "modify":
                old_attr = op.get("old", "")
                new_attr = op.get("new", "")
                if old_attr in result_attributes:
                    idx = result_attributes.index(old_attr)
                    result_attributes[idx] = new_attr
                    operation_summary.append(f"Modified: {old_attr} -> {new_attr}")

        return {
            "entity": self.entity_name,
            "interpreted_intent": f"Complex evolution of {self.entity_name} entity: {'; '.join(operation_summary)}",
            "extracted_attributes": result_attributes,
            "operations": operations,
            "existing_attributes": current_attributes,
            "domain_operations": ["evolve_entity"],
            "is_evolution": True,
            "evolution_type": "complex",
            "swea_coordination": self._create_evolution_coordination_plan(result_attributes),
            "business_vocabulary": [self.entity_name.lower()],
            "entity_focus": self.entity_name,
        }

    def _create_evolution_coordination_plan(self, attributes: List[str]) -> List[Dict[str, Any]]:
        """Create coordination plan for evolution with given attributes"""
        return [
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "coordinate_system_generation",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": attributes,
                    "is_evolution": True,
                },
            },
            {
                "swea_agent": "DatabaseSWEA",
                "task_type": "migrate_schema",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": attributes, 
                    "is_evolution": True,
                    "preserve_data": True,
                },
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "payload": {"attributes": attributes, "is_evolution": True},
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_api",
                "payload": {"attributes": attributes, "is_evolution": True},
            },
            {
                "swea_agent": "FrontendSWEA",
                "task_type": "generate_ui",
                "payload": {"attributes": attributes, "is_evolution": True},
            },
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "review_and_approve",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": attributes,
                    "is_evolution": True,
                },
            },
        ]

    def _generate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate schema based on attributes and context"""
        context = payload.get("context", "academic")
        
        # Normalize attributes to the new dictionary format
        raw_attributes = payload.get("attributes", self._get_default_attributes())
        attributes = self._normalize_attributes(raw_attributes)

        schema = {
            "entity": self.entity_name,
            "code": "", # Will be filled by LLM
            "attributes": attributes,
            "context": context,
            "business_rules": self._get_business_rules(),
            "generated_at": datetime.now().isoformat(),
        }

        prompt = f"""
        Generate a Pydantic model for {self.entity_name} entity with these attributes:
        {', '.join([f"{attr['name']}: {attr['type']}" for attr in attributes])}

        Context: {context}
        Business Rules: {'; '.join(self._get_business_rules())}

        Requirements:
        1. Create a Python class named "{self.entity_name}" using Pydantic BaseModel
        2. Include appropriate type hints reflecting domain understanding
        3. Add validation rules that preserve business domain rules
        4. Include meaningful docstrings that reflect domain entity knowledge
        5. Focus on domain entity representation and semantic coherence
        6. Must be easily evolvable to support runtime adaptation

        Return ONLY the complete Python code for the Pydantic model.
        """

        schema_code = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        schema["code"] = schema_code

        self.current_schema = schema
        self.update_memory("current_schema", schema)
        self._update_domain_knowledge(context, attributes)

        return schema

    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve schema while preserving domain knowledge and semantic coherence"""
        evolution_request = payload.get("evolution_request", "")
        new_attributes = payload.get("new_attributes", [])

        current_schema = self.get_memory("current_schema")
        if not current_schema:
            # Generate initial schema if none exists
            return self._generate_schema(
                {"attributes": new_attributes, "context": payload.get("context", "academic")}
            )

        prompt = f"""
        As the {self.entity_name} BAE, evolve the current {self.entity_name} entity schema:

        Current Schema Code:
        {current_schema.get('code', '')}

        Current Context: {current_schema.get('context', 'academic')}
        Current Attributes: {current_schema.get('attributes', [])}
        Business Rules: {'; '.join(self._get_business_rules())}

        Evolution Request: {evolution_request}
        New Attributes to Add: {new_attributes}

        Generate the evolved Pydantic model code while:
        1. Preserving existing domain knowledge and business rules
        2. Maintaining semantic coherence with business vocabulary
        3. Ensuring compatibility with existing data
        4. Adding new attributes with appropriate domain validation
        5. Keeping the focus on {self.entity_name} domain entity

        Return only the complete updated Python code.
        """

        evolved_code = self.llm.generate_domain_entity_response(prompt, self.entity_name)

        updated_attributes = current_schema.get("attributes", []) + new_attributes

        evolved_schema = {
            "entity": self.entity_name,
            "code": evolved_code,
            "attributes": updated_attributes,
            "context": current_schema.get("context", "academic"),
            "business_rules": self._get_business_rules(),
            "evolution_history": current_schema.get("evolution_history", []) + [evolution_request],
            "evolved_at": datetime.now().isoformat(),
        }

        self.current_schema = evolved_schema
        self.update_memory("current_schema", evolved_schema)

        return evolved_schema

    def _configure_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Configure BAE for different organizational contexts while preserving domain knowledge"""
        target_context = payload.get("target_context", "")
        modifications = payload.get("modifications", [])
        base_context = payload.get("base_context", "academic")

        # Preserve base domain knowledge
        base_knowledge = self.domain_knowledge.get(base_context, {})

        # Configure for new context
        configured_knowledge = {
            "entity": self.entity_name,
            "base_knowledge": base_knowledge,
            "context_modifications": modifications,
            "preserved_attributes": base_knowledge.get(
                "core_attributes", self._get_default_attributes()
            ),
            "context_specific_rules": self._generate_context_rules(target_context, modifications),
        }

        self.context_configurations[target_context] = configured_knowledge
        self.update_memory(f"context_config_{target_context}", configured_knowledge)

        return {
            "entity": self.entity_name,
            "configured_context": target_context,
            "base_context": base_context,
            "modifications": modifications,
            "reuse_percentage": self._calculate_reuse_percentage(base_knowledge, modifications),
        }

    def _coordinate_swea(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate SWEA agents while maintaining domain entity focus"""
        swea_tasks = payload.get("swea_tasks", [])
        domain_context = payload.get("domain_context", {})

        coordination_plan = []

        for task in swea_tasks:
            swea_task = {
                "entity": self.entity_name,
                "swea_agent": task.get("agent", ""),
                "task_type": task.get("task", ""),
                "domain_context": domain_context,
                "business_vocabulary": self._extract_business_vocabulary(),
                "semantic_requirements": {
                    "maintain_domain_coherence": True,
                    "preserve_business_rules": True,
                    "use_business_terminology": True,
                    "entity_focus": self.entity_name,
                },
            }
            coordination_plan.append(swea_task)

        self.update_memory("swea_coordination_plan", coordination_plan)
        return {"entity": self.entity_name, "coordination_plan": coordination_plan}

    def _validate_domain_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that generated artifacts maintain domain rules and semantic coherence"""
        artifact_code = payload.get("artifact_code", "")
        artifact_type = payload.get("artifact_type", "")

        prompt = f"""
        As the {self.entity_name} BAE (
            Business Autonomous Entity), validate this {artifact_type} artifact for domain rule compliance.

        VALIDATION CONTEXT:
        Entity Focus: {self.entity_name}
        Business Rules: {'; '.join(self._get_business_rules())}
        Expected Vocabulary: {', '.join(self._extract_business_vocabulary())}
        Domain Keywords: {', '.join(self.domain_keywords)}

        ARTIFACT TO VALIDATE:
        {artifact_code}

        VALIDATION CRITERIA:
        1. Semantic coherence with {self.entity_name} domain entity representation
        2. Business vocabulary preservation (uses {self.entity_name} terminology)
        3. Domain rule compliance specific to {self.entity_name} business logic
        4. Business logic consistency and data integrity
        5. Proper focus on {self.entity_name} entity operations and behaviors
        6. Code quality and maintainability for domain entity

        IMPORTANT: You must return a valid JSON object. Here's the exact format:

        {{
            "is_valid": true,
            "entity_focus_correct": true,
            "semantic_coherence_score": 90,
            "business_vocabulary_preserved": true,
            "domain_rules_followed": true,
            "issues": [],
            "recommendations": ["Maintain focus on {self.entity_name} domain representation"],
            "validation_summary": "Artifact maintains excellent domain coherence for {self.entity_name} entity"
        }}

        If there are issues, set the relevant boolean fields to false and include specific issues in the "issues" array.
        Always return valid JSON that can be parsed successfully. Do not include any text outside the JSON object.
        """

        validation_response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        cleaned_response = self._clean_json_response(validation_response)

        try:
            validation_result = json.loads(cleaned_response)

            # Ensure all required fields are present with defaults
            validation_result.setdefault("is_valid", True)
            validation_result.setdefault("entity_focus_correct", True)
            validation_result.setdefault("semantic_coherence_score", 85)
            validation_result.setdefault("business_vocabulary_preserved", True)
            validation_result.setdefault("domain_rules_followed", True)
            validation_result.setdefault("issues", [])
            validation_result.setdefault("recommendations", [])
            validation_result["entity"] = self.entity_name

            return validation_result
        except json.JSONDecodeError:
            # Return fallback validation result with all expected fields
            return {
                "entity": self.entity_name,
                "is_valid": True,
                "entity_focus_correct": True,
                "semantic_coherence_score": 85,
                "business_vocabulary_preserved": True,
                "domain_rules_followed": True,
                "issues": [],
                "recommendations": [],
                "error": "Failed to parse validation response",
                "raw_response": validation_response,
            }

    def _get_domain_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return comprehensive information about the domain entity"""
        return {
            "entity_name": self.entity_name,
            "domain": getattr(self, "domain", "N/A"),
            "domain_keywords": self.domain_keywords,
            "business_rules": self._get_business_rules(),
            "default_attributes": self._get_default_attributes(),
            "current_schema": self.current_schema,
            "domain_knowledge": self.domain_knowledge,
            "supported_tasks": list(self.handle(None, {}).get("supported_tasks", [])),
        }

    def _update_domain_knowledge(self, context: str, attributes: List[str]):
        """Update domain knowledge store with new schema"""
        if context not in self.domain_knowledge:
            self.domain_knowledge[context] = {}

        self.domain_knowledge[context].update(
            {
                "entity": self.entity_name,
                "core_attributes": attributes,
                "last_updated": datetime.now().isoformat(),
                "usage_count": self.domain_knowledge[context].get("usage_count", 0) + 1,
            }
        )

    def _generate_context_rules(self, context: str, modifications: List[str]) -> List[str]:
        """Generate context-specific business rules - can be overridden by concrete BAEs"""
        rules = []

        if context == "open_courses":
            rules.append(
                f"{self.entity_name} may have relaxed requirements for open course context"
            )
        elif context == "corporate_training":
            rules.append(f"{self.entity_name} must comply with corporate training standards")

        return rules

    def _extract_business_vocabulary(self) -> List[str]:
        """Extract business vocabulary terms that must be preserved"""
        vocabulary = [self.entity_name, "Entity", "Academic", "Learning"]
        vocabulary.extend(self.domain_keywords)

        # Add attribute-specific vocabulary
        schema = self.get_memory("current_schema")
        if schema:
            attributes = schema.get("attributes", [])
            for attr in attributes:
                if ":" in attr:
                    term = attr.split(":")[0].strip()
                    vocabulary.append(term.title())

        return list(set(vocabulary))

    def _calculate_reuse_percentage(
        self, base_knowledge: Dict[str, Any], modifications: List[str]
    ) -> float:
        """Calculate percentage of domain knowledge that can be reused"""
        if not base_knowledge:
            return 85.0  # Default high reuse for same entity

        base_attributes = base_knowledge.get("core_attributes", [])
        if not base_attributes:
            return 85.0

        # Enhanced calculation that considers multiple factors
        modification_count = len(modifications)
        base_count = len(base_attributes)

        if modification_count == 0:
            return 100.0

        # Factor 1: Attribute reuse (60% weight)
        attribute_reuse = (
            max(0, (base_count - modification_count) / base_count * 100) if base_count > 0 else 0
        )

        # Factor 2: Business rules reuse (25% weight) - assume high reuse for same entity
        business_rules_reuse = 90.0

        # Factor 3: Domain vocabulary reuse (15% weight) - assume high reuse for same entity
        vocabulary_reuse = 95.0

        # Weighted average
        total_reuse = attribute_reuse * 0.60 + business_rules_reuse * 0.25 + vocabulary_reuse * 0.15

        # Ensure minimum reuse percentage for same entity configurations
        total_reuse = max(total_reuse, 80.0)

        return round(total_reuse, 2)
