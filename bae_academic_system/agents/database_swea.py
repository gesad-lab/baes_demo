from bae_academic_system.agents.base_agent import BaseAgent
from bae_academic_system.core.managed_system_manager import ManagedSystemManager
from typing import Dict, Any, List
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

class DatabaseSWEA(BaseAgent):
    """SWEA responsible for preparing SQLite database schemas based on entity attributes."""

    def __init__(self):
        super().__init__("DatabaseSWEA", "Database Provisioning Agent", "SWEA")
        self.managed_system_manager = ManagedSystemManager()

    _SUPPORTED_TASKS = {
        "setup_database": "_setup_database"
    }

    def handle_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if task not in self._SUPPORTED_TASKS:
            return self.create_error_response(
                task,
                f"Unknown task. Supported tasks: {list(self._SUPPORTED_TASKS.keys())}",
                "invalid_task"
            )
        method = getattr(self, self._SUPPORTED_TASKS[task])
        try:
            return method(payload)
        except Exception as e:
            return self.create_error_response(task, str(e), "execution_error")

    # ------------------------------------------------------------------
    def _setup_database(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create SQLite database and a basic table for the entity."""
        entity = payload.get("entity", "Student")
        attributes: List[str] = payload.get("attributes", [])

        # Use managed system database path
        managed_system_path = self.managed_system_manager.managed_system_path
        db_file = payload.get(
            "database_path", 
            str(managed_system_path / "app" / "database" / "academic.db")
        )
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # Map Python types → SQLite
        type_map = {
            "str": "TEXT",
            "int": "INTEGER",
            "float": "REAL",
            "date": "TEXT"
        }

        # Build column definitions
        columns_sql: List[str] = []
        for attr in attributes:
            if ":" in attr:
                name, typ = [p.strip() for p in attr.split(":", 1)]
            else:
                name, typ = attr.strip(), "str"
            sql_type = type_map.get(typ.replace("Optional[", "").replace("]", ""), "TEXT")
            columns_sql.append(f"{name} {sql_type}")

        columns_sql_str = ", ".join(columns_sql) if columns_sql else "id INTEGER PRIMARY KEY AUTOINCREMENT"
        table_name = entity.lower() + "s"  # simple pluralisation

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql_str})")
            conn.commit()

        # Ensure managed system structure is updated
        self.managed_system_manager.ensure_managed_system_structure()
        
        logger.info(f"Managed system database created/updated at {db_file} with table {table_name}")
        return self.create_success_response(
            "setup_database",
            {
                "database_path": db_file,
                "table": table_name,
                "columns": columns_sql,
                "managed_system": True
            }
        ) 