import logging
import os
import sqlite3
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class DatabaseSWEA(BaseAgent):
    """SWEA responsible for preparing SQLite database schemas based on entity attributes."""

    def __init__(self):
        super().__init__("DatabaseSWEA", "Database Provisioning Agent", "SWEA")
        self._managed_system_manager = None  # Lazy initialization
        self.llm_client = OpenAIClient()

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    _SUPPORTED_TASKS = {"setup_database": "_setup_database"}

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                f"Unknown task. Supported tasks: {list(self._SUPPORTED_TASKS.keys())}",
                "invalid_task",
            )
        method = getattr(self, self._SUPPORTED_TASKS[task])
        try:
            return method(payload)
        except Exception as e:
            return self.create_error_response(task, str(e), "execution_error")

    def _interpret_feedback_for_database_setup(self, feedback: List[str], entity: str, original_attributes: List[str]) -> Dict[str, Any]:
        """
        Generic feedback interpretation using LLM to understand what database changes are needed.
        This approach can handle any type of feedback without hardcoded conditions.
        """
        if not feedback:
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "constraints": [],
                "modifications": []
            }

        feedback_text = "\n".join(feedback)
        
        system_prompt = f"""You are a database design expert helping to interpret feedback for improving a database setup.

CONTEXT:
- Entity: {entity}
- Original attributes: {original_attributes}
- Feedback received: {feedback_text}

TASK:
Interpret the feedback and provide specific database setup improvements in JSON format.

RESPONSE FORMAT (JSON only):
{{
    "attributes": ["list", "of", "final", "attributes", "with", "types"],
    "additional_requirements": ["any", "new", "requirements", "identified"],
    "constraints": ["database", "constraints", "to", "add"],
    "modifications": ["specific", "changes", "to", "make"],
    "explanation": "brief explanation of changes made based on feedback"
}}

GUIDELINES:
- Preserve existing attributes unless feedback specifically requests changes
- Add new attributes if feedback suggests missing fields
- Include proper data types (str, int, float, date, bool)
- Consider database best practices (indexes, constraints, relationships)
- Handle any type of feedback, even unexpected ones
- If feedback is unclear, make reasonable database design assumptions
"""

        user_prompt = f"""Based on the feedback provided, what database setup changes should be made for the {entity} entity?

Feedback to interpret:
{feedback_text}

Current attributes:
{original_attributes}

Please provide the JSON response with database improvements."""

        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            
            # Try to parse JSON response
            import json
            try:
                interpretation = json.loads(response)
                logger.info(f"DatabaseSWEA interpreted feedback: {interpretation.get('explanation', 'No explanation provided')}")
                return interpretation
            except json.JSONDecodeError:
                logger.warning(f"DatabaseSWEA could not parse LLM response as JSON: {response}")
                # Fallback: extract attributes from response text
                return self._extract_attributes_from_text(response, original_attributes)
                
        except Exception as e:
            logger.error(f"DatabaseSWEA feedback interpretation failed: {e}")
            # Fallback: return original attributes with error note
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "constraints": [],
                "modifications": [f"Could not interpret feedback: {str(e)}"],
                "explanation": "Using original attributes due to feedback interpretation error"
            }

    def _extract_attributes_from_text(self, response_text: str, original_attributes: List[str]) -> Dict[str, Any]:
        """Fallback method to extract attributes from LLM text response when JSON parsing fails"""
        # Simple text parsing fallback
        attributes = original_attributes.copy()
        modifications = []
        
        # Look for common patterns in the response
        lines = response_text.lower().split('\n')
        for line in lines:
            if 'add' in line and ('field' in line or 'column' in line or 'attribute' in line):
                modifications.append(f"Suggested addition from text: {line.strip()}")
            elif 'remove' in line and ('field' in line or 'column' in line or 'attribute' in line):
                modifications.append(f"Suggested removal from text: {line.strip()}")
        
        return {
            "attributes": attributes,
            "additional_requirements": [],
            "constraints": [],
            "modifications": modifications,
            "explanation": "Extracted information from text response (JSON parsing failed)"
        }

    def _apply_database_improvements(self, interpretation: Dict[str, Any], entity: str, db_file: str) -> Dict[str, Any]:
        """Apply the interpreted improvements to the database setup"""
        try:
            attributes = interpretation.get("attributes", [])
            additional_requirements = interpretation.get("additional_requirements", [])
            constraints = interpretation.get("constraints", [])
            modifications = interpretation.get("modifications", [])
            
            # Map Python types → SQLite
            type_map = {"str": "TEXT", "int": "INTEGER", "float": "REAL", "date": "TEXT", "bool": "INTEGER"}

            # Build column definitions - always start with ID column
            columns_sql: List[str] = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

            for attr in attributes:
                if ":" in attr:
                    name, typ = [p.strip() for p in attr.split(":", 1)]
                else:
                    name, typ = attr.strip(), "str"
                sql_type = type_map.get(typ.replace("Optional[", "").replace("]", ""), "TEXT")
                columns_sql.append(f"{name} {sql_type}")

            columns_sql_str = ", ".join(columns_sql)
            table_name = entity.lower() + "s"  # simple pluralisation

            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # Drop and recreate table to apply all changes
                # In production, this would use ALTER TABLE for data preservation
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute(f"CREATE TABLE {table_name} ({columns_sql_str})")
                
                # Apply additional constraints if specified
                for constraint in constraints:
                    try:
                        cursor.execute(constraint)
                        logger.info(f"Applied database constraint: {constraint}")
                    except Exception as e:
                        logger.warning(f"Could not apply constraint '{constraint}': {e}")
                
                conn.commit()

            result = {
                "database_path": db_file,
                "table": table_name,
                "columns": columns_sql,
                "managed_system": True,
                "improvements_applied": {
                    "attributes": attributes,
                    "additional_requirements": additional_requirements,
                    "constraints": constraints,
                    "modifications": modifications,
                    "explanation": interpretation.get("explanation", "No explanation provided")
                }
            }
            
            logger.info(f"DatabaseSWEA applied improvements based on feedback: {interpretation.get('explanation', 'No explanation')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply database improvements: {e}")
            raise

    # ------------------------------------------------------------------
    def _setup_database(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create SQLite database and a basic table for the entity with feedback-aware improvements."""
        entity = payload.get("entity", "Student")
        attributes: List[str] = payload.get("attributes", [])
        
        # Extract feedback information from payload
        techlead_feedback = payload.get("techlead_feedback", [])
        previous_errors = payload.get("previous_errors", [])
        expected_output = payload.get("expected_output", "")
        
        # Combine all feedback sources
        all_feedback = []
        if techlead_feedback:
            all_feedback.extend(techlead_feedback if isinstance(techlead_feedback, list) else [techlead_feedback])
        if previous_errors:
            all_feedback.extend(previous_errors if isinstance(previous_errors, list) else [previous_errors])
        if expected_output:
            all_feedback.append(f"Expected output: {expected_output}")

        # Use managed system database path
        managed_system_path = self.managed_system_manager.managed_system_path
        db_file = payload.get(
            "database_path", str(managed_system_path / "app" / "database" / "academic.db")
        )
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # Interpret feedback generically using LLM
        interpretation = self._interpret_feedback_for_database_setup(all_feedback, entity, attributes)
        
        # Apply the interpreted improvements
        result = self._apply_database_improvements(interpretation, entity, db_file)

        # Ensure managed system structure is updated
        self.managed_system_manager.ensure_managed_system_structure()

        logger.info(f"Managed system database created/updated at {db_file} with feedback-aware improvements")
        return self.create_success_response("setup_database", result)
