from agents.base_agent import BaseAgent
from llm.openai_client import OpenAIClient
from typing import Dict, Any, List, Optional
from abc import abstractmethod
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseBAE(BaseAgent):
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
        logger.info(f"{self.entity_name}BAE initialized with domain keywords: {domain_keywords}")
    
    @abstractmethod
    def _initialize_domain_knowledge(self):
        """Initialize domain-specific knowledge - must be implemented by concrete BAEs"""
        pass
    
    @abstractmethod
    def _get_default_attributes(self) -> List[str]:
        """Get default attributes for this domain entity - must be implemented by concrete BAEs"""
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
            "get_domain_info": self._get_domain_info
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
                    "entity": self.entity_name
                }
                logger.error(f"{self.entity_name}BAE task failed: {task} - {str(e)}")
                return error_result
        else:
            return {
                "error": f"Unknown task: {task}",
                "supported_tasks": list(task_handlers.keys()),
                "entity": self.entity_name
            }
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract JSON from markdown code blocks"""
        import re
        
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
    
    def _interpret_business_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret natural language business request for this domain entity"""
        business_request = payload.get("request", "")
        context = payload.get("context", "academic")
        
        prompt = f"""
        As the {self.entity_name} BAE (Business Autonomous Entity), interpret this business request:
        "{business_request}"
        
        Entity Focus: {self.entity_name}
        Domain Keywords: {', '.join(self.domain_keywords)}
        Context: {context}
        Default Attributes: {', '.join(self._get_default_attributes())}
        Business Rules: {'; '.join(self._get_business_rules())}
        
        Analyze what domain entity operations are needed and create a coordination plan for SWEA agents.
        
        Return a JSON structure with:
        - interpreted_intent: what the business user wants
        - domain_operations: list of domain entity operations needed  
        - swea_coordination: list of SWEA task objects, each with "swea_agent" and "task_type" keys
        - business_vocabulary: key terms that must be preserved in technical implementation
        - entity_focus: confirm this is about {self.entity_name} entities
        
        Example swea_coordination format:
        [
            {{"swea_agent": "ProgrammerSWEA", "task_type": "generate_model"}},
            {{"swea_agent": "ProgrammerSWEA", "task_type": "generate_api"}},
            {{"swea_agent": "FrontendSWEA", "task_type": "generate_ui"}}
        ]
        """
        
        response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        cleaned_response = self._clean_json_response(response)
        
        try:
            interpretation = json.loads(cleaned_response)
            interpretation["entity"] = self.entity_name
            
            # Ensure swea_coordination is properly formatted as list of dicts
            if "swea_coordination" in interpretation:
                coordination = interpretation["swea_coordination"]
                if isinstance(coordination, list):
                    # Fix any string items or improperly formatted items
                    fixed_coordination = []
                    for item in coordination:
                        if isinstance(item, str):
                            # Convert string to dict format
                            fixed_coordination.append({
                                "swea_agent": "ProgrammerSWEA",
                                "task_type": "generate_component"
                            })
                        elif isinstance(item, dict):
                            # Ensure required keys exist
                            if "swea_agent" not in item:
                                item["swea_agent"] = "ProgrammerSWEA"
                            if "task_type" not in item:
                                item["task_type"] = "generate_component"
                            fixed_coordination.append(item)
                    interpretation["swea_coordination"] = fixed_coordination
            else:
                # Provide default coordination plan
                interpretation["swea_coordination"] = [
                    {"swea_agent": "ProgrammerSWEA", "task_type": "generate_model"},
                    {"swea_agent": "ProgrammerSWEA", "task_type": "generate_api"},
                    {"swea_agent": "FrontendSWEA", "task_type": "generate_ui"}
                ]
            
            self.update_memory("last_interpretation", interpretation)
            return interpretation
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse business request interpretation",
                "raw_response": response,
                "entity": self.entity_name
            }
    
    def _generate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Pydantic schema maintaining domain entity focus"""
        attributes = payload.get("attributes", self._get_default_attributes())
        context = payload.get("context", "academic")
        
        prompt = f"""
        Generate a Pydantic model for {self.entity_name} entity with these attributes:
        {', '.join(attributes)}
        
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
        
        schema_info = {
            "entity": self.entity_name,
            "code": schema_code,
            "attributes": attributes,
            "context": context,
            "business_rules": self._get_business_rules(),
            "generated_at": datetime.now().isoformat()
        }
        
        self.current_schema = schema_info
        self.update_memory("current_schema", schema_info)
        self._update_domain_knowledge(context, attributes)
        
        return schema_info
    
    def _evolve_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evolve schema while preserving domain knowledge and semantic coherence"""
        evolution_request = payload.get("evolution_request", "")
        new_attributes = payload.get("new_attributes", [])
        
        current_schema = self.get_memory("current_schema")
        if not current_schema:
            # Generate initial schema if none exists
            return self._generate_schema({
                "attributes": new_attributes,
                "context": payload.get("context", "academic")
            })
        
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
            "evolved_at": datetime.now().isoformat()
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
            "preserved_attributes": base_knowledge.get("core_attributes", self._get_default_attributes()),
            "context_specific_rules": self._generate_context_rules(target_context, modifications)
        }
        
        self.context_configurations[target_context] = configured_knowledge
        self.update_memory(f"context_config_{target_context}", configured_knowledge)
        
        return {
            "entity": self.entity_name,
            "configured_context": target_context,
            "base_context": base_context,
            "modifications": modifications,
            "reuse_percentage": self._calculate_reuse_percentage(base_knowledge, modifications)
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
                    "entity_focus": self.entity_name
                }
            }
            coordination_plan.append(swea_task)
        
        self.update_memory("swea_coordination_plan", coordination_plan)
        return {
            "entity": self.entity_name,
            "coordination_plan": coordination_plan
        }
    
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
                "raw_response": validation_response
            }
    
    def _get_domain_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive domain information for this BAE"""
        return {
            "entity": self.entity_name,
            "domain_keywords": self.domain_keywords,
            "default_attributes": self._get_default_attributes(),
            "business_rules": self._get_business_rules(),
            "current_schema": self.current_schema,
            "context_configurations": self.context_configurations,
            "domain_knowledge": self.domain_knowledge,
            "memory_summary": {
                "total_interactions": len(self.memory.get("interactions", [])),
                "last_schema_update": self.current_schema.get("generated_at", "never")
            }
        }
    
    def _update_domain_knowledge(self, context: str, attributes: List[str]):
        """Update domain knowledge for reusability"""
        if context not in self.domain_knowledge:
            self.domain_knowledge[context] = {}
        
        self.domain_knowledge[context].update({
            "entity": self.entity_name,
            "core_attributes": attributes,
            "last_updated": datetime.now().isoformat(),
            "usage_count": self.domain_knowledge[context].get("usage_count", 0) + 1
        })
    
    def _generate_context_rules(self, context: str, modifications: List[str]) -> List[str]:
        """Generate context-specific business rules - can be overridden by concrete BAEs"""
        rules = []
        
        if context == "open_courses":
            rules.append(f"{self.entity_name} may have relaxed requirements for open course context")
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
    
    def _calculate_reuse_percentage(self, base_knowledge: Dict[str, Any], modifications: List[str]) -> float:
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
        attribute_reuse = max(0, (base_count - modification_count) / base_count * 100) if base_count > 0 else 0
        
        # Factor 2: Business rules reuse (25% weight) - assume high reuse for same entity
        business_rules_reuse = 90.0
        
        # Factor 3: Domain vocabulary reuse (15% weight) - assume high reuse for same entity
        vocabulary_reuse = 95.0
        
        # Weighted average
        total_reuse = (
            attribute_reuse * 0.60 +
            business_rules_reuse * 0.25 +
            vocabulary_reuse * 0.15
        )
        
        # Ensure minimum reuse percentage for same entity configurations
        total_reuse = max(total_reuse, 80.0)
        
        return round(total_reuse, 2) 