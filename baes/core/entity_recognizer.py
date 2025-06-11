from baes.llm.openai_client import OpenAIClient
from typing import Dict, List, Optional
import json

class EntityRecognizer:
    """Uses OpenAI to recognize and classify entities from natural language requests"""
    
    def __init__(self):
        self.llm = OpenAIClient()
        self.supported_entities = ["student", "course", "teacher"]
        
    def recognize_entity(self, user_input: str) -> Dict[str, any]:
        """
        Classify user input to determine which BAE entity they're referring to
        """
        prompt = f"""
        Analyze this user request and determine which academic entity they want to work with:
        
        User Request: "{user_input}"
        
        Supported Entities:
        - student (aluno, estudante, discente): for managing students/learners
        - course (curso, disciplina, matéria): for managing courses/subjects  
        - teacher (professor, docente, instrutor): for managing teachers/instructors
        
        Return a JSON response with:
        {{
            "detected_entity": "student|course|teacher|unknown",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation of why you chose this entity",
            "language_detected": "detected language",
            "action_intent": "create|update|delete|list|unknown"
        }}
        
        If the request doesn't clearly map to any supported entity, use "unknown".
        """
        
        system_prompt = """You are an Entity Recognition specialist for an Academic BAE System. Your job is to accurately classify user requests to route them to the appropriate Business Autonomous Entity (BAE). Be precise and conservative - if unsure, classify as 'unknown'."""
        
        try:
            response = self.llm.generate_response(prompt, system_prompt, temperature=0.1)
            classification = json.loads(response)
            
            # Validate the response
            if classification.get("detected_entity") not in self.supported_entities + ["unknown"]:
                classification["detected_entity"] = "unknown"
                classification["confidence"] = 0.0
                
            return classification
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback classification
            return {
                "detected_entity": "unknown",
                "confidence": 0.0,
                "reasoning": f"Failed to parse LLM response: {str(e)}",
                "language_detected": "unknown",
                "action_intent": "unknown",
                "error": str(e)
            }
    
    def is_supported_entity(self, entity: str) -> bool:
        """Check if entity is supported"""
        return entity in self.supported_entities
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entities"""
        return self.supported_entities.copy() 