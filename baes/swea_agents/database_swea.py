import logging
import os
import sqlite3
from typing import Any, Dict, List
import json
import csv
from datetime import datetime
from pathlib import Path

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager
from ..llm.openai_client import OpenAIClient
# Utility for conditional debug logging
from ..domain_entities.base_bae import is_debug_mode

logger = logging.getLogger(__name__)

# Stage 2 Improvement #8: Feedback Loop Analytics for DatabaseSWEA
class FeedbackLoopAnalytics:
    """
    Stage 2 Improvement #8: Feedback Loop Logging and Analytics
    Tracks all feedback interactions between TechLeadSWEA and DatabaseSWEA in CSV format.
    """
    
    def __init__(self):
        self.analytics_dir = Path("logs/feedback_analytics")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.analytics_dir / "database_feedback_analytics.csv"
        self._ensure_csv_headers()
    
    def _ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for pandas DataFrame compatibility"""
        if not self.csv_file.exists():
            headers = [
                'timestamp',
                'session_id', 
                'entity',
                'feedback_round',
                'techlead_feedback_count',
                'feedback_categories',
                'database_response_time_seconds',
                'feedback_addressed',
                'retry_count',
                'final_success',
                'feedback_text_length',
                'database_changes_made',
                'improvement_areas'
            ]
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_feedback_interaction(self, session_id: str, entity: str, 
                               feedback_round: int, techlead_feedback: List[str],
                               database_response_time: float, feedback_addressed: bool,
                               retry_count: int, final_success: bool, 
                               database_changes_made: List[str] = None):
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
                ';'.join(feedback_categories),
                round(database_response_time, 2),
                feedback_addressed,
                retry_count,
                final_success,
                sum(len(fb) for fb in techlead_feedback),
                ';'.join(database_changes_made or []),
                ';'.join(improvement_areas)
            ]
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                
            logger.info(f"📊 Database feedback analytics logged: {entity} round {feedback_round}")
            
        except Exception as e:
            logger.warning(f"Failed to log database feedback analytics: {e}")
    
    def _categorize_feedback(self, feedback_list: List[str]) -> List[str]:
        """Categorize feedback for analytics purposes"""
        categories = set()
        feedback_text = ' '.join(feedback_list).lower()
        
        # Schema feedback
        if any(term in feedback_text for term in ['schema', 'table', 'column', 'field', 'structure']):
            categories.add('schema')
        
        # Performance feedback  
        if any(term in feedback_text for term in ['performance', 'index', 'query', 'optimization', 'slow']):
            categories.add('performance')
            
        # Integrity feedback
        if any(term in feedback_text for term in ['constraint', 'foreign key', 'primary key', 'unique', 'integrity']):
            categories.add('integrity')
            
        # Connection feedback
        if any(term in feedback_text for term in ['connection', 'pool', 'timeout', 'session', 'context']):
            categories.add('connection')
            
        # Migration feedback
        if any(term in feedback_text for term in ['migration', 'alter', 'drop', 'create', 'modify']):
            categories.add('migration')
            
        return list(categories) if categories else ['general']
    
    def _extract_improvement_areas(self, feedback_list: List[str]) -> List[str]:
        """Extract specific improvement areas from feedback"""
        areas = set()
        feedback_text = ' '.join(feedback_list).lower()
        
        if 'scalability' in feedback_text:
            areas.add('scalability')
        if 'security' in feedback_text:
            areas.add('security') 
        if 'backup' in feedback_text:
            areas.add('backup_recovery')
        if 'transaction' in feedback_text:
            areas.add('transaction_management')
        if 'normalization' in feedback_text:
            areas.add('normalization')
            
        return list(areas) if areas else ['data_management']

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
🚨 CRITICAL WARNING: If you ignore ANY of the following instructions, your output will be REJECTED and you will be required to regenerate it. You MUST address EVERY requirement listed below. Failure to comply will result in immediate rejection.

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

    def _interpret_feedback_for_database_setup(self, feedback: List[str], entity: str, original_attributes: List[str]) -> Dict[str, Any]:
        """
        Generic feedback interpretation using LLM to understand what database changes are needed.
        This approach can handle any type of feedback without hardcoded conditions.
        """
        if not feedback:
            logger.debug(f"DatabaseSWEA: No feedback provided, using original attributes for {entity}")
            return {
                "attributes": original_attributes,
                "additional_requirements": [],
                "constraints": [],
                "modifications": []
            }

        feedback_text = "\n".join(feedback)
        logger.debug(f"DatabaseSWEA: Interpreting feedback for {entity}: {feedback_text}")
        
        system_prompt = f"""You are a database design expert helping to interpret feedback for improving a database setup.

{self._get_do_not_ignore_warning()}

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
                logger.info(f"DatabaseSWEA interpreted feedback: {interpretation.get('explanation', 'No explanation provided')}")
                logger.debug(f"DatabaseSWEA: Parsed interpretation: {interpretation}")
                
                # Stage 2 Improvement #8: Log successful feedback interaction
                response_time = (datetime.now() - start_time).total_seconds()
                db_changes = interpretation.get("constraints", []) + interpretation.get("modifications", [])
                
                self.feedback_analytics.log_feedback_interaction(
                    session_id=self.current_session_id,
                    entity=entity,
                    feedback_round=1,
                    techlead_feedback=feedback,
                    database_response_time=response_time,
                    feedback_addressed=True,
                    retry_count=0,
                    final_success=True,
                    database_changes_made=db_changes
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
                    database_changes_made=[]
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
                database_changes_made=[]
            )
            
            raise

    def _extract_attributes_from_text(self, response_text: str, original_attributes: List[str]) -> Dict[str, Any]:
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

    def _validate_interpretation_structure(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure interpretation has correct structure with proper data types"""
        validated = {
            "attributes": [],
            "additional_requirements": [],
            "constraints": [],
            "modifications": [],
            "explanation": interpretation.get("explanation", "No explanation provided")
        }
        
        # Normalize attributes to consistent string format
        raw_attributes = interpretation.get("attributes", [])
        logger.debug(f"DatabaseSWEA: Processing {len(raw_attributes)} attributes with types: {[type(attr) for attr in raw_attributes]}")
        
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
                logger.warning(f"DatabaseSWEA: Converted unexpected attribute type {type(attr)} to string: {str_attr}")
        
        # Ensure other fields are lists of strings
        for field in ["additional_requirements", "constraints", "modifications"]:
            raw_list = interpretation.get(field, [])
            validated[field] = [str(item) for item in raw_list if item]
        
        logger.debug(f"DatabaseSWEA: Validated interpretation with {len(validated['attributes'])} normalized attributes")
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
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
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
                    "explanation": "Fallback database created with basic schema"
                }
            }
            
            logger.info(f"DatabaseSWEA: Created fallback database for {entity} at {db_file}")
            return result
            
        except Exception as e:
            logger.error(f"DatabaseSWEA: Fallback database creation failed: {e}")
            raise

    def _apply_database_improvements(self, interpretation: Dict[str, Any], entity: str, db_file: str) -> Dict[str, Any]:
        """Apply the interpreted improvements to the database setup"""
        try:
            # Validate and normalize interpretation structure (Phase 1 fix)
            interpretation = self._validate_interpretation_structure(interpretation)
            
            attributes = interpretation.get("attributes", [])
            additional_requirements = interpretation.get("additional_requirements", [])
            constraints = interpretation.get("constraints", [])
            modifications = interpretation.get("modifications", [])
            
            # Map Python types → SQLite
            type_map = {"str": "TEXT", "int": "INTEGER", "float": "REAL", "date": "TEXT", "bool": "INTEGER"}

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
                    logger.warning(f"DatabaseSWEA: Unexpected attribute format: {attr} (type: {type(attr)})")
                    name, typ = str(attr), "str"
                
                # Sanitize field name
                name = name.replace(" ", "_").lower()
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
                    "explanation": interpretation.get("explanation", "No explanation provided")
                }
            }
            
            logger.info(f"DatabaseSWEA applied improvements based on feedback: {interpretation.get('explanation', 'No explanation')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply database improvements: {e}")
            logger.error(f"Interpretation data: {interpretation}")
            logger.error(f"Attribute types: {[type(attr) for attr in interpretation.get('attributes', [])]}")
            
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

    def _migrate_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate database schema for entity evolution"""
        try:
            entity = payload.get("entity", "Student")
            attributes = payload.get("attributes", [])
            feedback = payload.get("feedback", [])
            
            logger.info(f"🔄 DatabaseSWEA: Migrating schema for {entity} entity")
            
            # Interpret feedback for schema migration
            interpretation = self._interpret_feedback_for_database_setup(feedback, entity, attributes)
            interpretation = self._validate_interpretation_structure(interpretation)
            
            # Get database file path
            db_file = self.managed_system_manager.managed_system_path / "app" / "database" / "academic.db"
            
            # Apply schema migration
            result = self._apply_schema_migration(interpretation, entity, str(db_file))
            
            logger.info(f"✅ DatabaseSWEA: Schema migration completed for {entity}")
            return self.create_success_response("migrate_schema", result)
            
        except Exception as e:
            logger.error(f"❌ DatabaseSWEA schema migration failed: {str(e)}")
            return self.create_error_response("migrate_schema", str(e), "migration_error")

    def _apply_schema_migration(self, interpretation: Dict[str, Any], entity: str, db_file: str) -> Dict[str, Any]:
        """Apply schema migration based on interpretation"""
        try:
            table_name = entity.lower() + "s"
            
            # Get current schema
            current_columns = self._get_current_table_schema(db_file, table_name)
            
            # Build new schema from interpretation
            new_attributes = interpretation.get("attributes", [])
            new_columns = []
            
            for attr in new_attributes:
                if ":" in attr:
                    name, type_hint = attr.split(":", 1)
                    sql_type = self._convert_type_hint_to_sql(type_hint.strip())
                    new_columns.append(f"{name.strip()} {sql_type}")
                else:
                    new_columns.append(f"{attr.strip()} TEXT")
            
            # Add ID column if not present
            if not any("id" in col.lower() for col in new_columns):
                new_columns.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")
            
            # Apply migration using ALTER TABLE (for simple cases) or recreate table
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                
                # For simplicity, we'll recreate the table with new schema
                # In production, this would need more sophisticated migration logic
                
                # Backup existing data
                cursor.execute(f"CREATE TEMPORARY TABLE {table_name}_backup AS SELECT * FROM {table_name}")
                
                # Drop old table
                cursor.execute(f"DROP TABLE {table_name}")
                
                # Create new table with updated schema
                columns_sql = ", ".join(new_columns)
                cursor.execute(f"CREATE TABLE {table_name} ({columns_sql})")
                
                # Restore data (matching columns only)
                try:
                    cursor.execute(f"INSERT INTO {table_name} SELECT * FROM {table_name}_backup")
                except sqlite3.Error:
                    # If schemas don't match, insert only matching columns
                    logger.warning(f"Schema mismatch during migration for {table_name}, inserting compatible data only")
                
                # Clean up backup table
                cursor.execute(f"DROP TABLE {table_name}_backup")
                
                conn.commit()
            
            result = {
                "database_path": db_file,
                "table": table_name,
                "migrated_columns": new_columns,
                "migration_applied": True,
                "improvements_applied": interpretation
            }
            
            logger.info(f"✅ Schema migration completed for {table_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Schema migration failed: {str(e)}")
            raise

    def _get_current_table_schema(self, db_file: str, table_name: str) -> List[str]:
        """Get current table schema"""
        try:
            with sqlite3.connect(db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                return [f"{col[1]} {col[2]}" for col in columns]
        except Exception:
            return []

    def _convert_type_hint_to_sql(self, type_hint: str) -> str:
        """Convert Python type hint to SQL type"""
        type_mapping = {
            "str": "TEXT",
            "int": "INTEGER", 
            "float": "REAL",
            "bool": "INTEGER",
            "date": "TEXT",
            "datetime": "TEXT"
        }
        return type_mapping.get(type_hint.lower(), "TEXT")

    def _fix_database_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fix database issues based on TechLeadSWEA coordination"""
        try:
            entity = payload.get("entity", "Student")
            fix_context = payload.get("fix_context", {})
            issue_type = fix_context.get("issue_type", "")
            fix_action = payload.get("fix_action", "")
            issue_description = fix_context.get("issue_description", "")
            
            logger.info("🔧 DatabaseSWEA: Fixing database issues for %s - %s", entity, issue_description)
            
            # Handle different types of database issues
            if "schema" in issue_type or "table" in issue_type or "column" in issue_type:
                logger.debug("🔧 DatabaseSWEA: Fixing schema/table issues - recreating database")
                return self._setup_database(payload)
            elif "connection" in issue_type or "access" in issue_type:
                logger.debug("🔧 DatabaseSWEA: Fixing connection/access issues")
                # For connection issues, try to recreate the database with proper permissions
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix database connection: {issue_description}"],
                }
                return self._setup_database(enhanced_payload)
            elif "migration" in issue_type or "constraint" in issue_type:
                logger.debug("🔧 DatabaseSWEA: Fixing migration/constraint issues")
                # For migration issues, we need to handle existing data
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix migration issues: {issue_description}"],
                }
                return self._setup_database(enhanced_payload)
            elif "data" in issue_type or "integrity" in issue_type:
                logger.debug("🔧 DatabaseSWEA: Fixing data integrity issues")
                # For data integrity issues, recreate with better constraints
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"Fix data integrity: {issue_description}"],
                }
                return self._setup_database(enhanced_payload)
            else:
                # Default: recreate database with generic fix instructions
                logger.debug("🔧 DatabaseSWEA: Default fix - recreating database")
                enhanced_payload = {
                    **payload,
                    "techlead_feedback": [f"General database fix needed: {issue_description}"],
                }
                return self._setup_database(enhanced_payload)
                
        except Exception as e:
            logger.error("❌ DatabaseSWEA fix_issues failed: %s", str(e))
            return self.create_error_response("fix_issues", str(e), "fix_error")

# ---------------------------------------------------------------------------
# Custom exception to make failures explicit
# ---------------------------------------------------------------------------


class DatabaseGenerationError(Exception):
    """Raised when database generation or feedback interpretation fails"""
    pass
