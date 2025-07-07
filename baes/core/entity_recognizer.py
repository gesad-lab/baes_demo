import json
from typing import Dict, List, Optional

from baes.llm.openai_client import OpenAIClient


class EntityRecognizer:
    """Uses OpenAI to recognize and classify entities from natural language requests"""

    def __init__(self, context_store=None):
        self.llm = OpenAIClient()
        self.supported_entities = ["student", "course", "teacher"]
        self.context_store = context_store

    def recognize_entity(self, user_input: str) -> Dict[str, any]:
        """
        Classify user input to determine which BAE entity they're referring to.
        For relationship creation requests, correctly identifies the primary entity 
        (the one being modified) rather than the secondary entity being added.
        """
        
        # Gather context about existing entities and relationships
        context_info = self._gather_context_info()
        
        prompt = f"""
        You are an Entity Recognition specialist for an Academic BAE System. Your task is to analyze user requests and determine which entity they want to work with, particularly for relationship creation scenarios.

        User Request: "{user_input}"

        ## Current System Context:
        {context_info}

        ## Analysis Instructions:
        Follow this structured reasoning process:

        ### Step 1: Identify all entities mentioned in the request
        - List all entities (student, course, teacher) mentioned in the request
        - Identify the explicit action being requested

        ### Step 2: Determine request type
        - Is this a RELATIONSHIP request (e.g., "add X to Y", "connect X with Y", "link X to Y")?
        - Is this a CREATION request (e.g., "create X", "add X entity")?
        - Is this an UPDATE request (e.g., "modify X", "change X")?
        - Is this a DELETION request (e.g., "remove X", "delete X")?

        ### Step 3: For RELATIONSHIP requests - Apply the Primary Entity Rule
        **CRITICAL RULE**: The PRIMARY entity is the one that will be MODIFIED to include a reference to the secondary entity.
        
        Examples:
        - "add course to student" → PRIMARY: student (student gets course_id field)
        - "add student to course" → PRIMARY: course (course gets student_id field)  
        - "connect teacher with course" → Ambiguous - need more context
        - "assign teacher to course" → PRIMARY: course (course gets teacher_id field)
        - "enroll student in course" → PRIMARY: student (student gets course_id field)

        ### Step 4: Chain-of-thought reasoning for relationships
        - Which entity's schema needs to be modified?
        - Which entity will receive the foreign key reference?
        - Direction of relationship: From [secondary] TO [primary]
        - The entity being "added TO" another is usually the foreign key holder

        ### Step 5: Final determination
        - Declare the primary entity based on schema modification requirements
        - Provide confidence level (0.0-1.0)
        - Explain your reasoning clearly

        ## Response Format:
        Return a JSON response with:
        {{
            "detected_entity": "student|course|teacher|unknown",
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

        ## Supported Entities:
        - student (aluno, estudante, discente): for managing students/learners
        - course (curso, disciplina, matéria): for managing courses/subjects  
        - teacher (professor, docente, instrutor): for managing teachers/instructors

        **Important**: If the request doesn't clearly map to any supported entity or if you're uncertain about relationship direction, use "unknown" and explain why in your reasoning.
        """

        system_prompt = (
            "You are a data modeling expert tasked with interpreting natural language commands "
            "to define system components. Your primary function is to accurately identify the "
            "main subject (the 'primary entity') of a user's request, which determines which "
            "part of the system's data model will be created or modified. When a request "
            "describes a relationship between entities, your most critical task is to determine "
            "which entity's schema must be altered to establish the link. You must use a "
            "structured, step-by-step reasoning process. If the primary entity cannot be "
            "determined with high confidence, you must classify it as 'unknown' and explain "
            "your reasoning."
        )

        try:
            # Use the new JSON enforcement functionality
            json_schema = {
                "detected_entity": "student|course|teacher|unknown",
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

            # Validate the response
            if classification.get("detected_entity") not in self.supported_entities + ["unknown"]:
                classification["detected_entity"] = "unknown"
                classification["confidence"] = 0.0
                classification["reasoning"] = f"Invalid entity detected: {classification.get('detected_entity')}"

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
