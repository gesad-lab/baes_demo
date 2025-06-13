import json
import logging
import os
import re
from typing import Any, Dict, Optional

import openai
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI GPT-4o-mini client optimized for BAE (Business Autonomous Entity) operations.
    Focuses on domain entity reasoning and semantic coherence maintenance.
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Initialized OpenAI client with model: {self.model}")

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from response that might be wrapped in markdown code blocks"""
        # Remove markdown code blocks if present
        if "```json" in response:
            # Extract content between ```json and ```
            match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in response:
            # Extract content between ``` and ```
            match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Return original response if no code blocks found
        return response.strip()

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        """Generate response from OpenAI GPT-4o-mini with domain focus"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error generating response: {str(e)}"

    def generate_domain_entity_response(
        self,
        prompt: str,
        entity_type: str = "Student",
        context: str = "academic",
        temperature: float = 0.2,
    ) -> str:
        """Generate response with specific domain entity focus and semantic coherence"""
        system_prompt = f"""
        You are working with Business Autonomous Entities (BAEs) that represent domain entities
        as living, autonomous agents within the system.

        Current focus: {entity_type} entity in {context} context

        Your responsibilities:
        1. Maintain semantic coherence between business vocabulary and technical implementation
        2. Preserve domain knowledge and business rules
        3. Ensure generated artifacts reflect business terminology
        4. Focus on domain entity representation, not software engineering roles
        5. Enable runtime evolution while preserving semantic consistency

        Always prioritize business domain understanding and vocabulary preservation.
        """

        return self.generate_response(prompt, system_prompt, temperature)

    def generate_code_with_domain_focus(
        self, prompt: str, code_type: str, entity_context: Dict[str, Any]
    ) -> str:
        """Generate code while maintaining domain entity coherence"""
        entity = entity_context.get("entity", "Student")
        attributes = entity_context.get("attributes", [])
        business_rules = entity_context.get("business_rules", [])

        # Special handling for FastAPI routes to ensure proper router generation
        if "FastAPI" in code_type or "Routes" in code_type or "API" in code_type:
            system_prompt = f"""
            You are generating FastAPI routes for {entity} entity.

            CRITICAL REQUIREMENTS:
            - Use APIRouter, NOT FastAPI app
            - Start with: router = APIRouter(prefix="/api", tags=["{entity}s"])
            - Use sqlite3 for database operations with path: "../database/academic.db"
            - Include proper Pydantic models for requests/responses
            - Implement full CRUD: POST, GET (list), GET (single), PUT, DELETE
            - Use /api/{entity.lower()}s/ endpoint pattern with:
              * POST /api/{entity.lower()}s/ (create, return with id)
              * GET /api/{entity.lower()}s/ (list all)
              * GET /api/{entity.lower()}s/{{id}} (get by id)
              * PUT /api/{entity.lower()}s/{{id}} (update by id)
              * DELETE /api/{entity.lower()}s/{{id}} (delete by id)
            - Handle database with sqlite3 and proper row_factory
            - Database path must be: os.path.join(os.path.dirname(__file__), "../database/academic.db")
            - Create separate response model that includes id field for API responses
            - Use 'id' as primary key in all endpoints, not other fields
            - ONLY use the attributes specified: {attributes}
            - Do NOT add extra fields beyond what's specified
            - Make all fields required (no Optional fields)

            Entity: {entity}
            Attributes (use ONLY these): {attributes}

            Generate ONLY the complete Python code, no markdown, no explanations.
            """
        elif "Streamlit" in code_type or "UI" in code_type or "Frontend" in code_type:
            system_prompt = f"""
            You are generating Streamlit UI for {entity} entity management.

            CRITICAL REQUIREMENTS:
            - Create a complete Streamlit interface for {entity} management
            - Use API endpoint: http://localhost:8100/api/{entity.lower()}s/
            - Include form for creating new {entity.lower()}s
            - Include table for displaying all {entity.lower()}s
            - Include management features (edit/delete)
            - Use business vocabulary and user-friendly labels
            - Include error handling and success messages
            - Use st.rerun() for real-time updates
            - Include the words "student", "management", "form", "table" in the UI
            - ONLY use the attributes specified: {attributes}
            - Do NOT add extra fields beyond what's specified

            Entity: {entity}
            Attributes (use ONLY these): {attributes}

            Generate ONLY the complete Python Streamlit code, no markdown, no explanations.
            """
        else:
            system_prompt = f"""
            You are a code generation agent working under BAE coordination for the {entity} domain entity.

            Code Type: {code_type}
            Entity Attributes: {attributes}
            Business Rules: {business_rules}

            Requirements:
            1. Generate clean, professional {code_type} code
            2. Use business vocabulary in naming and documentation
            3. Include proper validation reflecting business rules
            4. Maintain semantic coherence with domain entity representation
            5. Ensure code is immediately executable and follows best practices
            6. Focus on domain entity operations, not generic CRUD

            Return ONLY the code, no explanations or markdown formatting.
            """

        return self.generate_response(prompt, system_prompt, temperature=0.1)

    def validate_semantic_coherence(
        self, artifact_code: str, artifact_type: str, domain_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that generated artifacts maintain semantic coherence with domain"""
        entity = domain_context.get("entity", "Student")
        business_vocabulary = domain_context.get("business_vocabulary", [])

        prompt = f"""
        Validate this {artifact_type} artifact for semantic coherence with {entity} domain entity:

        Artifact Code:
        {artifact_code}

        Domain Context:
        - Entity: {entity}
        - Business Vocabulary: {business_vocabulary}

        Analyze and return JSON with:
        {{
            "is_semantically_coherent": boolean,
            "coherence_score": 0-100,
            "business_vocabulary_preserved": boolean,
            "domain_rules_followed": boolean,
            "identified_issues": [list of issues],
            "improvement_suggestions": [list of suggestions]
        }}

        Return ONLY valid JSON.
        """

        response = self.generate_domain_entity_response(prompt, entity)

        try:
            json_content = self._extract_json_from_response(response)
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse semantic coherence validation as JSON: {str(e)}")
            logger.error(f"Raw OpenAI response: {response}")
            return {
                "is_semantically_coherent": False,
                "coherence_score": 0,
                "error": f"Failed to parse validation response: {str(e)}",
                "raw_response": response,
            }

    def interpret_business_request(
        self, natural_language_input: str, context: str = "academic"
    ) -> Dict[str, Any]:
        """Interpret natural language business request for BAE processing"""
        prompt = f"""
        As a Business Request Interpreter for BAE systems, analyze this natural language input:
        "{natural_language_input}"

        Context: {context}

        Extract and return JSON with:
        {{
            "intent": "primary business intent",
            "entity_focus": "main domain entity involved",
            "requested_operations": ["list of domain operations needed"],
            "attributes_mentioned": ["list of entity attributes mentioned"],
            "business_vocabulary": ["key business terms to preserve"],
            "swea_coordination_needed": {{
                "programmer": boolean,
                "frontend": boolean,
                "database": boolean
            }},
            "complexity_level": "simple|moderate|complex"
        }}

        Return ONLY valid JSON.
        """

        response = self.generate_domain_entity_response(prompt, context=context)

        try:
            json_content = self._extract_json_from_response(response)
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse business request interpretation as JSON: {str(e)}")
            logger.error(f"Raw OpenAI response: {response}")
            return {
                "intent": "parse_error",
                "error": f"Failed to parse business request: {str(e)}",
                "raw_response": response,
            }
