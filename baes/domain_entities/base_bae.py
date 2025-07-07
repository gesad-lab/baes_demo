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

    def _detect_relationship_request(self, request: str) -> Dict[str, Any]:
        """Detect if this is a relationship creation request using LLM instead of fixed patterns"""
        try:
            # Get current system state information for context
            existing_entities_info = self._get_existing_entities_context()
            current_entity_info = self._get_current_entity_context()
            context_info = self._build_context_information(existing_entities_info, current_entity_info)
            
            # Build LLM prompt for relationship detection
            prompt = f"""
            As a {self.entity_name} BAE (Business Autonomous Entity), analyze this request to determine if it's a relationship creation request:

            Request: "{request}"

            SYSTEM CONTEXT INFORMATION:
            {context_info}

            CRITICAL RELATIONSHIP DETECTION INSTRUCTIONS:
            1. Determine if this request is asking to CREATE A RELATIONSHIP between entities
            2. A relationship request typically involves connecting two or more entities
            3. Look for keywords like: "add X to Y", "connect", "link", "associate", "assign", "relate", "enroll", "register"
            4. Consider natural language variations and domain-specific terminology
            5. The PRIMARY entity is the one that will be MODIFIED to include a reference to the secondary entity
            6. The SECONDARY entity is the one being referenced (will create a foreign key to it)

            EXAMPLES OF RELATIONSHIP REQUESTS:
            - "add a course to the student entity" → relationship (student gets course_id)
            - "connect teacher with course" → relationship (course gets teacher_id)
            - "enroll student in course" → relationship (student gets course_id)
            - "assign teacher to course" → relationship (course gets teacher_id)
            - "link student to course" → relationship (student gets course_id)
            - "associate course with student" → relationship (student gets course_id)

            EXAMPLES OF NON-RELATIONSHIP REQUESTS:
            - "add student" → entity creation
            - "add email field to student" → entity evolution
            - "create course" → entity creation
            - "modify student name" → entity modification

            Return a JSON object with:

            {{
                "is_relationship": true/false,
                "target_entity": "entity that will be modified (gets foreign key)",
                "related_entity": "entity being referenced (foreign key points to this)",
                "relationship_type": "foreign_key|many_to_many|one_to_one",
                "description": "brief description of the relationship",
                "confidence": 0.0-1.0,
                "reasoning": "explanation of why this is/isn't a relationship request",
                "entities_mentioned": ["list of all entities mentioned in request"],
                "relationship_direction": "string"
            }}

            RELATIONSHIP DETECTION RULES:
            - If request mentions multiple entities AND uses relationship keywords → likely relationship
            - If request only mentions one entity OR uses creation/evolution keywords → likely not relationship
            - Consider domain context: academic terms like "enroll", "register", "assign" often indicate relationships
            - The entity being "added TO" another is usually the foreign key holder (primary entity)
            - If uncertain, set is_relationship to false and explain reasoning
            """

            # Use the new JSON enforcement functionality
            json_schema = {
                "is_relationship": True,
                "target_entity": "string",
                "related_entity": "string", 
                "relationship_type": "foreign_key|many_to_many|one_to_one",
                "description": "string",
                "confidence": 0.0,
                "reasoning": "string",
                "entities_mentioned": ["list of strings"],
                "relationship_direction": "string"
            }

            relationship_info = self.llm.generate_json_response(
                prompt=prompt,
                json_schema=json_schema
            )

            # Validate the response
            if relationship_info.get("is_relationship", False):
                # Ensure we have the required fields for a relationship
                if not relationship_info.get("target_entity") or not relationship_info.get("related_entity"):
                    logger.warning(f"🔗 {self.entity_name}BAE: LLM detected relationship but missing target/related entity")
                    relationship_info["is_relationship"] = False
                    relationship_info["reasoning"] = "Missing required relationship entities"
                    relationship_info["confidence"] = 0.0
                else:
                    logger.info(f"🔗 {self.entity_name}BAE: LLM detected relationship - {relationship_info['description']} (confidence: {relationship_info.get('confidence', 0.0)})")

            return relationship_info

        except Exception as e:
            logger.error(f"Error in LLM relationship detection: {str(e)}")
            return {
                "is_relationship": False,
                "target_entity": None,
                "related_entity": None,
                "relationship_type": None,
                "description": f"Error in relationship detection: {str(e)}",
                "confidence": 0.0,
                "reasoning": f"Exception occurred during LLM relationship detection: {str(e)}",
                "entities_mentioned": [],
                "relationship_direction": None,
                "error": True
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
        """Enhanced prompt with crystal-clear relationship detection rules for maximum accuracy."""
        
        # Get current system state information
        existing_entities_info = self._get_existing_entities_context()
        current_entity_info = self._get_current_entity_context()
        
        # Build enhanced context section for the prompt
        context_info = self._build_context_information(existing_entities_info, current_entity_info)
        
        return f"""
        As a {self.entity_name} BAE (Business Autonomous Entity), analyze this request in the context of '{context}':

        Request: "{request}"

        SYSTEM CONTEXT INFORMATION:
        {context_info}

        🔗 **RELATIONSHIP DETECTION RULES (HIGHEST PRIORITY - ANALYZE FIRST):**
        
        **RULE 1 - "ADD X TO Y ENTITY" PATTERN:**
        If request matches EXACTLY "add [ENTITY_A] to [ENTITY_B] entity":
        → This is ALWAYS a relationship request (100% certainty)
        → ENTITY_B (after "to") = target_entity (gets foreign key [ENTITY_A]_id)
        → ENTITY_A (before "to") = related_entity (referenced by foreign key)
        → Set: operation_type="relationship", is_relationship=true, confidence=1.0
        
        **RULE 2 - OTHER RELATIONSHIP PATTERNS:**
        If request matches any of these patterns:
        - "connect [ENTITY_A] with [ENTITY_B]"
        - "link [ENTITY_A] to [ENTITY_B]"  
        - "associate [ENTITY_A] with [ENTITY_B]"
        - "enroll [ENTITY_A] in [ENTITY_B]"
        - "assign [ENTITY_A] to [ENTITY_B]"
        - "relate [ENTITY_A] to [ENTITY_B]"
        - "register [ENTITY_A] for [ENTITY_B]"
        → This is ALWAYS a relationship request
        → Determine target_entity and related_entity based on context
        
        **RULE 3 - SINGLE ENTITY PATTERNS:**
        If request mentions only ONE entity:
        - "add [ENTITY]" → entity creation (operation_type="create")
        - "create [ENTITY]" → entity creation (operation_type="create")
        - "create [ENTITY] with [ATTRIBUTES]" → entity creation (operation_type="create")
        - "create [ENTITY] entity with [ATTRIBUTES]" → entity creation (operation_type="create")
        - "add [FIELD] to [ENTITY]" → entity evolution (operation_type="evolve")
        - "add [FIELD] to [ENTITY] entity" → entity evolution (operation_type="evolve")

        **CRITICAL EXAMPLES FOR REFERENCE:**
        🔗 RELATIONSHIP EXAMPLES (operation_type="relationship"):
        ✅ "add course to student entity" → relationship (student gets course_id foreign key)
        ✅ "add a course to the student entity" → relationship (student gets course_id foreign key)
        ✅ "connect teacher with course" → relationship (course gets teacher_id foreign key)
        ✅ "enroll student in course" → relationship (student gets course_id foreign key)
        
        🔄 EVOLUTION EXAMPLES (operation_type="evolve"):
        ✅ "add age to student entity" → evolution (add age field to student)
        ✅ "add email to student" → evolution (add email field to student)
        ✅ "add birth date to student entity" → evolution (add birth_date field to student)
        ✅ "add grade to student" → evolution (add grade field to student)
        
        🆕 CREATION EXAMPLES (operation_type="create"):
        ✅ "add student" → entity creation (create new student entity)
        ✅ "create student entity" → entity creation (create new student entity)
        ✅ "create a student entity with name and email" → entity creation (create student with name, email)
        ✅ "create student with name and email" → entity creation (create student with name, email)
        ✅ "add course" → entity creation (create new course entity)
        ✅ "create course entity with name" → entity creation (create course with name)

        **STEP-BY-STEP ANALYSIS FOR REQUEST: "{request}"**
        
        Step 1: Count entities mentioned in request = ?
        Step 2: Identify relationship keywords (to, with, in, for) = ?
        Step 3: Check if matches "add X to Y entity" pattern = ?
        Step 4: Apply decision matrix below
        
        **DECISION MATRIX (APPLY IN ORDER):**
        1. If request has 2+ entities AND relationship keywords → operation_type="relationship"
        2. If request has 1 entity AND field/attribute keywords → operation_type="evolve"
        3. If request has 1 entity AND creation keywords → operation_type="create"
        4. If unclear → operation_type="unknown" (but try to avoid this)
        
        **SPECIFIC PATTERN MATCHING:**
        • "add [field] to [entity]" → operation_type="evolve" (ALWAYS)
        • "add [field] to [entity] entity" → operation_type="evolve" (ALWAYS) 
        • "create [entity] with [attributes]" → operation_type="create" (ALWAYS)
        • "create a [entity] entity with [attributes]" → operation_type="create" (ALWAYS)
        
        **KEYWORDS TO RECOGNIZE:**
        • Relationship keywords: "to", "with", "in", "for", "connect", "link", "associate", "enroll", "assign"
        • Field/attribute keywords: "age", "email", "name", "birth_date", "grade", "phone", "address", "description"
        • Creation keywords: "add [entity]", "create [entity]", "make [entity]", "build [entity]"
        
        **ATTRIBUTE EXTRACTION RULES:**
        • For "create [entity] with [attributes]": Extract ONLY the attributes listed after "with"
        • For "add [field] to [entity]": Extract ONLY the field mentioned before "to"
        • Do NOT add default attributes like "course", "teacher", "student" unless explicitly requested
        • Do NOT assume relationships - only create what's explicitly asked for

        **RELATIONSHIP ENTITY ASSIGNMENT:**
        - For "add X to Y entity": Y=target_entity (gets X_id), X=related_entity
        - For "connect X with Y": contextually determine which gets foreign key
        - For "enroll X in Y": X=target_entity (gets Y_id), Y=related_entity

        **ENTITY EXISTENCE HANDLING:**
        1. If {self.entity_name} entity EXISTS and request adds to it → use operation_type="evolve" OR "relationship"
        2. If {self.entity_name} entity does NOT exist → use operation_type="create"
        3. For relationships, entities can be created if they don't exist

        **CONFIDENCE SCORING:**
        - 1.0: Perfect pattern match (e.g., "add course to student entity" or "add age to student entity")
        - 0.9: Clear keywords with good evidence (e.g., "add email to student")
        - 0.8: Good evidence for relationship/creation/evolution
        - 0.7: Some ambiguity but leaning toward interpretation
        - 0.6 or below: High ambiguity, may need user confirmation
        
        **CONFIDENCE GUIDELINES:**
        • Simple field additions should get 0.9+ confidence
        • Clear relationship patterns should get 1.0 confidence
        • Entity creation should get 0.8+ confidence

        Return a JSON object with:

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
            "reasoning": "Step-by-step explanation following the analysis above",
            "is_evolution": true/false,
            "evolution_type": "addition|removal|modification|complex",
            "entity_exists": true/false,
            "is_relationship": true/false,
            "target_entity": "entity that gets the foreign key - only for relationships",
            "related_entity": "entity referenced by foreign key - only for relationships", 
            "relationship_type": "foreign_key",
            "relationship_description": "brief description - only for relationships",
            "entities_mentioned": ["list of all entities mentioned in request"],
            "relationship_direction": "X_id added to Y - only for relationships"
        }}

        **MANDATORY REQUIREMENTS:**
        1. Follow the rules exactly in order
        2. Use the provided examples as reference
        3. AVOID returning "unknown" for basic cases - analyze the request carefully
        4. High confidence (0.8+) = clear interpretation
        5. Low confidence (0.6-) = potential user confirmation needed
        6. For "add [field] to [entity]" patterns, always use operation_type="evolve"
        7. For "add [entity1] to [entity2]" patterns, always use operation_type="relationship"
        8. CRITICAL: Only include attributes explicitly mentioned in the request - do NOT add extra fields
        9. For "create [entity] with [attributes]" patterns, ONLY use the specified attributes, no additional ones
        """

    def _interpret_business_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Unified business request interpretation using LLM for all request types including relationships"""
        try:
            request = payload.get("request", "")
            context = payload.get("context", "academic")

            # Use unified LLM interpretation for ALL requests including relationships
            prompt = self._build_unified_interpretation_prompt(request, context)
            
            # Enhanced JSON schema to include relationship detection
            json_schema = {
                "operation_type": "create|evolve|remove|modify|relationship",
                "entity": "string",
                "attributes": ["list of attribute objects"],
                "new_attributes": ["list of new attributes"],
                "removed_attributes": ["list of removed attributes"],
                "modified_attributes": ["list of modified attributes"],
                "business_vocabulary": ["list of business terms"],
                "requested_operations": ["list of operations"],
                "confidence": 0.0,
                "reasoning": "string",
                "is_evolution": True,
                "evolution_type": "addition|removal|modification|none",
                "entity_exists": True,
                # Relationship-specific fields
                "is_relationship": True,
                "target_entity": "string",
                "related_entity": "string",
                "relationship_type": "foreign_key|many_to_many|one_to_one",
                "relationship_description": "string",
                "entities_mentioned": ["list of strings"],
                "relationship_direction": "string"
            }

            interpretation = self.llm.generate_json_response(
                prompt=prompt,
                json_schema=json_schema
            )

            # Add detailed logging for debugging
            logger.info(f"🔍 {self.entity_name}BAE: LLM interpretation result:")
            logger.info(f"   Operation type: {interpretation.get('operation_type', 'unknown')}")
            logger.info(f"   Is relationship: {interpretation.get('is_relationship', False)}")
            logger.info(f"   Target entity: {interpretation.get('target_entity', 'None')}")
            logger.info(f"   Related entity: {interpretation.get('related_entity', 'None')}")
            logger.info(f"   Confidence: {interpretation.get('confidence', 0.0)}")
            logger.info(f"   Reasoning: {interpretation.get('reasoning', 'No reasoning provided')}")
            logger.info(f"   Entities mentioned: {interpretation.get('entities_mentioned', [])}")

            # Check if this is a relationship request
            if interpretation.get("is_relationship", False) and interpretation.get("operation_type") == "relationship":
                logger.info(
                    f"🔗 {self.entity_name}BAE: LLM detected relationship request - {interpretation.get('relationship_description', 'Unknown relationship')}"
                )
                
                # Validate relationship information
                target_entity = interpretation.get("target_entity")
                related_entity = interpretation.get("related_entity")
                
                if not target_entity or not related_entity:
                    logger.warning(f"🔗 {self.entity_name}BAE: LLM detected relationship but missing target/related entity")
                    logger.warning(f"   Target entity: {target_entity}")
                    logger.warning(f"   Related entity: {related_entity}")
                    # Continue with regular processing instead of failing
                else:
                    # Handle relationship request
                    return self._handle_relationship_request(request, context, interpretation)

            # Process regular (non-relationship) requests
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
            # Initial generation - use requested attributes or defaults
            raw_attributes = interpretation.get("attributes", [])
            
            # CRITICAL: If user specified attributes explicitly, use ONLY those
            # Don't add default attributes when user has been specific
            if raw_attributes:
                # User specified attributes - use only those
                extracted_attributes = self._normalize_attributes(raw_attributes)
                
                # Ensure 'id' attribute is always present and first, but don't add other defaults
                has_id = any(attr.get("name") == "id" for attr in extracted_attributes if isinstance(attr, dict))
                if not has_id:
                    id_attr = {"name": "id", "type": "int"}
                    extracted_attributes.insert(0, id_attr)
                    logger.info(f"🔧 {self.entity_name}BAE: Added mandatory 'id' attribute")
                
                logger.info(f"🎯 {self.entity_name}BAE: Using user-specified attributes: {[attr.get('name', str(attr)) for attr in extracted_attributes]}")
            else:
                # No attributes specified - use defaults
                raw_attributes = self._get_default_attributes()
                extracted_attributes = self._normalize_attributes(raw_attributes)
                
                # Ensure 'id' attribute for defaults too
                has_id = any(attr.get("name") == "id" for attr in extracted_attributes if isinstance(attr, dict))
                if not has_id:
                    id_attr = {"name": "id", "type": "int"}
                    extracted_attributes.insert(0, id_attr)
                
                logger.info(f"🎯 {self.entity_name}BAE: Using default attributes: {[attr.get('name', str(attr)) for attr in extracted_attributes]}")
            
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
        # CRITICAL: Create explicit constraint about using ONLY specified attributes
        attribute_constraint = {
            "use_only_specified_attributes": True,
            "do_not_add_default_attributes": True,
            "required_attributes": attributes,
            "attribute_count": len(attributes),
            "user_explicitly_specified": True,
            "strict_attribute_compliance": True
        }
        
        return [
            {
                "swea_agent": "TechLeadSWEA",
                "task_type": "coordinate_system_generation",
                "payload": {
                    "entity": self.entity_name,
                    "attributes": attributes,
                    "context": f"{operation_type} operation",
                    "is_evolution": is_evolution,
                    "attribute_constraints": attribute_constraint,
                    "business_requirements": {
                        "domain_focus": True,
                        "semantic_coherence": True,
                        "quality_gates": True,
                        "technical_governance": True,
                        "strict_attribute_compliance": True,
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
                    "attribute_constraints": attribute_constraint,
                    "use_only_specified_attributes": True,
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
                    "attribute_constraints": attribute_constraint,
                    "use_only_specified_attributes": True,
                    "do_not_add_extra_fields": True,
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
                    "attribute_constraints": attribute_constraint,
                    "use_only_specified_attributes": True,
                    "do_not_add_extra_fields": True,
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
                    "attribute_constraints": attribute_constraint,
                    "use_only_specified_attributes": True,
                    "do_not_add_extra_fields": True,
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
                    "attribute_constraints": attribute_constraint,
                    "strict_attribute_compliance": True,
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

        validation_result = self.llm.generate_json_response(
            prompt=prompt,
            system_prompt=f"""
            You are working with Business Autonomous Entities (BAEs) that represent domain entities
            as living, autonomous agents within the system.

            Current focus: {self.entity_name} entity in academic context

            Your responsibilities:
            1. Maintain semantic coherence between business vocabulary and technical implementation
            2. Preserve domain knowledge and business rules
            3. Ensure generated artifacts reflect business terminology
            4. Focus on domain entity representation, not software engineering roles
            5. Enable runtime evolution while preserving semantic consistency

            Always prioritize business domain understanding and vocabulary preservation.
            """,
            json_schema={
                "is_valid": True,
                "entity_focus_correct": True,
                "semantic_coherence_score": 90,
                "business_vocabulary_preserved": True,
                "domain_rules_followed": True,
                "issues": ["list of issues"],
                "recommendations": ["list of recommendations"],
                "validation_summary": "string"
            }
        )

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
        """Build comprehensive context information for accurate relationship detection."""
        context_lines = []
        
        # Current entity information with relationship details
        entity_name = self.entity_name.lower()
        if current_entity.get("exists", False):
            attributes = current_entity.get("attributes", [])
            if attributes:
                attr_list = []
                foreign_keys = []
                regular_attributes = []
                
                for attr in attributes:
                    if isinstance(attr, dict):
                        attr_name = attr.get('name', 'unknown')
                        attr_type = attr.get('type', 'str')
                        attr_display = f"{attr_name}:{attr_type}"
                        
                        if attr.get('is_foreign_key'):
                            related_entity = attr.get('related_entity', 'unknown')
                            foreign_keys.append(f"{attr_name} → {related_entity}")
                            attr_display += f" (FK→{related_entity})"
                        else:
                            regular_attributes.append(attr_display)
                        
                        attr_list.append(attr_display)
                    elif isinstance(attr, str):
                        attr_list.append(attr)
                        regular_attributes.append(attr)
                    else:
                        attr_list.append(str(attr))
                        regular_attributes.append(str(attr))
                
                context_lines.append(f"🎯 CURRENT ENTITY STATUS:")
                context_lines.append(f"   Entity '{self.entity_name}' EXISTS with {len(attributes)} attributes")
                context_lines.append(f"   📊 Attributes: {', '.join(attr_list)}")
                
                if foreign_keys:
                    context_lines.append(f"   🔗 Current relationships: {', '.join(foreign_keys)}")
                
                context_lines.append(f"   📍 Source: {current_entity.get('source', 'unknown')}")
                context_lines.append(f"   ⚠️  Any evolution must PRESERVE these existing attributes!")
            else:
                context_lines.append(f"🎯 CURRENT ENTITY STATUS:")
                context_lines.append(f"   Entity '{self.entity_name}' EXISTS but has no recorded attributes")
                context_lines.append(f"   Source: {current_entity.get('source', 'unknown')}")
        else:
            context_lines.append(f"🎯 CURRENT ENTITY STATUS:")
            context_lines.append(f"   Entity '{self.entity_name}' does NOT exist in the system")
            context_lines.append(f"   This is likely a CREATE operation for a new entity")
        
        # Other existing entities with relationship potential
        if existing_entities:
            other_entities = {k: v for k, v in existing_entities.items() if k != entity_name}
            if other_entities:
                context_lines.append(f"\n📋 AVAILABLE ENTITIES FOR RELATIONSHIPS:")
                
                relationship_ready_entities = []
                for ent_name, ent_info in other_entities.items():
                    if ent_info.get("exists", False):
                        attrs = ent_info.get("attributes", [])
                        relationship_ready_entities.append(ent_name.capitalize())
                        
                        if attrs:
                            attr_summary = []
                            fk_summary = []
                            for attr in attrs[:3]:  # Show first 3 attributes
                                if isinstance(attr, dict):
                                    attr_name = attr.get('name', 'unknown')
                                    if attr.get('is_foreign_key'):
                                        related = attr.get('related_entity', 'unknown')
                                        fk_summary.append(f"{attr_name}→{related}")
                                    else:
                                        attr_summary.append(attr_name)
                                elif isinstance(attr, str):
                                    attr_summary.append(attr.split(':')[0] if ':' in attr else attr)
                                else:
                                    attr_summary.append(str(attr))
                            
                            attr_text = ', '.join(attr_summary)
                            if len(attrs) > 3:
                                attr_text += f" (+{len(attrs)-3} more)"
                            
                            display_text = f"{attr_text}"
                            if fk_summary:
                                display_text += f" | Relationships: {', '.join(fk_summary)}"
                            
                            context_lines.append(f"   ✅ {ent_name.capitalize()}: {display_text}")
                        else:
                            context_lines.append(f"   ✅ {ent_name.capitalize()}: (ready for relationships)")
                
                # Show possible relationship combinations
                if len(relationship_ready_entities) >= 1:
                    context_lines.append(f"\n🔗 POTENTIAL RELATIONSHIPS:")
                    for entity in relationship_ready_entities:
                        if entity.lower() != self.entity_name.lower():
                            context_lines.append(f"   💡 {self.entity_name} ↔ {entity} (add {entity.lower()}_id to {self.entity_name})")
                            context_lines.append(f"   💡 {entity} ↔ {self.entity_name} (add {self.entity_name.lower()}_id to {entity})")
                            
        else:
            context_lines.append(f"\n📋 AVAILABLE ENTITIES FOR RELATIONSHIPS: None")
            context_lines.append(f"   ⚠️  No other entities exist yet - relationships require multiple entities")
        
        # Relationship detection guidance
        context_lines.append(f"\n� RELATIONSHIP DETECTION GUIDANCE:")
        context_lines.append(f"   🎯 'add [ENTITY_A] to [ENTITY_B] entity' = RELATIONSHIP (ENTITY_B gets ENTITY_A_id)")
        context_lines.append(f"   🎯 'connect/link/associate [A] with [B]' = RELATIONSHIP")
        context_lines.append(f"   🎯 'enroll [A] in [B]' = RELATIONSHIP (A gets B_id)")
        context_lines.append(f"   ❌ 'add [ENTITY]' = ENTITY CREATION (single entity)")
        context_lines.append(f"   ❌ 'add [FIELD] to [ENTITY]' = ENTITY EVOLUTION (field addition)")
        
        # Academic domain patterns
        context_lines.append(f"\n📚 ACADEMIC DOMAIN PATTERNS:")
        context_lines.append(f"   🎓 Student-Course: student gets course_id (enrollment)")
        context_lines.append(f"   👨‍🏫 Teacher-Course: course gets teacher_id (assignment)")
        context_lines.append(f"   📖 Student-Teacher: student gets teacher_id (mentoring)")
        
        return '\n'.join(context_lines)
