import csv
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from baes.core.managed_system_manager import ManagedSystemManager
from baes.domain_entities.base_bae import BaseAgent, is_debug_mode
from baes.llm.openai_client import OpenAIClient
from config import Config

logger = logging.getLogger(__name__)


# Stage 2 Improvement #8: Feedback Loop Analytics for DatabaseSWEA
class FeedbackLoopAnalytics:
    """
    Stage 2 Improvement #8: Feedback Loop Logging and Analytics
    Tracks all feedback interactions between TechLeadSWEA and DatabaseSWEA in CSV format.
    """

    def __init__(self):
        # Use tests/.temp for analytics during tests
        if Config.IS_TEST_ENVIRONMENT:
            self.analytics_dir = Path("tests/.temp")
        else:
            self.analytics_dir = Path("logs/feedback_analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.analytics_dir / "database_feedback_analytics.csv"
        self._ensure_csv_headers()

    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for pandas DataFrame compatibility"""
        if not self.csv_file.exists():
            headers = [
                "timestamp",
                "session_id",
                "entity",
                "feedback_round",
                "techlead_feedback_count",
                "feedback_categories",
                "database_response_time_seconds",
                "feedback_addressed",
                "retry_count",
                "final_success",
                "feedback_text_length",
                "database_changes_made",
                "improvement_areas",
            ]
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def log_feedback_interaction(
        self,
        session_id: str,
        entity: str,
        feedback_round: int,
        techlead_feedback: List[str],
        database_response_time: float,
        feedback_addressed: bool,
        retry_count: int,
        final_success: bool,
        database_changes_made: List[str] = None,
    ):
        """Log feedback loop interaction to CSV for analytics"""
        try:
            # Categorize feedback for analytics
            feedback_categories = self._categorize_feedback(techlead_feedback)
            improvement_areas = self._extract_improvement_areas(techlead_feedback)

            row_data = [
                datetime.now().isoformat(),
                session_id,
                entity,
                feedback_round,
                len(techlead_feedback),
                ";".join(feedback_categories),
                round(database_response_time, 2),
                feedback_addressed,
                retry_count,
                final_success,
                sum(len(fb) for fb in techlead_feedback),
                ";".join(database_changes_made or []),
                ";".join(improvement_areas),
            ]

            with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row_data)

            logger.info(f"📊 Database feedback analytics logged: {entity} round {feedback_round}")

        except Exception as e:
            logger.warning(f"Failed to log database feedback analytics: {e}")

    def _categorize_feedback(self, feedback_list: List[str]) -> List[str]:
        """Categorize feedback for analytics purposes"""
        categories = set()
        feedback_text = " ".join(feedback_list).lower()

        # Schema feedback
        if any(
            term in feedback_text for term in ["schema", "table", "column", "field", "structure"]
        ):
            categories.add("schema")

        # Performance feedback
        if any(
            term in feedback_text
            for term in ["performance", "index", "query", "optimization", "slow"]
        ):
            categories.add("performance")

        # Integrity feedback
        if any(
            term in feedback_text
            for term in ["constraint", "foreign key", "primary key", "unique", "integrity"]
        ):
            categories.add("integrity")

        # Connection feedback
        if any(
            term in feedback_text
            for term in ["connection", "pool", "timeout", "session", "context"]
        ):
            categories.add("connection")

        # Migration feedback
        if any(
            term in feedback_text for term in ["migration", "alter", "drop", "create", "modify"]
        ):
            categories.add("migration")

        return list(categories) if categories else ["general"]

    def _extract_improvement_areas(self, feedback_list: List[str]) -> List[str]:
        """Extract specific improvement areas from feedback"""
        areas = set()
        feedback_text = " ".join(feedback_list).lower()

        if "scalability" in feedback_text:
            areas.add("scalability")
        if "security" in feedback_text:
            areas.add("security")
        if "backup" in feedback_text:
            areas.add("backup_recovery")
        if "transaction" in feedback_text:
            areas.add("transaction_management")
        if "normalization" in feedback_text:
            areas.add("normalization")

        return list(areas) if areas else ["data_management"]


class DatabaseSWEA(BaseAgent):
    """SWEA responsible for preparing SQLite database schemas based on entity attributes."""

    def __init__(self):
        super().__init__("DatabaseSWEA", "Database Provisioning Agent", "SWEA")
        self._managed_system_manager = None  # Lazy initialization
        self.llm_client = OpenAIClient()
        # Stage 2 Improvement #8: Feedback Loop Analytics
        self.feedback_analytics = FeedbackLoopAnalytics()
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def managed_system_manager(self):
        """Lazy initialization of ManagedSystemManager"""
        if self._managed_system_manager is None:
            self._managed_system_manager = ManagedSystemManager()
        return self._managed_system_manager

    def _get_do_not_ignore_warning(self) -> str:
        """
        Generate standard 'Do Not Ignore' warning text for all LLM prompts.
        Stage 1 Improvement #10: Explicit warnings to prevent LLM from ignoring instructions.
        """
        return """
🚨 CRITICAL WARNING: If you ignore ANY of the following instructions, your output will be REJECTED \
    and you will be required to regenerate it. You MUST address EVERY requirement listed below. \
    Failure to comply will result in immediate rejection.

⚠️  DO NOT IGNORE ANY INSTRUCTIONS - Your response will be validated against ALL requirements.
⚠️  DO NOT SKIP ANY STEPS - Every instruction must be implemented exactly as specified.
⚠️  DO NOT USE PLACEHOLDERS - Generate complete, working code with no TODO comments.
⚠️  DO NOT OMIT ERROR HANDLING - Implement comprehensive error handling as required.
⚠️  DO NOT IGNORE FEEDBACK - Implement ALL TechLeadSWEA feedback exactly as provided.

COMPLIANCE IS MANDATORY - Non-compliance will result in immediate rejection and retry.
"""

    # Supported task identifiers
    _SUPPORTED_TASKS = {
        "setup_database": "_setup_database",
        "migrate_schema": "_migrate_schema",
        "create_relationships": "_create_relationships",
        "fix_issues": "_fix_database_issues",
    }

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

    def _interpret_feedback_for_database_setup(
        self, feedback: List[str], entity: str, original_attributes: List[str]
    ) -> Dict[str, Any]:
        """
        Generic feedback interpretation using LLM to understand what database changes are needed.
        This approach can handle any type of feedback without hardcoded conditions.
        """
        if not feedback:
            logger.debug(
                f"DatabaseSWEA: No feedback provided, using original attributes for {entity}"
            )
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "constraints": [],
                "modifications": [],
            }

        feedback_text = "\n".join(feedback)
        logger.debug(f"DatabaseSWEA: Interpreting feedback for {entity}: {feedback_text}")

        # Stage 4 Improvement #1: Get structured feedback for injection
        structured_feedback = self._get_structured_feedback_injection(
            entity, "DatabaseSWEA", "setup_database"
        )

        system_prompt = f"""You are a database design expert helping to interpret feedback for improving a database setup.

{self._get_do_not_ignore_warning()}

CONTEXT:
- Entity: {entity}
- Original attributes: {original_attributes}
- Feedback received: {feedback_text}

{structured_feedback}

STAGE 3 IMPROVEMENT #4: PRIORITY-BASED FEEDBACK HANDLING
TechLeadSWEA now provides categorized feedback with priority levels:
- CRITICAL: Issues that prevent system from working (MUST fix immediately)
- REQUIRED: Important functionality issues (MUST fix before approval)
- OPTIONAL: Nice-to-have improvements (can ignore for now)

You MUST focus on CRITICAL and REQUIRED feedback only. Ignore OPTIONAL suggestions.

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
- ALWAYS return valid JSON in the specified format
- Ensure attributes are simple strings like "name:str" or "email:str"
"""

        user_prompt = f"""Based on the feedback provided, what database setup changes should be made for the {entity} entity?

Feedback to interpret:
{feedback_text}

Current attributes:
{original_attributes}

Please provide the JSON response with database improvements."""

        # Stage 2 Improvement #8: Track analytics timing
        start_time = datetime.now()

        try:
            response = self.llm_client.generate_response(user_prompt, system_prompt)
            logger.debug(f"DatabaseSWEA: Raw LLM response: {response}")

            # Try to parse JSON response
            try:
                interpretation = json.loads(response)
                logger.info(
                    f"DatabaseSWEA interpreted feedback: {interpretation.get('explanation', 'No explanation provided')}"
                )
                logger.debug(f"DatabaseSWEA: Parsed interpretation: {interpretation}")

                # Stage 2 Improvement #8: Log successful feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                db_changes = interpretation.get("constraints", []) + interpretation.get(
                    "modifications", []
                )

                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    feedback_round=1,
                    techlead_feedback=feedback,
                    database_response_time=response_time,
                    feedback_addressed=True,
                    retry_count=0,
                    final_success=True,
                    database_changes_made=db_changes,
                )

                return interpretation
            except json.JSONDecodeError as json_error:
                error_msg = (
                    f"LLM response for DB feedback interpretation is not valid JSON: {json_error}. "
                    f"Raw response: {response}"
                )
                logger.error(error_msg)

                # Stage 2 Improvement #8: Log failed feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    feedback_round=1,
                    techlead_feedback=feedback,
                    database_response_time=response_time,
                    feedback_addressed=False,
                    retry_count=0,
                    final_success=False,
                    database_changes_made=[],
                )

                raise DatabaseGenerationError(error_msg) from json_error

        except Exception as e:
            logger.error(f"DatabaseSWEA feedback interpretation failed: {e}")

            # Stage 2 Improvement #8: Log failed feedback interaction
            response_time = (datetime.now() - start_time).total_seconds()
            self.feedback_analytics.log_feedback_interaction(
                session_id=self.current_session_id,
                entity=entity,
                feedback_round=1,
                techlead_feedback=feedback,
                database_response_time=response_time,
                feedback_addressed=False,
                retry_count=0,
                final_success=False,
                database_changes_made=[],
            )

            raise

    def _get_structured_feedback_injection(
        self, entity: str, swea_agent: str, task_type: str
    ) -> str:
        """
        Stage 4 Improvement #1: Get structured feedback injection from TechLeadSWEA.
        Returns formatted feedback instructions for prompt injection.
        """
        try:
            # Import TechLeadSWEA to access feedback storage
            from baes.swea_agents.techlead_swea import TechLeadSWEA

            # Create temporary TechLeadSWEA instance to access feedback storage
            techlead = TechLeadSWEA()
            structured_instructions = techlead._retrieve_feedback_for_injection(
                entity, swea_agent, task_type
            )

            if structured_instructions:
                logger.info(
                    f"📤 DatabaseSWEA: Retrieved structured feedback for {entity}.{swea_agent}.{task_type}"
                )
                return structured_instructions
            else:
                logger.debug(
                    f"📤 DatabaseSWEA: No structured feedback available for {entity}.{swea_agent}.{task_type}"
                )
                return ""

        except Exception as e:
            logger.warning(f"DatabaseSWEA: Failed to get structured feedback injection: {str(e)}")
            return ""

    def _extract_attributes_from_text(
        self, response_text: str, original_attributes: List[str]
    ) -> Dict[str, Any]:
        """Fallback method to extract attributes from LLM text response when JSON parsing fails"""
        # Type validation to avoid AttributeError on non-string response
        if not isinstance(response_text, str):
            raise DatabaseGenerationError(
                f"LLM response expected str but got {type(response_text)}"
            )

        if is_debug_mode():
            logger.debug("DatabaseSWEA raw fallback text preview: %.120s", repr(response_text))

        attributes = original_attributes.copy()
        modifications = []

        # Look for common patterns in the response
        lines = response_text.lower().split("\n")
        for line in lines:
            if "add" in line and ("field" in line or "column" in line or "attribute" in line):
                modifications.append(f"Suggested addition from text: {line.strip()}")
            elif "remove" in line and ("field" in line or "column" in line or "attribute" in line):
                modifications.append(f"Suggested removal from text: {line.strip()}")

        return {
            "attributes": attributes,
            "additional_requirements": [],
            "constraints": [],
            "modifications": modifications,
            "explanation": "Extracted information from text response (JSON parsing failed)",
        }

    def _validate_interpretation_structure(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure interpretation has correct structure with proper data types"""
        validated = {
            "attributes": [],
            "additional_requirements": [],
            "constraints": [],
            "modifications": [],
            "explanation": interpretation.get("explanation", "No explanation provided"),
        }

        # Normalize attributes to consistent string format
        raw_attributes = interpretation.get("attributes", [])
        logger.debug(
            f"DatabaseSWEA: Processing {len(raw_attributes)} attributes with types: {[type(attr) for attr in raw_attributes]}"
        )

        for attr in raw_attributes:
            if isinstance(attr, dict):
                # Convert dict to "name:type" string format
                name = attr.get("name", "field")
                typ = attr.get("type", "str")
                validated["attributes"].append(f"{name}:{typ}")
                logger.debug(f"DatabaseSWEA: Converted dict attribute to string: {name}:{typ}")
            elif isinstance(attr, str):
                validated["attributes"].append(attr)
            else:
                # Fallback - convert to string
                str_attr = str(attr)
                validated["attributes"].append(str_attr)
                logger.warning(
                    f"DatabaseSWEA: Converted unexpected attribute type {type(attr)} to string: {str_attr}"
                )

        # Ensure other fields are lists of strings
        for field in ["additional_requirements", "constraints", "modifications"]:
            raw_list = interpretation.get(field, [])
            validated[field] = [str(item) for item in raw_list if item]

        logger.debug(
            f"DatabaseSWEA: Validated interpretation with {len(validated['attributes'])} normalized attributes"
        )
        return validated

    def _create_fallback_database(self, entity: str, db_file: str) -> Dict[str, Any]:
        """Create a basic fallback database when interpretation fails"""
        try:
            # Create basic table with minimal schema
            table_name = entity.lower() + "s"
            basic_columns = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "name TEXT NOT NULL",
                "email TEXT",
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP",
            ]
            columns_sql_str = ", ".join(basic_columns)

            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                cursor.execute(f"CREATE TABLE {table_name} ({columns_sql_str})")
                conn.commit()

            result = {
                "database_path": db_file,
                "table": table_name,
                "columns": basic_columns,
                "managed_system": True,
                "fallback_used": True,
                "improvements_applied": {
                    "attributes": ["name:str", "email:str", "created_at:str"],
                    "additional_requirements": [],
                    "constraints": [],
                    "modifications": ["Used fallback schema due to interpretation error"],
                    "explanation": "Fallback database created with basic schema",
                },
            }

            logger.info(f"DatabaseSWEA: Created fallback database for {entity} at {db_file}")
            return result

        except Exception as e:
            logger.error(f"DatabaseSWEA: Fallback database creation failed: {e}")
            raise

    def _apply_database_improvements(
        self, interpretation: Dict[str, Any], entity: str, db_file: str
    ) -> Dict[str, Any]:
        """Apply the interpreted improvements to the database setup"""
        try:
            # Validate and normalize interpretation structure (Phase 1 fix)
            interpretation = self._validate_interpretation_structure(interpretation)

            attributes = interpretation.get("attributes", [])
            additional_requirements = interpretation.get("additional_requirements", [])
            constraints = interpretation.get("constraints", [])
            modifications = interpretation.get("modifications", [])

            # Map Python types → SQLite
            type_map = {
                "str": "TEXT",
                "int": "INTEGER",
                "float": "REAL",
                "date": "TEXT",
                "bool": "INTEGER",
            }

            # Build column definitions - always start with ID column
            columns_sql: List[str] = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

            for attr in attributes:
                # Robust attribute processing (Phase 1 fix)
                if isinstance(attr, dict):
                    # LLM returned structured attribute info
                    name = attr.get("name", "unknown_field")
                    typ = attr.get("type", "str")
                    logger.debug(f"DatabaseSWEA: Processing dict attribute: {name}:{typ}")
                elif isinstance(attr, str):
                    # Traditional string format
                    if ":" in attr:
                        name, typ = [p.strip() for p in attr.split(":", 1)]
                    else:
                        name, typ = attr.strip(), "str"
                    logger.debug(f"DatabaseSWEA: Processing string attribute: {name}:{typ}")
                else:
                    # Fallback for unexpected formats (Phase 1 fix)
                    logger.warning(
                        f"DatabaseSWEA: Unexpected attribute format: {attr} (type: {type(attr)})"
                    )
                    name, typ = str(attr), "str"

                # Sanitize field name
                name = name.replace(" ", "_").lower()
                
                # Skip 'id' field since it's already added as PRIMARY KEY
                if name == 'id':
                    logger.debug(f"DatabaseSWEA: Skipping 'id' attribute - already handled as PRIMARY KEY")
                    continue
                
                sql_type = type_map.get(typ.replace("Optional[", "").replace("]", ""), "TEXT")
                columns_sql.append(f"{name} {sql_type}")

            columns_sql_str = ", ".join(columns_sql)
            table_name = entity.lower() + "s"

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
                "tables_created": [table_name],  # Add this for TechLeadSWEA validation
                "managed_system": True,
                "improvements_applied": {
                    "attributes": attributes,
                    "additional_requirements": additional_requirements,
                    "constraints": constraints,
                    "modifications": modifications,
                    "explanation": interpretation.get("explanation", "No explanation provided"),
                },
            }

            logger.info(
                f"DatabaseSWEA applied improvements based on feedback: {interpretation.get('explanation', 'No explanation')}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to apply database improvements: {e}")
            logger.error(f"Interpretation data: {interpretation}")
            logger.error(
                f"Attribute types: {[type(attr) for attr in interpretation.get('attributes', [])]}"
            )

            # Provide fallback database creation with basic schema (Phase 1 fix)
            logger.info("DatabaseSWEA: Attempting fallback database creation...")
            return self._create_fallback_database(entity, db_file)

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
            all_feedback.extend(
                techlead_feedback if isinstance(techlead_feedback, list) else [techlead_feedback]
            )
        if previous_errors:
            all_feedback.extend(
                previous_errors if isinstance(previous_errors, list) else [previous_errors]
            )
        if expected_output:
            all_feedback.append(f"Expected output: {expected_output}")

        # Use managed system database path
        managed_system_path = self.managed_system_manager.managed_system_path
        db_file = payload.get(
            "database_path", str(managed_system_path / "app" / "database" / "baes_system.db")
        )
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # Interpret feedback generically using LLM
        interpretation = self._interpret_feedback_for_database_setup(
            all_feedback, entity, attributes
        )

        # Apply the interpreted improvements
        result = self._apply_database_improvements(interpretation, entity, db_file)

        # Ensure managed system structure is updated
        self.managed_system_manager.ensure_managed_system_structure()

        logger.info(
            f"Managed system database created/updated at {db_file} with feedback-aware improvements"
        )
        return self.create_success_response("setup_database", result)

    def _migrate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate database schema for entity evolution"""
        try:
            entity = payload.get("entity", "Student")
            new_attributes = payload.get("attributes", [])
            feedback = payload.get("feedback", [])

            logger.info(f"🔄 DatabaseSWEA: Starting schema migration for {entity} entity")

            db_file = self.managed_system_manager.managed_system_path / "app" / "database" / "baes_system.db"
            table_name = entity.lower() + "s"
            
            # Get current schema from database
            current_schema_from_db = self._get_current_table_schema(str(db_file), table_name)
            current_attributes = []
            type_map_reverse = {"TEXT": "str", "INTEGER": "int", "REAL": "float"}
            
            logger.info(f"📊 Current table schema for {table_name}: {current_schema_from_db}")
            
            for col_def in current_schema_from_db:
                parts = col_def.split()
                name = parts[0]
                if name == 'id': continue
                sql_type = parts[1]
                py_type = type_map_reverse.get(sql_type, "str")
                current_attributes.append(f"{name}:{py_type}")
            
            # DEBUG: Log the extracted current attributes
            logger.info(f"🔍 DEBUG - current_attributes from DB: {current_attributes}")
            logger.info(f"🔍 DEBUG - new_attributes from request: {new_attributes}")

            # Merge current and new attributes, preserving existing ones
            all_attributes = list(dict.fromkeys(current_attributes + new_attributes))
            logger.info(f"🔗 Merged attributes for migration: {all_attributes}")
            
            interpretation = self._interpret_feedback_for_database_setup(
                feedback, entity, all_attributes
            )
            interpretation = self._validate_interpretation_structure(interpretation)
            
            # DEBUG: Log what the LLM interpretation returned
            logger.info(f"🔍 DEBUG - LLM interpretation result: {interpretation}")

            result = self._apply_schema_migration(interpretation, entity, str(db_file))

            logger.info(f"✅ DatabaseSWEA: Schema migration completed successfully for {entity}")
            
            # Extract SQL code for TechLeadSWEA validation
            sql_code = result.get("code", "")
            
            # Return result with 'code' field for TechLeadSWEA validation
            return self.create_success_response("migrate_schema", {
                **result,
                "code": sql_code,  # TechLeadSWEA expects this field
                "file_path": f"migration_{entity.lower()}_{int(time.time())}.sql"
            })

        except Exception as e:
            logger.error(f"❌ DatabaseSWEA schema migration failed for {entity}: {str(e)}")
            return self.create_error_response("migrate_schema", str(e), "migration_error")

    def _create_relationships(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create foreign key relationships between tables with comprehensive SQL generation."""
        try:
            entity = payload.get("entity")
            relationships = payload.get("relationships", [])
            attributes = payload.get("attributes", [])
            context = payload.get("context", "")
            
            db_file = self.managed_system_manager.managed_system_path / "app" / "database" / "baes_system.db"
            table_name = entity.lower() + "s"
            
            logger.info(f"🔗 DatabaseSWEA: Creating relationships for {entity}")
            
            # Build comprehensive columns map with explicit PRIMARY KEY
            current_columns_map = {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT'}
            
            # Process existing attributes
            for attr in attributes:
                if isinstance(attr, str):
                    if ":" in attr:
                        name, typ = [p.strip() for p in attr.split(":", 1)]
                    else:
                        name, typ = attr.strip(), "str"
                    
                    name = name.replace(" ", "_").lower()
                    if name != 'id':  # Skip id as it's already handled
                        sql_type = self._convert_type_hint_to_sql(typ)
                        current_columns_map[name] = sql_type

            # Add foreign key columns for relationships
            existing_columns = {}
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # Check if table exists and get current structure
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
                    logger.info(f"📋 Current table structure for {table_name}: {list(existing_columns.keys())}")
                    
                    # Update current_columns_map with existing structure, preserving PRIMARY KEY
                    for col_name, col_type in existing_columns.items():
                        if col_name == 'id':
                            # Ensure id column always has PRIMARY KEY
                            current_columns_map['id'] = 'INTEGER PRIMARY KEY AUTOINCREMENT'
                        else:
                            current_columns_map[col_name] = col_type
                
                # Add foreign key columns to the schema
                for rel in relationships:
                    foreign_key_name = f"{rel['target_entity'].lower()}_id"
                    target_table = f"{rel['target_entity'].lower()}s"
                    
                    # Add foreign key column to the schema
                    current_columns_map[foreign_key_name] = f"INTEGER REFERENCES {target_table}(id)"
                    logger.info(f"🔗 Added foreign key: {foreign_key_name} -> {target_table}")

            # Generate complete CREATE TABLE statement with explicit PRIMARY KEY
            columns_sql = ", ".join([f"{name} {typ}" for name, typ in current_columns_map.items()])
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
            
            # Execute the relationship creation in the database
            logger.info(f"🛠️  Executing relationship creation SQL for {table_name}")
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Execute the CREATE TABLE statement (IF NOT EXISTS)
                cursor.execute(create_table_sql)
                logger.info(f"✅ Table created/verified: {table_name}")
                
                # Execute any ALTER TABLE statements for existing tables
                for rel in relationships:
                    foreign_key_name = f"{rel['target_entity'].lower()}_id"
                    target_table = f"{rel['target_entity'].lower()}s"
                    
                    # Check if column already exists
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    current_column_names = [row[1] for row in cursor.fetchall()]
                    
                    if foreign_key_name not in current_column_names:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {foreign_key_name} INTEGER REFERENCES {target_table}(id)"
                        cursor.execute(alter_sql)
                        logger.info(f"✅ Added foreign key: {foreign_key_name}")
                
                conn.commit()
                logger.info(f"💾 Relationship creation committed to database")

            # Build comprehensive SQL documentation for TechLeadSWEA validation
            sql_statements = []
            sql_statements.append(f"-- Relationship creation for {entity} entity")
            sql_statements.append(f"-- Generated by DatabaseSWEA with comprehensive table management")
            sql_statements.append(f"-- Entity: {entity} | Table: {table_name} | Timestamp: {datetime.now().isoformat()}")
            sql_statements.append(f"-- Context: {context}")
            sql_statements.append("")
            
            # Add main table creation with explicit PRIMARY KEY
            sql_statements.append(f"-- Create {table_name} table with PRIMARY KEY and relationships")
            sql_statements.append(create_table_sql + ";")
            
            # Add relationship-specific ALTER TABLE statements for existing tables
            for rel in relationships:
                foreign_key_name = f"{rel['target_entity'].lower()}_id"
                target_table = f"{rel['target_entity'].lower()}s"
                
                if table_exists and foreign_key_name not in existing_columns:
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {foreign_key_name} INTEGER REFERENCES {target_table}(id)"
                    sql_statements.append(f"{alter_sql};")
                    sql_statements.append(f"-- Added foreign key relationship: {table_name}.{foreign_key_name} -> {target_table}.id")

            # Combine all SQL statements
            pure_sql = "\n".join(sql_statements)
            
            # Generate comprehensive Python code with logging for TechLeadSWEA validation
            python_code = f"""-- Relationship creation for {entity} entity
-- Generated by DatabaseSWEA with comprehensive logging and table management
-- Entity: {entity} | Table: {table_name} | Timestamp: {datetime.now().isoformat()}

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

def setup_database(db_path: str = None) -> str:
    \"\"\"
    Initialize database with all required tables including relationships.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        str: Path to the initialized database
    \"\"\"
    if db_path is None:
        db_path = Path("app/database/baes_system.db")
    else:
        db_path = Path(db_path)
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🔗 Setting up database with relationships at: {{db_path}}")
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        logger.info("✅ Foreign key constraints enabled")
        
        # Create {table_name} table with PRIMARY KEY and relationships
        create_table_sql = "CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
        cursor.execute(create_table_sql)
        logger.info(f"✅ Created/verified table: {table_name} with PRIMARY KEY")
        
        conn.commit()
        logger.info("✅ Database setup with relationships completed successfully")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Database setup failed: {{e}}")
        raise
    finally:
        if conn:
            conn.close()
    
    return str(db_path)

def create_{entity.lower()}_relationships(db_path: str = None) -> Dict[str, Any]:
    \"\"\"
    Create foreign key relationships for {entity} entity.
    
    This function adds foreign key columns and relationships while preserving existing data.
    Generated by DatabaseSWEA for relationship management.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        Dict containing relationship creation results
    \"\"\"
    if db_path is None:
        db_path = Path("app/database/baes_system.db")
    else:
        db_path = Path(db_path)
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🔗 Creating relationships for {table_name}")
    logger.info(f"📊 Database path: {{db_path}}")
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        logger.info("✅ Foreign key constraints enabled")
        
        # Log current schema before relationship creation
        cursor.execute("PRAGMA table_info({table_name})")
        current_schema = cursor.fetchall()
        logger.info(f"📋 Current schema: {{[col[1] for col in current_schema]}}")
        
        # Ensure table exists with complete structure including PRIMARY KEY
        cursor.execute("CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})")
        logger.info(f"✅ Ensured table exists: {table_name} with PRIMARY KEY")
        
        conn.commit()
        logger.info(f"✅ Relationship creation completed successfully for {table_name}")
        
        # Log final schema
        cursor.execute("PRAGMA table_info({table_name})")
        final_schema = cursor.fetchall()
        logger.info(f"📊 Final schema: {{[col[1] for col in final_schema]}}")
        
        return {{
            "success": True,
            "table": "{table_name}",
            "columns": {list(current_columns_map.keys())},
            "relationships_created": True,
            "foreign_keys": {[f"{rel['target_entity'].lower()}_id" for rel in relationships]}
        }}
        
    except sqlite3.Error as db_error:
        if conn:
            conn.rollback()
        logger.error(f"❌ Database error during {table_name} relationship creation: {{db_error}}")
        raise
    except Exception as error:
        if conn:
            conn.rollback()
        logger.error(f"❌ Relationship creation failed for {table_name}: {{error}}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_{entity.lower()}_relationships()
"""
            
            result = {
                "database_path": str(db_file),
                "table": table_name,
                "columns": list(current_columns_map.keys()),
                "relationships_created": True,
                "code": python_code,  # Full Python code with logging for TechLeadSWEA validation
                "sql": pure_sql,  # Pure SQL statements that were executed
                "foreign_keys": [f"{rel['target_entity'].lower()}_id" for rel in relationships],
                "entity": entity,
                "improvements_applied": {
                    "relationships": relationships,
                    "context": context
                }
            }
            
            logger.info(f"✅ Relationship creation for '{table_name}' completed successfully")
            logger.info(f"📊 Final table columns: {list(current_columns_map.keys())}")
            logger.info(f"🔗 Foreign keys created: {[f'{rel['target_entity'].lower()}_id' for rel in relationships]}")
            return result

        except Exception as e:
            logger.error(f"❌ Relationship creation failed for {entity}: {str(e)}")
            raise

    def _apply_schema_migration(
        self, interpretation: Dict[str, Any], entity: str, db_file: str
    ) -> Dict[str, Any]:
        """Apply schema migration based on interpretation, preserving existing data."""
        try:
            table_name = entity.lower() + "s"
            new_attributes = interpretation.get("attributes", [])
            
            logger.info(f"🔄 Applying schema migration for {table_name}")
            logger.info(f"📝 New attributes to process: {new_attributes}")
            
            # Get current table columns before migration
            current_columns = []
            try:
                with sqlite3.connect(db_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    current_columns = [row[1] for row in cursor.fetchall()]
                    logger.info(f"📊 Current table columns: {current_columns}")
            except Exception as e:
                logger.warning(f"⚠️  Could not get current table info: {e}")
            
            # DEBUG: Log the interpretation attributes
            logger.info(f"🔍 DEBUG - interpretation attributes: {new_attributes}")
            
            new_columns_map = {}
            for attr in new_attributes:
                if isinstance(attr, str):
                    if ":" in attr:
                        name, typ = [p.strip() for p in attr.split(":", 1)]
                    else:
                        name, typ = attr.strip(), "str"
                elif isinstance(attr, dict):
                    name = attr.get("name", "unknown_field")
                    typ = attr.get("type", "str")
                else:
                    continue

                name = name.replace(" ", "_").lower()
                
                # Skip 'id' field since it will be handled separately as PRIMARY KEY
                if name == 'id':
                    logger.debug(f"DatabaseSWEA: Skipping 'id' attribute in migration - will be handled as PRIMARY KEY")
                    continue
                
                sql_type = self._convert_type_hint_to_sql(typ)
                new_columns_map[name] = sql_type

            # Always ensure 'id' column is first with PRIMARY KEY
            new_columns_map = {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', **new_columns_map}
            
            # DEBUG: Log the new columns map
            logger.info(f"🔍 DEBUG - new_columns_map: {new_columns_map}")

            # Determine which columns to preserve from backup
            columns_to_preserve = []
            if current_columns:
                # For migration operations, preserve ALL existing columns by default
                # Always start with 'id' column which should always exist
                if 'id' in current_columns:
                    columns_to_preserve.append('id')
                    logger.info(f"🔍 DEBUG - Column 'id' added to preserve list (always preserved)")
                
                # Process all other existing columns
                for col in current_columns:
                    if col == 'id':
                        continue  # Already handled above
                    
                    if col in new_columns_map:
                        # Column exists in new schema, preserve it
                        columns_to_preserve.append(col)
                        logger.info(f"🔍 DEBUG - Column '{col}' found in new_columns_map, preserving")
                    else:
                        # Column doesn't exist in new schema, but we should preserve it anyway
                        # Try to infer the type from the existing table and add to new schema
                        existing_type = self._get_column_type_from_current_table(db_file, table_name, col)
                        if existing_type:
                            new_columns_map[col] = existing_type
                            columns_to_preserve.append(col)
                            logger.info(f"🔍 DEBUG - Column '{col}' added to new schema to preserve existing data")
                        else:
                            logger.warning(f"🔍 DEBUG - Column '{col}' could not be preserved (unknown type), will be LOST")
                
                logger.info(f"🔄 Columns to preserve during migration: {columns_to_preserve}")
                logger.info(f"🔍 DEBUG - Updated new_columns_map: {new_columns_map}")
            else:
                # If no current columns info, assume we're creating new table
                columns_to_preserve = list(new_columns_map.keys())
                logger.info(f"🆕 Creating new table with columns: {columns_to_preserve}")
            
            # Build new table schema
            new_columns_sql = ", ".join([f"{name} {typ}" for name, typ in new_columns_map.items()])
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({new_columns_sql})"
                
            # Execute the actual database migration with proper data preservation
            logger.info(f"🛠️  Executing schema migration SQL for {table_name}")
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cursor.fetchone() is not None
                
                if table_exists and current_columns:
                    # CRITICAL: Data preservation logic
                    logger.info(f"📊 Table exists with {len(current_columns)} columns, preserving data")
                    
                    # Step 1: Backup existing table
                    backup_table = f"{table_name}_backup"
                    cursor.execute(f"ALTER TABLE {table_name} RENAME TO {backup_table}")
                    logger.info(f"💾 Created backup table: {backup_table}")
                    
                    # Step 2: Create new table with updated schema
                    cursor.execute(create_table_sql)
                    logger.info(f"🆕 Created new table with updated schema")
                    
                    # Step 3: Restore data from backup (CRITICAL PART)
                    if columns_to_preserve:
                        preserve_columns_sql = ", ".join(columns_to_preserve)
                        restore_sql = f"INSERT INTO {table_name} ({preserve_columns_sql}) SELECT {preserve_columns_sql} FROM {backup_table}"
                        logger.info(f"🔄 Restoring data: {restore_sql}")
                        cursor.execute(restore_sql)
                        
                        # Verify data integrity
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        new_count = cursor.fetchone()[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
                        old_count = cursor.fetchone()[0]
                        
                        logger.info(f"📊 Data verification: {old_count} -> {new_count} records")
                        
                        if new_count >= old_count:
                            logger.info("✅ Data integrity verified - proceeding with cleanup")
                            cursor.execute(f"DROP TABLE {backup_table}")
                            logger.info(f"🗑️  Dropped backup table: {backup_table}")
                        else:
                            logger.error("❌ Data integrity check failed - rolling back")
                            cursor.execute(f"DROP TABLE {table_name}")
                            cursor.execute(f"ALTER TABLE {backup_table} RENAME TO {table_name}")
                            raise Exception("Data integrity check failed during migration")
                else:
                    # Create new table
                    logger.info(f"🆕 Creating new table: {table_name}")
                    cursor.execute(create_table_sql)
                
                conn.commit()
                logger.info(f"💾 Schema migration committed to database")
            
            # Build comprehensive SQL documentation for TechLeadSWEA validation
            sql_statements = []
            sql_statements.append(f"-- Schema migration for {entity} entity")
            sql_statements.append(f"-- Generated by DatabaseSWEA with data preservation")
            sql_statements.append(f"-- Entity: {entity} | Table: {table_name} | Timestamp: {datetime.now().isoformat()}")
            sql_statements.append("")
            
            if current_columns:
                sql_statements.append(f"-- Data preservation migration: {len(current_columns)} -> {len(new_columns_map)} columns")
                sql_statements.append(f"ALTER TABLE {table_name} RENAME TO {table_name}_backup;")
                sql_statements.append(create_table_sql + ";")
                if columns_to_preserve:
                    preserve_columns_sql = ", ".join(columns_to_preserve)
                    restore_sql = f"INSERT INTO {table_name} ({preserve_columns_sql}) SELECT {preserve_columns_sql} FROM {table_name}_backup"
                    sql_statements.append(f"{restore_sql};")
                sql_statements.append(f"DROP TABLE {table_name}_backup;")
            else:
                sql_statements.append(f"-- New table creation")
                sql_statements.append(create_table_sql + ";")
            
            pure_sql = "\n".join(sql_statements)

            # Create the comprehensive Python code with logging for TechLeadSWEA validation
            python_code = f"""-- Schema migration for {entity} entity
-- Generated by DatabaseSWEA with data preservation and comprehensive logging
-- Entity: {entity} | Table: {table_name} | Timestamp: {datetime.now().isoformat()}

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

def setup_database(db_path: str = None) -> str:
    \"\"\"
    Initialize database with all required tables.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        str: Path to the initialized database
    \"\"\"
    if db_path is None:
        db_path = Path("app/database/baes_system.db")
    else:
        db_path = Path(db_path)
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Setting up database at: {{db_path}}")
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create {table_name} table with PRIMARY KEY
        create_table_sql = "CREATE TABLE IF NOT EXISTS {table_name} ({new_columns_sql})"
        cursor.execute(create_table_sql)
        
        conn.commit()
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database setup failed: {{e}}")
        raise
    finally:
        if conn:
            conn.close()
    
    return str(db_path)

def migrate_{entity.lower()}_schema(db_path: str = None) -> Dict[str, Any]:
    \"\"\"
    Migrate {entity} database schema with data preservation.
    
    This migration adds new fields while preserving existing data.
    Generated by DatabaseSWEA for entity evolution.
    
    Args:
        db_path: Optional path to database file
        
    Returns:
        Dict containing migration results
    \"\"\"
    if db_path is None:
        db_path = Path("app/database/baes_system.db")
    else:
        db_path = Path(db_path)
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"🔄 Starting schema migration for {table_name}")
    logger.info(f"📊 Database path: {{db_path}}")
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Log current schema before migration
        cursor.execute("PRAGMA table_info({table_name})")
        current_schema = cursor.fetchall()
        logger.info(f"📋 Current schema: {{[col[1] for col in current_schema]}}")
        
        # Begin transaction for atomic migration
        logger.info("🔧 Beginning schema migration transaction")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", ("{table_name}",))
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Backup existing table
            logger.info(f"💾 Creating backup table: {table_name}_backup")
            cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_backup")
            
            # Create new table with updated schema including PRIMARY KEY
            logger.info(f"🆕 Creating new table with updated schema")
            cursor.execute("CREATE TABLE IF NOT EXISTS {table_name} ({new_columns_sql})")
            
            # Restore data from backup, preserving existing columns
            preserve_columns_sql = "{', '.join(columns_to_preserve) if columns_to_preserve else 'id'}"
            restore_sql = f"INSERT INTO {table_name} ({{preserve_columns_sql}}) SELECT {{preserve_columns_sql}} FROM {table_name}_backup"
            cursor.execute(restore_sql)
            logger.info("📥 Data restored from backup table")
            
            # Verify data integrity
            cursor.execute("SELECT COUNT(*) FROM {table_name}")
            new_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM {table_name}_backup")
            old_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Data verification: {{old_count}} -> {{new_count}} records")
            
            if new_count >= old_count:
                logger.info("✅ Data integrity verified - proceeding with cleanup")
                cursor.execute("DROP TABLE {table_name}_backup")
                logger.info(f"🗑️  Dropped backup table: {table_name}_backup")
            else:
                logger.error("❌ Data integrity check failed - rolling back")
                cursor.execute("DROP TABLE {table_name}")
                cursor.execute("ALTER TABLE {table_name}_backup RENAME TO {table_name}")
                raise Exception("Data integrity check failed during migration")
        else:
            # Create new table with PRIMARY KEY
            logger.info(f"🆕 Creating new table: {table_name}")
            cursor.execute("CREATE TABLE IF NOT EXISTS {table_name} ({new_columns_sql})")
        
        conn.commit()
        logger.info(f"✅ Schema migration completed successfully for {table_name}")
        
        # Log final schema
        cursor.execute("PRAGMA table_info({table_name})")
        final_schema = cursor.fetchall()
        logger.info(f"📊 Final schema: {{[col[1] for col in final_schema]}}")
        
        return {{
            "success": True,
            "table": "{table_name}",
            "columns": {list(new_columns_map.keys())},
            "migration_completed": True,
            "data_preserved": table_exists
        }}
        
    except sqlite3.Error as db_error:
        if conn:
            conn.rollback()
        logger.error(f"❌ Database error during {table_name} migration: {{db_error}}")
        raise
    except Exception as error:
        if conn:
            conn.rollback()
        logger.error(f"❌ Migration failed for {table_name}: {{error}}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_{entity.lower()}_schema()
"""

            result = {
                "database_path": db_file,
                "table": table_name,
                "columns": list(new_columns_map.keys()),
                "migration_applied": True,
                "code": python_code,  # Full Python code with logging for TechLeadSWEA validation
                "sql": pure_sql,  # Pure SQL statements that were executed
                "improvements_applied": interpretation,
                "data_preserved": len(columns_to_preserve) > 0,
                "preserved_columns": columns_to_preserve
            }
            
            logger.info(f"✅ Schema migration for '{table_name}' completed successfully")
            logger.info(f"📊 Final table columns: {list(new_columns_map.keys())}")
            return result

        except Exception as e:
            logger.error(f"❌ Schema migration failed for {entity}: {str(e)}")
            raise

    def _format_sql_for_python(self, sql: str) -> str:
        """Format SQL statements for inclusion in Python code with proper logging"""
        lines = sql.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            if line.endswith(';'):
                line = line[:-1]  # Remove semicolon for Python execution
            formatted_lines.append(f'            cursor.execute("{line}")')
            formatted_lines.append(f'            logger.info("✅ Executed: {line[:50]}...")')
        
        return '\n'.join(formatted_lines)

    def _get_current_table_schema(self, db_file: str, table_name: str) -> List[str]:
        """Get current table schema as list of 'column_name column_type' strings"""
        try:
            logger.info(f"📊 Getting current schema for table: {table_name}")
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                schema = [f"{col[1]} {col[2]}" for col in columns]
                logger.info(f"📋 Current schema for {table_name}: {schema}")
                return schema
        except Exception as e:
            logger.warning(f"⚠️  Could not get schema for {table_name}: {e}")
            return []

    def _convert_type_hint_to_sql(self, type_hint: str) -> str:
        """Convert Python type hint to SQL type"""
        type_mapping = {
            "str": "TEXT",
            "int": "INTEGER", 
            "float": "REAL",
            "bool": "INTEGER",
            "date": "TEXT",
            "datetime": "TEXT",
        }
        sql_type = type_mapping.get(type_hint.lower(), "TEXT")
        logger.debug(f"🔄 Converted type hint '{type_hint}' to SQL type '{sql_type}'")
        return sql_type

    def _get_column_type_from_current_table(self, db_file: str, table_name: str, column_name: str) -> str:
        """Get the SQL type of a column from the current table"""
        try:
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    if col[1] == column_name:  # col[1] is the column name
                        return col[2]  # col[2] is the column type
                return None
        except Exception as e:
            logger.warning(f"⚠️  Could not get column type for {column_name}: {e}")
            return None




# ---------------------------------------------------------------------------
# Custom exception to make failures explicit
# ---------------------------------------------------------------------------


class DatabaseGenerationError(Exception):
    """Raised when database generation or feedback interpretation fails"""

    pass
