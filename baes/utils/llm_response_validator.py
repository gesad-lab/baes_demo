"""
LLM Response Validation Utility - Phase 3 Prevention
Provides centralized validation for LLM responses to prevent common errors like
'dict' object has no attribute 'strip' and JSON parsing failures.
"""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class LLMResponseValidator:
    """Centralized validator for LLM responses across all SWEA agents"""

    # Standard schemas for different SWEA response types
    SWEA_RESPONSE_SCHEMAS = {
        "database": {
            "required_fields": [
                "attributes",
                "additional_requirements",
                "constraints",
                "modifications",
            ],
            "optional_fields": ["explanation"],
            "attribute_formats": ["string", "dict_with_name_type"],
        },
        "backend": {
            "required_fields": [
                "attributes",
                "additional_requirements",
                "code_improvements",
                "modifications",
            ],
            "optional_fields": ["explanation"],
            "attribute_formats": ["string", "dict_with_name_type"],
        },
        "frontend": {
            "required_fields": ["attributes", "ui_improvements", "layout_changes", "modifications"],
            "optional_fields": ["explanation"],
            "attribute_formats": ["string", "dict_with_name_type"],
        },
    }

    @classmethod
    def validate_response_structure(
        cls, response: Dict[str, Any], swea_type: str
    ) -> Dict[str, Any]:
        """
        Validate and normalize LLM response structure

        Args:
            response: Raw LLM response dictionary
            swea_type: Type of SWEA ("database", "backend", "frontend")

        Returns:
            Validated and normalized response dictionary

        Raises:
            ValueError: If response is invalid and cannot be normalized
        """
        schema = cls.SWEA_RESPONSE_SCHEMAS.get(swea_type.lower())
        if not schema:
            logger.warning(f"No schema defined for SWEA type: {swea_type}")
            return response

        validated = {}

        # Validate required fields
        for field in schema["required_fields"]:
            if field not in response:
                logger.warning(f"LLM response missing required field '{field}' for {swea_type}SWEA")
                validated[field] = []  # Default to empty list
            else:
                validated[field] = response[field]

        # Add optional fields if present
        for field in schema["optional_fields"]:
            validated[field] = response.get(field, "No explanation provided")

        # Special handling for attributes field (prevent dict/strip error)
        if "attributes" in validated:
            validated["attributes"] = cls._normalize_attributes(validated["attributes"], swea_type)

        # Ensure all list fields are actually lists of strings
        for field in schema["required_fields"]:
            if field in validated and field != "attributes":
                validated[field] = cls._ensure_string_list(validated[field], field)

        logger.debug(
            f"Validated {swea_type}SWEA response with {len(validated.get('attributes', []))} attributes"
        )
        return validated

    @classmethod
    def _normalize_attributes(cls, attributes: Any, swea_type: str) -> List[str]:
        """
        Normalize attributes to consistent string format to prevent strip() errors

        Args:
            attributes: Raw attributes from LLM (could be list of strings, dicts, or mixed)
            swea_type: Type of SWEA for logging context

        Returns:
            List of normalized string attributes in "name:type" format
        """
        if not isinstance(attributes, list):
            logger.warning(f"{swea_type}SWEA attributes field is not a list: {type(attributes)}")
            return []

        normalized = []
        for i, attr in enumerate(attributes):
            try:
                if isinstance(attr, dict):
                    # Convert dict format to string format
                    name = attr.get("name", f"field_{i}")
                    attr_type = attr.get("type", "str")
                    normalized_attr = f"{name}:{attr_type}"
                    normalized.append(normalized_attr)
                    logger.debug(
                        f"{swea_type}SWEA: Converted dict attribute to string: {normalized_attr}"
                    )

                elif isinstance(attr, str):
                    # Already in correct format
                    normalized.append(attr)

                elif attr is None:
                    # Skip None values
                    logger.warning(f"{swea_type}SWEA: Skipping None attribute at index {i}")
                    continue

                else:
                    # Convert unexpected types to string
                    str_attr = str(attr)
                    if str_attr and str_attr != "None":
                        normalized.append(str_attr)
                        logger.warning(
                            f"{swea_type}SWEA: Converted {type(attr)} attribute to string: {str_attr}"
                        )

            except Exception as e:
                logger.error(f"{swea_type}SWEA: Error processing attribute {i} ({attr}): {e}")
                # Skip problematic attributes rather than failing
                continue

        return normalized

    @classmethod
    def _ensure_string_list(cls, field_value: Any, field_name: str) -> List[str]:
        """
        Ensure field value is a list of strings

        Args:
            field_value: Raw field value from LLM
            field_name: Name of the field for logging

        Returns:
            List of strings
        """
        if not isinstance(field_value, list):
            if isinstance(field_value, str):
                return [field_value]
            elif field_value is None:
                return []
            else:
                return [str(field_value)]

        # Convert all items to strings and filter out empty/None values
        string_list = []
        for item in field_value:
            if item is not None:
                str_item = str(item).strip()
                if str_item:
                    string_list.append(str_item)

        return string_list

    @classmethod
    def validate_json_parseable(cls, response_text: str) -> Dict[str, Any]:
        """
        Validate that response text can be parsed as JSON using the new JSON enforcement functionality

        Args:
            response_text: Raw text response from LLM

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If response cannot be parsed as valid JSON
        """
        try:
            # Use the new JSON enforcement functionality from OpenAIClient
            from baes.llm.openai_client import OpenAIClient
            
            client = OpenAIClient()
            
            # Create a generic schema for any JSON response
            json_schema = {
                "data": "any",
                "success": True,
                "error": "string"
            }
            
            fallback_schema = {
                "data": {},
                "success": False,
                "error": "JSON parsing failed",
                "fallback_response": True
            }
            
            parsed_response = client.generate_json_response(
                prompt=f"Parse this JSON response: {response_text}",
                json_schema=json_schema,
                fallback_schema=fallback_schema
            )
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"JSON parsing failed for response: {e}")
            logger.debug(f"Problematic response text: {response_text}")
            raise ValueError(f"Invalid JSON response: {e}")

    @classmethod
    def _clean_json_response(cls, response: str) -> str:
        """
        Clean LLM response to extract JSON from markdown code blocks and fix common issues

        Args:
            response: Raw response text from LLM

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        if "```json" in response:
            pattern = r"```json\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                response = match.group(1).strip()
        elif "```" in response:
            pattern = r"```\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                response = match.group(1).strip()

        # Fix common JSON issues
        response = response.strip()

        # Remove any leading/trailing text that's not JSON
        if response.startswith("{") and response.endswith("}"):
            pass  # Looks like pure JSON
        else:
            # Try to extract JSON object from text
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                response = json_match.group(0)

        return response

    @classmethod
    def create_fallback_response(
        cls, swea_type: str, original_attributes: List[str]
    ) -> Dict[str, Any]:
        """
        Create a fallback response when LLM response is invalid

        Args:
            swea_type: Type of SWEA ("database", "backend", "frontend")
            original_attributes: Original attributes to preserve

        Returns:
            Valid fallback response dictionary
        """
        schema = cls.SWEA_RESPONSE_SCHEMAS.get(
            swea_type.lower(), cls.SWEA_RESPONSE_SCHEMAS["database"]
        )

        fallback = {
            "attributes": original_attributes or ["name:str", "created_at:str"],
            "explanation": f"Fallback response due to LLM parsing error for {swea_type}SWEA",
        }

        # Add empty lists for all required fields
        for field in schema["required_fields"]:
            if field not in fallback:
                fallback[field] = []

        logger.info(
            f"Created fallback response for {swea_type}SWEA with {len(fallback['attributes'])} attributes"
        )
        return fallback


# Convenience functions for direct use in SWEA agents
def validate_database_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate DatabaseSWEA response"""
    return LLMResponseValidator.validate_response_structure(response, "database")


def validate_backend_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate BackendSWEA response"""
    return LLMResponseValidator.validate_response_structure(response, "backend")


def validate_frontend_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate FrontendSWEA response"""
    return LLMResponseValidator.validate_response_structure(response, "frontend")


def parse_llm_json_response(
    response_text: str, swea_type: str, original_attributes: List[str] = None
) -> Dict[str, Any]:
    """
    Parse and validate LLM JSON response with fallback handling

    Args:
        response_text: Raw text response from LLM
        swea_type: Type of SWEA for validation
        original_attributes: Original attributes for fallback

    Returns:
        Validated response dictionary
    """
    try:
        # Parse JSON
        parsed = LLMResponseValidator.validate_json_parseable(response_text)

        # Validate structure
        validated = LLMResponseValidator.validate_response_structure(parsed, swea_type)

        return validated

    except (ValueError, KeyError, TypeError) as e:
        logger.warning(f"LLM response parsing failed for {swea_type}SWEA: {e}")
        return LLMResponseValidator.create_fallback_response(swea_type, original_attributes or [])
