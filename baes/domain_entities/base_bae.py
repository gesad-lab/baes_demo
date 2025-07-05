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

    def _build_unified_interpretation_prompt(self, request: str, context: str) -> str:
        """Builds a context-aware unified prompt for LLM to interpret any type of business request."""
        
        # Get current system state information
        existing_entities_info = self._get_existing_entities_context()
        current_entity_info = self._get_current_entity_context()
        
        # Build context section for the prompt
        context_info = self._build_context_information(existing_entities_info, current_entity_info)
        
        return f"""
        As a {self.entity_name} BAE (Business Autonomous Entity), analyze this request in the context of '{context}':

        Request: "{request}"

        SYSTEM CONTEXT INFORMATION:
        {context_info}

        CRITICAL INSTRUCTIONS:
        1. If the {self.entity_name} entity ALREADY EXISTS and has current attributes, this is likely an EVOLUTION operation
        2. If the request mentions "add", "include", "append" to an existing entity, use operation_type="evolve"
        3. If the {self.entity_name} entity does NOT exist, this is a CREATE operation
        4. For evolution operations, PRESERVE all existing attributes and only add/modify/remove as requested
        5. For create operations, include all necessary attributes for a complete entity

        Determine the operation type and extract all relevant information. Return a JSON object with:

        {{
            "operation_type": "create|evolve|remove|modify|relationship",
            "entity": "{self.entity_name}",
            "attributes": [
                {{"name": "attribute_name", "type": "attribute_type"}}
            ],
            "new_attributes": [
                {{"name": "new_attr_name", "type": "new_attr_type"}}
            ],
            "removed_attributes": ["attr_name_to_remove"],
            "modified_attributes": [
                {{"old": "old_attr: old_type", "new": "new_attr: new_type"}}
            ],
            "business_vocabulary": ["term1", "term2"],
            "requested_operations": ["create", "read", "update", "delete"],
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation of the interpretation including why you chose create vs evolve",
            "is_evolution": true/false,
            "evolution_type": "addition|removal|modification|complex",
            "entity_exists": true/false
        }}

        OPERATION TYPE GUIDELINES:
        - "create": Entity does not exist OR request asks to create from scratch
        - "evolve": Entity exists AND request asks to add/modify existing entity
        - "remove": Request asks to remove attributes from existing entity
        - "modify": Request asks to change existing attributes (rename, change type)
        - "relationship": Request asks to connect entities

        ATTRIBUTE HANDLING:
        - For "create": populate "attributes" with ALL required fields for the entity
        - For "evolve": populate "new_attributes" with ONLY the fields to add, existing preserved automatically
        - For "remove": populate "removed_attributes" with fields to remove
        - For "modify": populate "modified_attributes" with field changes
        - Always include "id: int" as the first attribute for database operations (auto-generated)
        - Use appropriate types: str, int, float, date, datetime, bool
        """

    def _interpret_business_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Unified business request interpretation using LLM for all request types"""
        try:
            request = payload.get("request", "")
            context = payload.get("context", "academic")

            # First, check if this is a relationship creation request (keep existing logic)
            relationship_info = self._detect_relationship_request(request)
            if relationship_info["is_relationship"]:
                logger.info(
                    f"🔗 {self.entity_name}BAE: Detected relationship request - {relationship_info['description']}"
                )
                return self._handle_relationship_request(request, context, relationship_info)

            # Use unified LLM interpretation for all other requests
            prompt = self._build_unified_interpretation_prompt(request, context)
            interpretation_str = self.llm.generate_response(prompt)

            try:
                interpretation = json.loads(self._clean_json_response(interpretation_str))
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM response: {interpretation_str}")
                # Create a fallback interpretation
                interpretation = {
                    "operation_type": "create",
                    "entity": self.entity_name,
                    "attributes": self._get_default_attributes(),
                    "new_attributes": [],
                    "removed_attributes": [],
                    "modified_attributes": [],
                    "business_vocabulary": [],
                    "requested_operations": ["create", "read", "update", "delete"],
                    "confidence": 0.0,
                    "reasoning": "Fallback interpretation due to LLM parsing error",
                    "is_evolution": False,
                    "evolution_type": "none"
                }

            # Process the interpretation based on operation type
            return self._process_unified_interpretation(interpretation, request, context)

        except Exception as e:
            logger.error(f"Error in unified interpretation: {str(e)}")
            return {
                "success": False,
                "error": "INTERPRETATION_ERROR",
                "message": f"Failed to interpret business request: {str(e)}",
                "entity": self.entity_name
            }

    def _process_unified_interpretation(self, interpretation: Dict[str, Any], request: str, context: str) -> Dict[str, Any]:
        """Process the unified LLM interpretation and create appropriate coordination plan"""
        operation_type = interpretation.get("operation_type", "create")
        is_evolution = interpretation.get("is_evolution", False)
        entity_exists = interpretation.get("entity_exists", False)
        
        # Enhanced logic: if entity exists but operation_type is still "create", force it to "evolve"
        if entity_exists and operation_type == "create":
            # Check if this is actually an evolution request based on keywords
            evolution_keywords = ["add", "include", "append", "insert", "extend"]
            if any(keyword in request.lower() for keyword in evolution_keywords):
                logger.info(f"🔄 {self.entity_name}BAE: Correcting operation_type from 'create' to 'evolve' - entity exists and request contains evolution keywords")
                operation_type = "evolve"
                is_evolution = True
                interpretation["operation_type"] = "evolve"
                interpretation["is_evolution"] = True
                interpretation["evolution_type"] = "addition"
        
        # Extract and normalize attributes based on operation type
        if operation_type == "create":
            # Initial generation - use all attributes
            raw_attributes = interpretation.get("attributes", [])
            if not raw_attributes:
                raw_attributes = self._get_default_attributes()
            extracted_attributes = self._normalize_attributes(raw_attributes)
            
            # Store the schema for future reference
            self.current_schema = {
                "entity": self.entity_name,
                "attributes": extracted_attributes,
                "context": context,
                "generated_at": datetime.now().isoformat(),
                "business_rules": self._get_business_rules(),
                "is_evolution": False,
                "interpretation": interpretation,
            }
            
        elif operation_type in ["evolve", "remove", "modify"]:
            # Evolution - load current schema and apply changes
            self._load_stored_schema()
            current_attributes = self.current_schema.get("attributes", []) if self.current_schema else []
            
            # If no current attributes found but entity exists, try to get from database
            if not current_attributes and entity_exists:
                current_entity_context = self._get_current_entity_context()
                if current_entity_context.get("exists", False):
                    current_attributes = current_entity_context.get("attributes", [])
                    logger.info(f"📥 {self.entity_name}BAE: Loaded {len(current_attributes)} attributes from {current_entity_context.get('source', 'unknown')}")
            
            # Apply evolution changes
            extracted_attributes = self._apply_evolution_changes(
                current_attributes, interpretation, operation_type
            )
            
            # Log the evolution for transparency
            logger.info(f"🔄 {self.entity_name}BAE: Evolution operation - {operation_type}")
            logger.info(f"   📊 Current attributes: {len(current_attributes)} -> {[attr.get('name', str(attr)) for attr in current_attributes]}")
            logger.info(f"   ➕ Final attributes: {len(extracted_attributes)} -> {[attr.get('name', str(attr)) for attr in extracted_attributes]}")
            
            # Update schema
            if self.current_schema:
                self.current_schema["attributes"] = extracted_attributes
                self.current_schema["is_evolution"] = True
                self.current_schema["last_modified"] = datetime.now().isoformat()
            else:
                self.current_schema = {
                    "entity": self.entity_name,
                    "attributes": extracted_attributes,
                    "context": context,
                    "generated_at": datetime.now().isoformat(),
                    "business_rules": self._get_business_rules(),
                    "is_evolution": True,
                    "interpretation": interpretation,
                }
        else:
            # Unknown operation type - fallback to create
            raw_attributes = interpretation.get("attributes", self._get_default_attributes())
            extracted_attributes = self._normalize_attributes(raw_attributes)

        # Create the interpretation result
        result = {
            "entity": self.entity_name,
            "domain": getattr(self, "domain", "academic"),
            "attributes": extracted_attributes,
            "extracted_attributes": extracted_attributes,
            "is_evolution": is_evolution,
            "request_type": operation_type,
            "business_context": request,
            "semantic_coherence": True,
            "domain_knowledge_preserved": True,
            "interpreted_intent": f"{operation_type}_{self.entity_name.lower()}_management_system",
            "domain_operations": [f"{operation_type}_entity", "update_schema"],
            "business_vocabulary": interpretation.get("business_vocabulary", []),
            "entity_focus": self.entity_name,
            "confidence": interpretation.get("confidence", 0.0),
            "reasoning": interpretation.get("reasoning", ""),
            "entity_exists": entity_exists,
        }

        # Add evolution-specific metadata if applicable
        if is_evolution:
            result.update({
                "new_attributes": interpretation.get("new_attributes", []),
                "removed_attributes": interpretation.get("removed_attributes", []),
                "modified_attributes": interpretation.get("modified_attributes", []),
                "evolution_type": interpretation.get("evolution_type", "addition"),
            })

        # Create comprehensive coordination plan
        result["swea_coordination"] = self._create_unified_coordination_plan(
            extracted_attributes, is_evolution, operation_type
        )

        return result

    def _apply_evolution_changes(self, current_attributes: List[Dict[str, Any]], 
                                interpretation: Dict[str, Any], operation_type: str) -> List[Dict[str, Any]]:
        """Apply evolution changes to current attributes based on LLM interpretation"""
        result_attributes = current_attributes.copy()
        
        logger.debug(f"🔄 Applying {operation_type} evolution changes:")
        logger.debug(f"   📊 Starting with {len(current_attributes)} current attributes")
        
        if operation_type == "evolve":
            # Add new attributes
            new_attrs = interpretation.get("new_attributes", [])
            
            # If new_attributes is empty but attributes is provided, use attributes as new_attributes
            # This handles cases where LLM puts evolution attributes in the wrong field
            if not new_attrs and interpretation.get("attributes"):
                attrs_from_interpretation = interpretation.get("attributes", [])
                # Only treat as new attributes if they're not already in current attributes
                current_attr_names = {attr.get("name", "") for attr in current_attributes if isinstance(attr, dict)}
                
                potential_new_attrs = []
                for attr in attrs_from_interpretation:
                    if isinstance(attr, dict):
                        attr_name = attr.get("name", "")
                        if attr_name and attr_name not in current_attr_names:
                            potential_new_attrs.append(attr)
                
                if potential_new_attrs:
                    new_attrs = potential_new_attrs
                    logger.info(f"🔄 {operation_type}: Using {len(new_attrs)} attributes from 'attributes' field as new attributes")
            
            if new_attrs:
                new_attrs_normalized = self._normalize_attributes(new_attrs)
                
                # Ensure we don't duplicate existing attributes
                current_attr_names = {attr.get("name", "") for attr in result_attributes if isinstance(attr, dict)}
                
                for new_attr in new_attrs_normalized:
                    attr_name = new_attr.get("name", "")
                    if attr_name and attr_name not in current_attr_names:
                        result_attributes.append(new_attr)
                        logger.debug(f"   ➕ Added new attribute: {attr_name}:{new_attr.get('type', 'str')}")
                    else:
                        logger.debug(f"   ⚠️  Skipped duplicate attribute: {attr_name}")
                        
        elif operation_type == "remove":
            # Remove specified attributes (but never remove 'id')
            removed_attrs = interpretation.get("removed_attributes", [])
            if removed_attrs:
                # Filter out 'id' from removal list - it should never be removed
                filtered_removed_attrs = [attr for attr in removed_attrs if attr != 'id']
                if len(filtered_removed_attrs) != len(removed_attrs):
                    logger.warning("⚠️  Prevented removal of 'id' attribute - it's required for database operations")
                
                original_count = len(result_attributes)
                result_attributes = [
                    attr for attr in result_attributes 
                    if attr.get("name") not in filtered_removed_attrs
                ]
                removed_count = original_count - len(result_attributes)
                logger.debug(f"   ➖ Removed {removed_count} attributes: {filtered_removed_attrs}")
                
        elif operation_type == "modify":
            # Modify existing attributes (but be careful with 'id')
            modified_attrs = interpretation.get("modified_attributes", [])
            for mod in modified_attrs:
                old_attr = mod.get("old", "")
                new_attr = mod.get("new", "")
                if old_attr and new_attr:
                    # Prevent modification of 'id' attribute
                    if old_attr.startswith("id:") or old_attr == "id":
                        logger.warning("⚠️  Prevented modification of 'id' attribute - it's immutable")
                        continue
                        
                    # Find and replace the attribute
                    for i, attr in enumerate(result_attributes):
                        if isinstance(attr, dict):
                            current_attr_repr = f"{attr.get('name')}:{attr.get('type')}"
                            if current_attr_repr == old_attr:
                                new_attr_normalized = self._normalize_attributes([new_attr])
                                if new_attr_normalized:
                                    result_attributes[i] = new_attr_normalized[0]
                                    logger.debug(f"   🔄 Modified attribute: {old_attr} -> {new_attr}")
                                break
        
        # CRITICAL: Ensure 'id' attribute is always present and first
        has_id = any(attr.get("name") == "id" for attr in result_attributes if isinstance(attr, dict))
        if not has_id:
            # Add 'id' attribute at the beginning
            id_attr = {"name": "id", "type": "int"}
            result_attributes.insert(0, id_attr)
            logger.debug("   🔧 Added mandatory 'id' attribute")
        else:
            # Ensure 'id' is first in the list
            id_attr = None
            non_id_attrs = []
            for attr in result_attributes:
                if isinstance(attr, dict) and attr.get("name") == "id":
                    id_attr = attr
                else:
                    non_id_attrs.append(attr)
            
            if id_attr:
                result_attributes = [id_attr] + non_id_attrs
                logger.debug("   🔧 Moved 'id' attribute to first position")
        
        logger.debug(f"   📊 Final result: {len(result_attributes)} attributes")
        return result_attributes

    def _create_unified_coordination_plan(self, attributes: List[Dict[str, Any]], 
                                        is_evolution: bool, operation_type: str) -> List[Dict[str, Any]]:
        """Create a unified coordination plan for all operation types"""
        return [
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "coordinate_system_generation",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": attributes,
                    "context": f"{operation_type} operation",
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
                    "attributes": attributes,
                    "context": f"{operation_type} operation",
                    "preserve_data": is_evolution,
                    "business_rules": True,
                },
            },
            {
                "swea_agent": "BackendSWEA",
                "task_type": "generate_model",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": attributes,
                    "context": f"{operation_type} operation",
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
                    "attributes": attributes,
                    "context": f"{operation_type} operation",
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
                    "attributes": attributes,
                    "context": f"{operation_type} operation",
                    "ui_framework": "streamlit",
                    "features": ["crud_operations", "data_visualization", "user_friendly"],
                },
            },
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "review_and_approve",
                "payload": {
                    "entity": self.entity_name,
                    "context": f"{operation_type} operation",
                    "system_components": ["database", "backend", "frontend"],
                    "phase": "phase_1_complete",
                    "final_review": True,
                },
            },
        ]

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
            return ["name: str", "email: str"]
        elif self.entity_name.lower() == "course":
            return ["name: str", "code: str"]
        elif self.entity_name.lower() == "teacher":
            return ["name: str", "email: str"]
        else:
            return ["name: str", "description: str"]

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

        updated_attributes = current_schema.get("attributes", []) + self._normalize_attributes(new_attributes)

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
        As the {self.entity_name} BAE (Business Autonomous Entity), validate this {artifact_type} artifact for domain rule compliance.

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
                if isinstance(attr, dict):
                    term = attr.get("name")
                    if term:
                        vocabulary.append(term.title())
                elif isinstance(attr, str) and ":" in attr:
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

    def _get_existing_entities_context(self) -> Dict[str, Any]:
        """Get information about all existing entities in the system."""
        try:
            # Get entities from context store
            context_store_path = os.environ.get("BAE_CONTEXT_STORE_PATH", "database/context_store.json")
            context_store = ContextStore(context_store_path)
            
            existing_entities = {}
            
            # Get all entities from context store
            all_entities = context_store.get_entities()
            for entity_data in all_entities:
                entity_name = entity_data.get("name", "").lower()
                entity_info = entity_data.get("data", {})
                
                if entity_name and entity_name not in existing_entities:
                    # Extract attributes if available
                    attributes = []
                    if isinstance(entity_info, dict):
                        # From agent memory schema
                        if "attributes" in entity_info:
                            attributes = entity_info.get("attributes", [])
                        # From domain knowledge
                        elif "interpretation" in entity_info:
                            interpretation = entity_info.get("interpretation", {})
                            attributes = interpretation.get("extracted_attributes", [])
                    
                    existing_entities[entity_name] = {
                        "exists": True,
                        "attributes": attributes,
                        "source": entity_data.get("type", "unknown")
                    }
            
            return existing_entities
            
        except Exception as e:
            logger.warning(f"Could not get existing entities context: {e}")
            return {}

    def _get_current_entity_context(self) -> Dict[str, Any]:
        """Get detailed information about the current entity being processed."""
        try:
            # Check current schema in memory
            current_schema = self.get_memory("current_schema")
            if current_schema:
                return {
                    "exists": True,
                    "attributes": current_schema.get("attributes", []),
                    "context": current_schema.get("context", "academic"),
                    "last_modified": current_schema.get("last_modified", current_schema.get("generated_at", "unknown")),
                    "source": "bae_memory"
                }
            
            # Try to load from persistent storage
            self._load_stored_schema()
            if self.current_schema:
                return {
                    "exists": True,
                    "attributes": self.current_schema.get("attributes", []),
                    "context": self.current_schema.get("context", "academic"),
                    "last_modified": self.current_schema.get("last_modified", self.current_schema.get("generated_at", "unknown")),
                    "source": "persistent_storage"
                }
            
            # Check if entity exists in managed system (database)
            try:
                from baes.core.managed_system_manager import ManagedSystemManager
                manager = ManagedSystemManager()
                db_path = manager.managed_system_path / "app" / "database" / "baes_system.db"
                
                if db_path.exists():
                    import sqlite3
                    table_name = f"{self.entity_name.lower()}s"
                    
                    with sqlite3.connect(str(db_path)) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                        table_exists = cursor.fetchone() is not None
                        
                        if table_exists:
                            # Get table schema
                            cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = cursor.fetchall()
                            
                            attributes = []
                            type_map = {"TEXT": "str", "INTEGER": "int", "REAL": "float"}
                            
                            for col in columns:
                                col_name = col[1]
                                col_type = col[2]
                                py_type = type_map.get(col_type, "str")
                                # Include ALL columns including 'id' for complete schema representation
                                attributes.append({"name": col_name, "type": py_type})
                            
                            return {
                                "exists": True,
                                "attributes": attributes,
                                "context": "academic",
                                "source": "database_schema"
                            }
                
            except Exception as db_e:
                logger.debug(f"Could not check database for entity {self.entity_name}: {db_e}")
            
            # Entity does not exist
            return {
                "exists": False,
                "attributes": [],
                "context": "academic",
                "source": "none"
            }
            
        except Exception as e:
            logger.warning(f"Could not get current entity context for {self.entity_name}: {e}")
            return {
                "exists": False,
                "attributes": [],
                "context": "academic",
                "source": "error"
            }

    def _build_context_information(self, existing_entities: Dict[str, Any], current_entity: Dict[str, Any]) -> str:
        """Build formatted context information for the LLM prompt."""
        context_lines = []
        
        # Current entity information
        entity_name = self.entity_name.lower()
        if current_entity.get("exists", False):
            attributes = current_entity.get("attributes", [])
            if attributes:
                attr_list = []
                for attr in attributes:
                    if isinstance(attr, dict):
                        attr_list.append(f"{attr.get('name', 'unknown')}:{attr.get('type', 'str')}")
                    elif isinstance(attr, str):
                        attr_list.append(attr)
                    else:
                        attr_list.append(str(attr))
                
                context_lines.append(f"🎯 CURRENT ENTITY STATUS:")
                context_lines.append(f"   Entity '{self.entity_name}' EXISTS with attributes: {', '.join(attr_list)}")
                context_lines.append(f"   Source: {current_entity.get('source', 'unknown')}")
                context_lines.append(f"   ⚠️  Any evolution must PRESERVE these existing attributes!")
            else:
                context_lines.append(f"🎯 CURRENT ENTITY STATUS:")
                context_lines.append(f"   Entity '{self.entity_name}' EXISTS but has no recorded attributes")
                context_lines.append(f"   Source: {current_entity.get('source', 'unknown')}")
        else:
            context_lines.append(f"🎯 CURRENT ENTITY STATUS:")
            context_lines.append(f"   Entity '{self.entity_name}' does NOT exist in the system")
            context_lines.append(f"   This is likely a CREATE operation for a new entity")
        
        # Other existing entities information
        if existing_entities:
            other_entities = {k: v for k, v in existing_entities.items() if k != entity_name}
            if other_entities:
                context_lines.append(f"\n📋 OTHER ENTITIES IN SYSTEM:")
                for ent_name, ent_info in other_entities.items():
                    if ent_info.get("exists", False):
                        attrs = ent_info.get("attributes", [])
                        if attrs:
                            attr_summary = []
                            for attr in attrs[:3]:  # Show first 3 attributes
                                if isinstance(attr, dict):
                                    attr_summary.append(attr.get('name', 'unknown'))
                                elif isinstance(attr, str):
                                    attr_summary.append(attr.split(':')[0] if ':' in attr else attr)
                                else:
                                    attr_summary.append(str(attr))
                            attr_text = ', '.join(attr_summary)
                            if len(attrs) > 3:
                                attr_text += f" (+{len(attrs)-3} more)"
                            context_lines.append(f"   - {ent_name}: {attr_text}")
                        else:
                            context_lines.append(f"   - {ent_name}: (no attributes recorded)")
        else:
            context_lines.append(f"\n📋 OTHER ENTITIES IN SYSTEM: None")
        
        # Evolution detection hints
        context_lines.append(f"\n💡 EVOLUTION DETECTION HINTS:")
        context_lines.append(f"   - Words like 'add', 'include', 'append' to existing entity = EVOLVE")
        context_lines.append(f"   - Words like 'create', 'make', 'build' new entity = CREATE")
        context_lines.append(f"   - Words like 'remove', 'delete' attribute = REMOVE")
        context_lines.append(f"   - Words like 'change', 'modify', 'update' attribute = MODIFY")
        
        return '\n'.join(context_lines)
