import logging
import os
import sqlite3
from typing import Any, Dict, List

from ..agents.base_agent import BaseAgent
from ..core.managed_system_manager import ManagedSystemManager

logger = logging.getLogger(__name__)


class DatabaseSWEA(BaseAgent):
    """SWEA responsible for preparing SQLite database schemas based on entity attributes."""

    def __init__(self):
        super().__init__("DatabaseSWEA", "Database Provisioning Agent", "SWEA")
        self._managed_system_manager = None  # Lazy initialization

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

    # ------------------------------------------------------------------
    def _setup_database(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create SQLite database and a basic table for the entity."""
        entity = payload.get("entity", "Student")
        attributes: List[str] = payload.get("attributes", [])

        # Use managed system database path
        managed_system_path = self.managed_system_manager.managed_system_path
        db_file = payload.get(
            "database_path", str(managed_system_path / "app" / "database" / "academic.db")
        )
        os.makedirs(os.path.dirname(db_file), exist_ok=True)

        # Map Python types → SQLite
        type_map = {"str": "TEXT", "int": "INTEGER", "float": "REAL", "date": "TEXT"}

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
                "managed_system": True,
            },
        )
