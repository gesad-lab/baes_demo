"""
Database Standards for DatabaseSWEA Agent

Contains SQLite-specific patterns and validation rules that DatabaseSWEA
should follow and TechLeadSWEA should validate against.

These standards ensure consistency in database schema generation and eliminate
validation misalignment for database code.
"""

from typing import Any, Dict

from .base_standards import BaseStandards


class DatabaseStandards(BaseStandards):
    """
    Database-specific standards and validation rules for SQLite schema generation.
    
    These standards define the exact patterns needed to pass TechLeadSWEA validation,
    particularly addressing schema structure, constraints, and database operations.
    """
    
    # Required imports for database code
    REQUIRED_IMPORTS = {
        "sqlite3": "import sqlite3",
        "pathlib": "from pathlib import Path",
        "logging": "import logging",
        "datetime": "from datetime import datetime",
        "typing": "from typing import Dict, List, Optional, Any",
    }
    
    # Schema patterns (CRITICAL - for table structure)
    SCHEMA_PATTERNS = {
        "table_creation": {
            "primary_key": "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "not_null": "field_name TEXT NOT NULL",
            "unique": "field_name TEXT UNIQUE",
            "foreign_key": "FOREIGN KEY (field_id) REFERENCES other_table(id)",
            "timestamps": [
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ]
        },
        "field_types": {
            "string": "TEXT",
            "integer": "INTEGER", 
            "float": "REAL",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "email": "TEXT"  # with validation constraint
        },
        "constraints": {
            "primary_key": "PRIMARY KEY",
            "not_null": "NOT NULL",
            "unique": "UNIQUE",
            "check": "CHECK (condition)",
            "default": "DEFAULT value"
        }
    }
    
    # Database connection patterns (CRITICAL - reuse from backend)
    CONNECTION_PATTERNS = {
        "database_path": "Path(\"app/database/baes_system.db\")",
        "path_creation": "db_path.parent.mkdir(parents=True, exist_ok=True)",
        "connection": "sqlite3.connect(str(db_path))",
        "row_factory": "conn.row_factory = sqlite3.Row",
        "exception_handling": [
            "try:",
            "conn = sqlite3.connect(str(db_path))",
            "# database operations",
            "conn.commit()",
            "except Exception as e:",
            "conn.rollback()",
            "raise",
            "finally:",
            "conn.close()"
        ]
    }
    
    # SQL operation patterns
    SQL_PATTERNS = {
        "create_table": {
            "template": "CREATE TABLE IF NOT EXISTS table_name (columns)",
            "with_constraints": "CREATE TABLE IF NOT EXISTS table_name (id INTEGER PRIMARY KEY AUTOINCREMENT, field TEXT NOT NULL)",
            "foreign_keys": "PRAGMA foreign_keys = ON"
        },
        "indexes": {
            "create_index": "CREATE INDEX IF NOT EXISTS idx_table_field ON table_name(field)",
            "unique_index": "CREATE UNIQUE INDEX IF NOT EXISTS idx_table_field ON table_name(field)"
        },
        "migrations": {
            "alter_table": "ALTER TABLE table_name ADD COLUMN new_field TEXT",
            "drop_column": "-- SQLite doesn't support DROP COLUMN directly",
            "rename_table": "ALTER TABLE old_name RENAME TO new_name"
        }
    }
    
    # Data validation patterns
    VALIDATION_PATTERNS = {
        "email_check": "CHECK (email LIKE '%@%')",
        "positive_numbers": "CHECK (field_name > 0)",
        "date_range": "CHECK (start_date <= end_date)",
        "enum_values": "CHECK (status IN ('active', 'inactive', 'pending'))"
    }
    
    # Database initialization patterns
    INIT_PATTERNS = {
        "function_structure": [
            "def setup_database(db_path: str = None) -> str:",
            "\"\"\"Initialize database with all required tables\"\"\"",
            "if db_path is None:",
            "db_path = Path(\"app/database/baes_system.db\")",
            "else:",
            "db_path = Path(db_path)",
            "db_path.parent.mkdir(parents=True, exist_ok=True)",
            "return str(db_path)"
        ],
        "table_creation_order": [
            "# Create tables in dependency order",
            "# Parent tables first, then child tables with foreign keys"
        ],
        "error_handling": [
            "try:",
            "# Database operations",
            "conn.commit()",
            "logger.info(\"Database setup completed successfully\")",
            "except Exception as e:",
            "conn.rollback()",
            "logger.error(f\"Database setup failed: {e}\")",
            "raise",
            "finally:",
            "conn.close()"
        ]
    }
    
    # Validation methods specific to database code
    @classmethod
    def validate_schema_structure(cls, code: str) -> Dict[str, Any]:
        """
        Validate database schema structure and table definitions.
        """
        issues = []
        suggestions = []
        
        # Check for primary key
        if "CREATE TABLE" in code and "PRIMARY KEY" not in code:
            issues.append("Tables missing primary key definitions")
            suggestions.append("Add PRIMARY KEY constraint to table definitions")
        
        # Check for proper table creation
        if "CREATE TABLE" in code and "IF NOT EXISTS" not in code:
            issues.append("Table creation without IF NOT EXISTS clause")
            suggestions.append("Use CREATE TABLE IF NOT EXISTS for safer table creation")
        
        # Check for foreign key constraints
        if "FOREIGN KEY" in code and "PRAGMA foreign_keys = ON" not in code:
            issues.append("Foreign keys defined but pragma not enabled")
            suggestions.append("Add PRAGMA foreign_keys = ON to enable foreign key constraints")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL"
        }
    
    @classmethod
    def validate_connection_handling(cls, code: str) -> Dict[str, Any]:
        """
        Validate database connection patterns and resource management.
        """
        issues = []
        suggestions = []
        
        # Check for proper path handling
        if "sqlite3.connect" in code and "Path" not in code:
            issues.append("Database connection without proper path handling")
            suggestions.append("Use pathlib.Path for database path management")
        
        # Check for directory creation
        if "Path" in code and "mkdir" not in code:
            issues.append("Missing directory creation for database path")
            suggestions.append("Add db_path.parent.mkdir(parents=True, exist_ok=True)")
        
        # Check for transaction handling
        if "sqlite3.connect" in code and "commit" not in code:
            issues.append("Database operations without transaction commit")
            suggestions.append("Add conn.commit() after database operations")
        
        # Check for connection closing
        if "sqlite3.connect" in code and ("close" not in code and "finally" not in code):
            issues.append("Database connections not properly closed")
            suggestions.append("Add conn.close() in finally block or use context manager")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL"
        }
    
    @classmethod
    def validate_sql_syntax(cls, code: str) -> Dict[str, Any]:
        """
        Validate SQL syntax and best practices.
        """
        issues = []
        suggestions = []
        
        # Check for parameterized queries (if INSERT/UPDATE present)
        if ("INSERT" in code or "UPDATE" in code) and "?" not in code and "execute" in code:
            issues.append("SQL queries without parameterization (SQL injection risk)")
            suggestions.append("Use parameterized queries with ? placeholders")
        
        # Check for proper field types
        if "CREATE TABLE" in code:
            # Check for common type issues
            if "VARCHAR" in code:
                issues.append("Using VARCHAR instead of TEXT in SQLite")
                suggestions.append("Use TEXT instead of VARCHAR for string fields in SQLite")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "REQUIRED"
        }
    
    @classmethod
    def validate_database_completeness(cls, code: str, entity: str) -> Dict[str, Any]:
        """
        Validate that all required database components are implemented.
        """
        issues = []
        suggestions = []
        
        entity_lower = entity.lower()
        entity_plural = f"{entity_lower}s"
        
        # Check for table creation
        if f"CREATE TABLE" not in code:
            issues.append(f"Missing table creation for {entity}")
            suggestions.append(f"Add CREATE TABLE statement for {entity_plural}")
        
        # Check for setup function
        if "def setup_database" not in code and "def" in code:
            issues.append("Missing setup_database function")
            suggestions.append("Add setup_database() function for database initialization")
        
        # Check for proper logging
        if "logger" not in code:
            issues.append("Missing logging for database operations")
            suggestions.append("Add logging for database setup and error tracking")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL"
        }
    
    @classmethod
    def get_database_validation(cls, code: str, entity: str) -> Dict[str, Any]:
        """
        Run comprehensive database validation against all standards.
        
        This method performs all the validations that TechLeadSWEA should use
        to ensure consistency between generation and validation.
        """
        # Run all database-specific validations
        schema_validation = cls.validate_schema_structure(code)
        connection_validation = cls.validate_connection_handling(code)
        sql_validation = cls.validate_sql_syntax(code)
        db_validation = cls.validate_database_completeness(code, entity)
        
        # Run base validations
        base_validation = cls.get_comprehensive_validation(code)
        
        # Combine all issues and suggestions
        all_issues = (
            schema_validation["issues"] +
            connection_validation["issues"] +
            sql_validation["issues"] +
            db_validation["issues"] +
            base_validation["issues"]
        )
        
        all_suggestions = (
            schema_validation["suggestions"] +
            connection_validation["suggestions"] + 
            sql_validation["suggestions"] +
            db_validation["suggestions"] +
            base_validation["suggestions"]
        )
        
        # Calculate overall validity
        is_valid = len(all_issues) == 0
        quality_score = max(0.0, 1.0 - (len(all_issues) * 0.1))
        
        return {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "issues": all_issues,
            "suggestions": all_suggestions,
            "validation_details": {
                "schema_structure": schema_validation,
                "connection_handling": connection_validation,
                "sql_syntax": sql_validation,
                "database_completeness": db_validation,
                "base_standards": base_validation
            },
            "entity": entity
        } 