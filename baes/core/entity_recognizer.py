import json
from typing import Dict, List, Optional

from baes.core.recognition_cache import RecognitionCache
from baes.llm.openai_client import OpenAIClient
from config import Config


class EntityRecognizer:
    """Uses OpenAI to recognize and classify entities from natural language requests"""

    def __init__(self, context_store=None):
        self.llm = OpenAIClient()
        # Only registered BAE entities - everything else uses GenericBAE fallback
        self.supported_entities = ["student", "course", "teacher"]
        self.context_store = context_store
        
        # Initialize recognition cache (US3: Entity Recognition Caching)
        if Config.ENABLE_RECOGNITION_CACHE:
            self.cache = RecognitionCache()
        else:
            self.cache = None

    def recognize_entity(self, user_input: str) -> Dict[str, any]:
        """
        Classify user input to determine which BAE entity they're referring to.
        For relationship creation requests, correctly identifies the primary entity 
        (the one being modified) rather than the secondary entity being added.
        
        US3: Checks cache before calling OpenAI (10-15% token savings)
        """
        
        # US3: Try cache first if enabled
        if self.cache:
            cached_result = self.cache.cache_read(user_input)
            if cached_result:
                # Cache hit - return cached recognition result
                return {
                    "detected_entity": cached_result.entity_name,
                    "confidence": 0.95,  # High confidence for cached results
                    "reasoning": f"Retrieved from cache (cached at {cached_result.cached_at})",
                    "language_detected": "en",  # Cached results don't preserve language
                    "action_intent": "create",  # Assume create for cached
                    "relationship_analysis": {
                        "is_relationship_request": cached_result.requires_custom_logic,
                        "entities_mentioned": [cached_result.entity_name],
                        "primary_entity": cached_result.entity_name,
                        "secondary_entity": None,
                        "relationship_direction": None
                    },
                    "cached": True,
                    "cache_tier": "memory" if cached_result.cached_at else "persistent"
                }
        
        # Gather context about existing entities and relationships
        context_info = self._gather_context_info()
        
        prompt = f"""
        You are an Entity Recognition specialist for a BAE (Business Autonomous Entity) System. Your task is to analyze user requests and identify the PRIMARY ENTITY or CONCEPT that the user wants to work with.

        User Request: "{user_input}"

        ## Current System Context:
        {context_info}

        ## Analysis Instructions:

        ### Step 1: Identify what the user wants to create/manage
        - What is the PRIMARY subject of this request?
        - Extract the main entity/concept (e.g., "student", "book", "api", "product", "vehicle")
        - Use a SINGLE, SIMPLE NOUN to describe it (lowercase, singular form)

        ### Step 2: Determine request type
        - Is this a RELATIONSHIP request (e.g., "add X to Y", "connect X with Y")?
        - Is this a CREATION request (e.g., "create X", "build X", "develop X")?
        - Is this an UPDATE request (e.g., "modify X", "change X")?
        - Is this a DELETION request (e.g., "remove X", "delete X")?

        ### Step 3: For RELATIONSHIP requests - Apply the Primary Entity Rule
        **CRITICAL RULE**: The PRIMARY entity is the one that will be MODIFIED to include a reference to the secondary entity.
        
        Examples:
        - "add course to student" → PRIMARY: student (student schema gets modified)
        - "add student to course" → PRIMARY: course (course schema gets modified)
        - "create API for products" → PRIMARY: api (the thing being created)
        - "build database for users" → PRIMARY: database (the thing being built)

        ### Step 4: Entity Extraction Guidelines
        - For "REST API", "web service", "backend API" → use "api"
        - For "user interface", "web UI", "frontend" → use "ui"
        - For "database", "data model", "schema" → use "database"
        - For "test suite", "tests" → use "test"
        - For business entities like "book", "product", "employee" → use the noun directly
        - For academic entities like "student", "course", "teacher" → use the exact term

        ### Step 5: Confidence Assessment
        - High confidence (>0.8): Clear, unambiguous entity mentioned
        - Medium confidence (0.5-0.8): Entity can be inferred with reasonable certainty
        - Low confidence (<0.5): Request is vague, ambiguous, or unintelligible → use "unknown"

        ## Response Format:
        Return a JSON response with:
        {{
            "detected_entity": "string (single noun, lowercase, singular)",
            "confidence": 0.0-1.0,
            "reasoning": "Step-by-step explanation of your analysis",
            "language_detected": "detected language",
            "action_intent": "create|update|delete|list|relationship|unknown",
            "relationship_analysis": {{
                "is_relationship_request": true/false,
                "entities_mentioned": ["entity1", "entity2"],
                "primary_entity": "entity that will be modified",
                "secondary_entity": "entity being referenced",
                "relationship_direction": "from secondary to primary"
            }}
        }}

        ## Registered BAE Entities (have specialized handlers):
        - **student** (aluno, estudante, discente): students/learners
        - **course** (curso, disciplina, matéria): courses/subjects  
        - **teacher** (professor, docente, instrutor): teachers/instructors

        ## Dynamic Entity Handling:
        - Any OTHER entity will be handled by GenericBAE fallback
        - Examples: "book", "product", "api", "vehicle", "employee", "inventory", etc.
        - Just extract the entity name - the system will handle it dynamically!

        **Important**: 
        - Extract the entity name even if it's NOT in the registered list
        - Only use "unknown" if confidence is very low (<0.5) or request is unintelligible
        - The system supports ANY entity through dynamic fallback - your job is just to identify it!
        """

        system_prompt = (
            "You are an entity extraction expert that identifies the PRIMARY subject of user requests. "
            "Your job is simple: extract the main entity/concept the user wants to work with. "
            "Return it as a single, simple noun (lowercase, singular form). Examples: 'student', 'book', "
            "'api', 'product', 'vehicle', 'employee', 'database', 'ui'. Don't worry if the entity isn't "
            "in a predefined list - the system handles ANY entity through dynamic fallback. Just extract "
            "what the user is talking about. Only return 'unknown' if confidence is very low (<0.5) or "
            "the request is completely unintelligible."
        )

        try:
            # Use the new JSON enforcement functionality
            # Note: detected_entity accepts ANY string (not constrained to enum)
            # This allows dynamic entity recognition with GenericBAE fallback
            json_schema = {
                "detected_entity": "string",  # Any entity name (lowercase, singular)
                "confidence": 0.0,
                "reasoning": "string",
                "language_detected": "string",
                "action_intent": "create|update|delete|list|relationship|unknown",
                "relationship_analysis": {
                    "is_relationship_request": True,
                    "entities_mentioned": ["list of strings"],
                    "primary_entity": "string",
                    "secondary_entity": "string",
                    "relationship_direction": "string"
                }
            }

            fallback_schema = {
                "detected_entity": "unknown",
                "confidence": 0.0,
                "reasoning": "Failed to parse LLM response",
                "language_detected": "unknown",
                "action_intent": "unknown",
                "relationship_analysis": {
                    "is_relationship_request": False,
                    "entities_mentioned": [],
                    "primary_entity": None,
                    "secondary_entity": None,
                    "relationship_direction": None
                },
                "error": True
            }

            classification = self.llm.generate_json_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,
                json_schema=json_schema,
                fallback_schema=fallback_schema
            )

            # Validate the response - accept ANY entity name
            # The system will route to specific BAE if available, or GenericBAE fallback otherwise
            detected = classification.get("detected_entity", "unknown")
            
            # Basic validation: ensure it's a non-empty string
            if not detected or not isinstance(detected, str) or detected.strip() == "":
                classification["detected_entity"] = "unknown"
                classification["confidence"] = 0.0
                classification["reasoning"] = "Empty or invalid entity name"
            
            # US3: Write to cache if enabled and successful recognition
            if self.cache and classification.get("confidence", 0.0) > 0.5:
                try:
                    self.cache.cache_write(user_input, {
                        "entity_name": classification["detected_entity"],
                        "attributes": [],  # Not extracted at recognition stage
                        "entity_type": "STANDARD",  # Determined later by BaseBae
                        "requires_custom_logic": classification.get("relationship_analysis", {}).get("is_relationship_request", False),
                        "custom_logic_reasons": []
                    })
                except Exception as e:
                    # Cache write failure should not block recognition
                    import logging
                    logging.getLogger(__name__).warning(f"⚠️  Cache write failed: {e}")
            
            return classification

        except Exception as e:
            # Error handling - return unknown classification
            return {
                "detected_entity": "unknown",
                "confidence": 0.0,
                "reasoning": f"Failed to parse LLM response: {str(e)}",
                "language_detected": "unknown",
                "action_intent": "unknown",
                "relationship_analysis": {
                    "is_relationship_request": False,
                    "entities_mentioned": [],
                    "primary_entity": None,
                    "secondary_entity": None,
                    "relationship_direction": None
                },
                "error": str(e),
            }

    def _gather_context_info(self) -> str:
        """Gather rich context about existing entities, attributes, and relationships"""
        if not self.context_store:
            return "No context information available."
        
        context_parts = []
        
        # Get existing entities
        try:
            entities = self.context_store.get_entities()
            if entities:
                context_parts.append("### Existing Entities:")
                for entity in entities:
                    entity_name = entity.get("name", "Unknown")
                    entity_type = entity.get("type", "Unknown")
                    context_parts.append(f"- {entity_name} ({entity_type})")
                    
                    # Add attributes if available
                    data = entity.get("data", {})
                    if isinstance(data, dict):
                        # Check different data formats
                        if "knowledge" in data:
                            knowledge = data["knowledge"]
                            if isinstance(knowledge, dict) and "attributes" in knowledge:
                                attrs = knowledge["attributes"]
                                if attrs:
                                    context_parts.append(f"  Attributes: {', '.join(attrs)}")
                        elif "attributes" in data:
                            attrs = data["attributes"]
                            if attrs:
                                context_parts.append(f"  Attributes: {', '.join(attrs)}")
            else:
                context_parts.append("### Existing Entities: None")
        except Exception as e:
            # raise error
            raise Exception(f"Error retrieving existing entities: {str(e)}")
        
        # Get existing relationships
        try:
            relationships = []
            for entity in self.supported_entities:
                entity_rels = self.context_store.get_entity_relationships(entity)
                relationships.extend(entity_rels)
            
            if relationships:
                context_parts.append("### Existing Relationships:")
                for rel in relationships:
                    primary = rel.get("primary_entity", "Unknown")
                    related = rel.get("related_entity", "Unknown")
                    rel_type = rel.get("relationship_type", "Unknown")
                    context_parts.append(f"- {primary} → {related} ({rel_type})")
            else:
                context_parts.append("### Existing Relationships: None")
        except Exception as e:
            # raise error
            raise Exception(f"Error retrieving existing relationships: {str(e)}")
        
        # Get domain knowledge
        try:
            domain_entities = self.context_store.get_all_domain_entities()
            if domain_entities:
                context_parts.append("### Domain Knowledge:")
                for entity in domain_entities:
                    knowledge = self.context_store.get_domain_knowledge(entity)
                    if knowledge:
                        context_parts.append(f"- {entity}: {type(knowledge).__name__} available")
            else:
                context_parts.append("### Domain Knowledge: None")
        except Exception as e:
            # raise error
            raise Exception(f"Error retrieving domain knowledge: {str(e)}")
            
        return "\n".join(context_parts) if context_parts else "No context information available."

    def is_supported_entity(self, entity: str) -> bool:
        """Check if entity is supported"""
        return entity in self.supported_entities

    def get_supported_entities(self) -> List[str]:
        """Get list of supported entities"""
        return self.supported_entities.copy()
