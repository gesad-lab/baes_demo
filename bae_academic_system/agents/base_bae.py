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
        """Implementation of abstract method from BaseAgent"""
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
        - swea_coordination: list of SWEA tasks to accomplish the request
        - business_vocabulary: key terms that must be preserved in technical implementation
        - entity_focus: confirm this is about {self.entity_name} entities
        """
        
        response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        
        try:
            interpretation = json.loads(response)
            interpretation["entity"] = self.entity_name
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
        As the {self.entity_name} BAE, validate this {artifact_type} artifact for domain rule compliance:
        
        Artifact Code:
        {artifact_code}
        
        Entity Focus: {self.entity_name}
        Business Rules: {'; '.join(self._get_business_rules())}
        
        Check for:
        1. Semantic coherence with {self.entity_name} domain entity
        2. Business vocabulary preservation
        3. Domain rule compliance specific to {self.entity_name}
        4. Business logic consistency
        5. Proper focus on {self.entity_name} entity operations
        
        Return JSON with validation results:
        {{
            "is_valid": boolean,
            "entity_focus_correct": boolean,
            "semantic_coherence_score": 0-100,
            "business_vocabulary_preserved": boolean,
            "domain_rules_followed": boolean,
            "issues": [list of issues if any],
            "recommendations": [list of improvements]
        }}
        """
        
        validation_response = self.llm.generate_domain_entity_response(prompt, self.entity_name)
        
        try:
            validation_result = json.loads(validation_response)
            validation_result["entity"] = self.entity_name
            return validation_result
        except json.JSONDecodeError:
            return {
                "entity": self.entity_name,
                "is_valid": False,
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
            return 0.0
        
        base_attributes = base_knowledge.get("core_attributes", [])
        if not base_attributes:
            return 0.0
        
        # Simplified calculation - in practice this would be more sophisticated
        modification_count = len(modifications)
        base_count = len(base_attributes)
        
        if modification_count == 0:
            return 100.0
        
        reuse_percentage = max(0, (base_count - modification_count) / base_count * 100)
        return round(reuse_percentage, 2) 