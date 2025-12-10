import json
import logging
import os
import re
from typing import Any, Dict, Optional
from datetime import datetime

import openai
from dotenv import load_dotenv

load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress httpx logs unless in debug mode
# httpx logs every HTTP request at INFO level, which is too verbose for normal operation
httpx_logger = logging.getLogger("httpx")
if os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes"):
    httpx_logger.setLevel(logging.DEBUG)
else:
    httpx_logger.setLevel(logging.WARNING)  # Only show warnings and errors


class OpenAIClient:
    """
    OpenAI GPT-4o-mini client optimized for BAE (Business Autonomous Entity) operations.
    Focuses on domain entity reasoning and semantic coherence maintenance.
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.debug(f"Initialized OpenAI client with model: {self.model}")

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

    def _strip_markdown_formatting(self, response: str) -> str:
        """Strip markdown code block formatting from response"""
        response = response.strip()

        # Remove markdown code block markers
        if response.startswith("```python"):
            response = response[9:]  # Remove ```python
        elif response.startswith("```"):
            response = response[3:]  # Remove ```

        if response.endswith("```"):
            response = response[:-3]  # Remove trailing ```

        return response.strip()

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0,
        max_tokens: int = 2000,
        ensure_json: bool = False,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate response from OpenAI GPT-4o-mini with domain focus.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0 for deterministic)
            max_tokens: Maximum tokens in response
            ensure_json: If True, enforces JSON response format
            json_schema: Optional JSON schema to guide the response structure
            
        Returns:
            Generated response string (clean JSON if ensure_json=True)
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Enhance prompt for JSON enforcement if requested
            if ensure_json:
                enhanced_prompt = self._enhance_prompt_for_json(prompt, json_schema)
                messages.append({"role": "user", "content": enhanced_prompt})
            else:
                messages.append({"role": "user", "content": prompt})

            # Build API parameters conditionally for gpt-4 vs gpt-5 models
            api_params = {
                "model": self.model,
                "messages": messages
            }
            
            # gpt-5 models only support temperature=1 (default), so we omit it
            # gpt-4 models support custom temperature values
            if not self.model.startswith("gpt-5"):
                api_params["temperature"] = temperature
            
            # gpt-5 uses max_completion_tokens, gpt-4 uses max_tokens
            if self.model.startswith("gpt-5"):
                api_params["max_completion_tokens"] = max_tokens
            else:
                api_params["max_tokens"] = max_tokens
            
            response = self.client.chat.completions.create(**api_params)
            from baes.utils.metrics_tracker import add_tokens
            add_tokens(response.usage.prompt_tokens, response.usage.completion_tokens)

            response_content = response.choices[0].message.content

            # If JSON is required, clean and validate the response
            if ensure_json:
                return self._ensure_valid_json(response_content, json_schema)

            return response_content

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            error_response = f"Error generating response: {str(e)}"
            
            # If JSON was required, return a valid JSON error response
            if ensure_json:
                return json.dumps({
                    "error": True,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                    "fallback_response": True
                })
            
            return error_response

    def generate_json_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0,
        max_tokens: int = 2000,
        json_schema: Optional[Dict[str, Any]] = None,
        fallback_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate and parse JSON response with robust error handling and fallback strategies.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0 for deterministic)
            max_tokens: Maximum tokens in response
            json_schema: Optional JSON schema to guide the response structure
            fallback_schema: Optional fallback schema if primary parsing fails
            
        Returns:
            Parsed JSON as dictionary, or fallback response if parsing fails
        """
        try:
            # First attempt: Generate with JSON enforcement
            response_text = self.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                ensure_json=True,
                json_schema=json_schema
            )
            
            # Try to parse the response
            try:
                parsed_json = json.loads(response_text)
                return parsed_json
            except json.JSONDecodeError as parse_error:
                logger.warning(f"JSON parsing failed on first attempt: {parse_error}")
                
                # Second attempt: Try to extract JSON from the response
                extracted_json = self._extract_json_from_response(response_text)
                try:
                    parsed_json = json.loads(extracted_json)
                    logger.info("JSON successfully extracted and parsed on second attempt")
                    return parsed_json
                except json.JSONDecodeError as extract_error:
                    logger.warning(f"JSON extraction failed: {extract_error}")
                    
                    # Third attempt: Try to fix common JSON issues
                    fixed_json = self._fix_common_json_issues(response_text)
                    try:
                        parsed_json = json.loads(fixed_json)
                        logger.info("JSON successfully fixed and parsed on third attempt")
                        return parsed_json
                    except json.JSONDecodeError as fix_error:
                        logger.error(f"JSON fixing failed: {fix_error}")
                        
                        # Final fallback: Return structured error response
                        return self._create_fallback_json_response(
                            original_response=response_text,
                            error=str(fix_error),
                            fallback_schema=fallback_schema
                        )
                        
        except Exception as e:
            logger.error(f"JSON generation failed: {str(e)}")
            return self._create_fallback_json_response(
                original_response="",
                error=str(e),
                fallback_schema=fallback_schema
            )

    def _enhance_prompt_for_json(self, prompt: str, json_schema: Optional[Dict[str, Any]] = None) -> str:
        """Enhance prompt to ensure JSON response format"""
        json_instructions = """
CRITICAL: You MUST respond with valid JSON only. Do not include any text before or after the JSON.
Do not use markdown code blocks. Do not include explanations outside the JSON structure.

JSON REQUIREMENTS:
- Start with { and end with }
- Use double quotes for all strings
- Use proper JSON syntax (no trailing commas, valid types)
- Include all required fields
- Do not include any text outside the JSON structure
"""
        
        if json_schema:
            schema_str = json.dumps(json_schema, indent=2)
            json_instructions += f"""
EXPECTED JSON STRUCTURE:
{schema_str}

You must follow this exact structure. All fields are required unless marked as optional.
"""
        
        enhanced_prompt = f"{prompt}\n\n{json_instructions}"
        return enhanced_prompt

    def _ensure_valid_json(self, response: str, json_schema: Optional[Dict[str, Any]] = None) -> str:
        """Ensure the response is valid JSON with multiple fallback strategies"""
        # First, try to extract JSON from the response
        extracted_json = self._extract_json_from_response(response)
        
        # Try to parse the extracted JSON
        try:
            parsed = json.loads(extracted_json)
            # If successful, return the cleaned JSON
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
        
        # If extraction failed, try to fix common JSON issues
        fixed_json = self._fix_common_json_issues(response)
        try:
            parsed = json.loads(fixed_json)
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
        
        # If all attempts fail, return a structured error response
        error_response = {
            "error": True,
            "error_message": "Failed to generate valid JSON response",
            "original_response": response[:500],  # Truncate for safety
            "fallback_response": True
        }
        
        if json_schema:
            error_response["expected_schema"] = json_schema
        
        return json.dumps(error_response, ensure_ascii=False)

    def _fix_common_json_issues(self, response: str) -> str:
        """Fix common JSON formatting issues"""
        # Remove any text before the first {
        start_idx = response.find('{')
        if start_idx != -1:
            response = response[start_idx:]
        
        # Remove any text after the last }
        end_idx = response.rfind('}')
        if end_idx != -1:
            response = response[:end_idx + 1]
        
        # Fix common JSON syntax issues
        response = response.replace("'", '"')  # Replace single quotes with double quotes
        response = response.replace("True", "true")  # Fix boolean values
        response = response.replace("False", "false")
        response = response.replace("None", "null")
        
        # Remove trailing commas in objects and arrays
        response = re.sub(r',(\s*[}\]])', r'\1', response)
        
        # Fix unquoted property names
        response = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', response)
        
        return response.strip()

    def _create_fallback_json_response(
        self, 
        original_response: str, 
        error: str, 
        fallback_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a fallback JSON response when parsing fails"""
        fallback = {
            "error": True,
            "error_message": error,
            "original_response": original_response[:200] if original_response else "",
            "fallback_response": True,
            "timestamp": datetime.now().isoformat()
        }
        
        if fallback_schema:
            # Try to create a minimal valid response based on fallback schema
            try:
                for key, value in fallback_schema.items():
                    if key not in fallback:
                        fallback[key] = value
            except Exception as e:
                logger.warning(f"Failed to apply fallback schema: {e}")
        
        return fallback

    def generate_domain_entity_response(
        self,
        prompt: str,
        entity_type: str = "Student",
        context: str = "academic",
        temperature: float = 0,
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
            - Use sqlite3 for database operations with path: "../database/baes_system.db"
            - Include proper Pydantic models for requests/responses
            - Implement full CRUD: POST, GET (list), GET (single), PUT, DELETE
            - Use /api/{entity.lower()}s/ endpoint pattern with:
              * POST /api/{entity.lower()}s/ (create, return with id)
              * GET /api/{entity.lower()}s/ (list all)
              * GET /api/{entity.lower()}s/{{id}} (get by id)
              * PUT /api/{entity.lower()}s/{{id}} (update by id)
              * DELETE /api/{entity.lower()}s/{{id}} (delete by id)
            - Handle database with sqlite3 and proper row_factory
            - Database path must be: os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/baes_system.db"))
            - Add error handling for database connection failures
            - Ensure database file exists before connecting
            - Create separate response model that includes id field for API responses
            - Use 'id' as primary key in all endpoints, not other fields
            - ONLY use the attributes specified: {attributes}
            - Do NOT add extra fields beyond what's specified
            - Make all fields required (no Optional fields)

            Entity: {entity}
            Attributes (use ONLY these): {attributes}

            IMPORTANT: Use this database connection pattern:
            ```python
            def get_db_connection():
                db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/baes_system.db"))
                if not os.path.exists(db_path):
                    raise HTTPException(status_code=500, detail=f"Database not found at {{db_path}}")
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn
            ```

            Generate ONLY the complete Python code, no markdown, no explanations.
            """
        elif "Streamlit" in code_type or "UI" in code_type or "Frontend" in code_type:
            system_prompt = f"""
            You are generating Streamlit UI for {entity} entity management.

            CRITICAL REQUIREMENTS:
            - Create a complete functional Streamlit interface for {entity} CRUD operations
            - MUST include these imports at the top of the file:
              * import streamlit as st
              * import requests
              * import pandas as pd
              * from config import Config
            - MUST use API endpoint from Config.get_api_endpoint_url() method
            - Set API_URL = Config.get_api_endpoint_url("{entity.lower()}s") at the top of the file
            - Generate form fields dynamically based on provided attributes: {attributes}
            - Use st.dataframe() with column_config for proper table display with column names
            - Use pandas DataFrame (pd.DataFrame) to properly format data for st.dataframe()
            - Use SAFE attribute access with .get() method for all data fields to avoid KeyError
            - Handle missing or differently named fields gracefully (e.g., 'name' vs 'Name')
            - Implement working edit functionality using session state and forms
            - Implement working delete functionality using session state for confirmation (
                do NOT use st.confirm which doesn't exist)
            - For delete confirmation, use st.button() with session state to show/hide confirmation buttons
            - Delete confirmation pattern: First button shows "Are you sure?", second button performs actual delete
            - Include proper error handling and success messages
            - Use st.rerun() for real-time updates (NOT st.experimental_rerun which is deprecated) after operations
            - Use business vocabulary and user-friendly labels
            - Follow the EXACT structure from the frontend_gen.txt template
            - ONLY use the attributes specified: {attributes}
            - Generate complete form fields for both create and edit operations
            - Do NOT add extra fields beyond what's specified

            Entity: {entity}
            Attributes (use ONLY these): {attributes}

            IMPORTANT: Generate ALL form input fields based on the attributes provided.
            For example, if attributes are ["name: str", "registration_number: str", "course: str"],
            generate text_input fields for each of these in both create and edit forms.

            CRITICAL ATTRIBUTE ACCESS PATTERN:
            - ALWAYS use .get() method for accessing dictionary fields: item.get('field_name', 'default_value')
            - NEVER use direct access like item['field_name'] which can cause KeyError
            - For display names in dropdowns/buttons, use fallback pattern:
              display_name = item.get('name', item.get('title', item.get('Name', f"ID {{item['id']}}")))
            - Handle both lowercase and capitalized field names gracefully

            DELETE CONFIRMATION PATTERN (required):
            ```python
            # Example delete confirmation pattern using session state
            # Use safe attribute access to get display name
            display_name = selected_item.get('name', selected_item.get('Name', f"ID {{selected_item['id']}}"))
            if st.button(f"Delete {{display_name}}", type="secondary"):
                st.session_state.confirm_delete_id = selected_item['id']

            if hasattr(st.session_state, 'confirm_delete_id') and st.session_state.confirm_delete_id:
                st.warning("⚠️ Are you sure you want to delete this {entity.lower()}?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Delete", type="primary"):
                        # Perform actual delete API call here
                        # Clear confirmation state
                        del st.session_state.confirm_delete_id
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel"):
                        del st.session_state.confirm_delete_id
                        st.rerun()
            ```

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

        response = self.generate_response(prompt, system_prompt, temperature=0)

        # Strip markdown formatting if present
        return self._strip_markdown_formatting(response)

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

        # Use the new JSON enforcement functionality
        json_schema = {
            "is_semantically_coherent": True,
            "coherence_score": 85,
            "business_vocabulary_preserved": True,
            "domain_rules_followed": True,
            "identified_issues": [],
            "improvement_suggestions": []
        }

        # Use the new generate_json_response method for robust JSON handling
        return self.generate_json_response(
            prompt=prompt,
            system_prompt=f"""
            You are working with Business Autonomous Entities (BAEs) that represent domain entities
            as living, autonomous agents within the system.

            Current focus: {entity} entity in academic context

            Your responsibilities:
            1. Maintain semantic coherence between business vocabulary and technical implementation
            2. Preserve domain knowledge and business rules
            3. Ensure generated artifacts reflect business terminology
            4. Focus on domain entity representation, not software engineering roles
            5. Enable runtime evolution while preserving semantic consistency

            Always prioritize business domain understanding and vocabulary preservation.
            """,
            temperature=0,
            json_schema=json_schema,
            fallback_schema={
                "is_semantically_coherent": False,
                "coherence_score": 0,
                "business_vocabulary_preserved": False,
                "domain_rules_followed": False,
                "identified_issues": ["Validation failed due to parsing error"],
                "improvement_suggestions": ["Review the generated code manually"]
            }
        )

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

        # Use the new JSON enforcement functionality
        json_schema = {
            "intent": "create_entity",
            "entity_focus": "Student",
            "requested_operations": ["create"],
            "attributes_mentioned": [],
            "business_vocabulary": [],
            "swea_coordination_needed": {
                "programmer": True,
                "frontend": True,
                "database": True
            },
            "complexity_level": "simple"
        }

        # Use the new generate_json_response method for robust JSON handling
        return self.generate_json_response(
            prompt=prompt,
            system_prompt=f"""
            You are working with Business Autonomous Entities (BAEs) that represent domain entities
            as living, autonomous agents within the system.

            Current focus: Business request interpretation in {context} context

            Your responsibilities:
            1. Maintain semantic coherence between business vocabulary and technical implementation
            2. Preserve domain knowledge and business rules
            3. Ensure generated artifacts reflect business terminology
            4. Focus on domain entity representation, not software engineering roles
            5. Enable runtime evolution while preserving semantic consistency

            Always prioritize business domain understanding and vocabulary preservation.
            """,
            temperature=0,
            json_schema=json_schema,
            fallback_schema={
                "intent": "parse_error",
                "entity_focus": "unknown",
                "requested_operations": [],
                "attributes_mentioned": [],
                "business_vocabulary": [],
                "swea_coordination_needed": {
                    "programmer": False,
                    "frontend": False,
                    "database": False
                },
                "complexity_level": "unknown"
            }
        )
