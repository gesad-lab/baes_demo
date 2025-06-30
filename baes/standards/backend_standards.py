"""
Backend Standards for BackendSWEA Agent

Contains FastAPI, Pydantic, and database-specific patterns and validation rules
that BackendSWEA should follow and TechLeadSWEA should validate against.

These standards directly address the max_retries issue by ensuring alignment
between code generation and validation expectations.
"""

from typing import Any, Dict, List

from .base_standards import BaseStandards


class BackendStandards(BaseStandards):
    """
    Backend-specific standards and validation rules for FastAPI code generation.

    These standards define the exact patterns needed to pass TechLeadSWEA validation,
    particularly addressing database connection management, HTTP status codes,
    and error handling requirements that were causing max_retries failures.
    """

    # Required imports for FastAPI backend code
    REQUIRED_IMPORTS = {
        "fastapi_core": "from fastapi import APIRouter, HTTPException, Depends, status, Response",
        "pydantic": "from pydantic import BaseModel",
        "typing": "from typing import List, Optional",
        "database": "import sqlite3",
        "pathlib": "from pathlib import Path",
        "context_manager": "from contextlib import contextmanager",
        "logging": "import logging",
    }

    # Database connection patterns (CRITICAL - addresses main retry cause)
    DATABASE_PATTERNS = {
        "context_manager_decorator": "@contextmanager",
        "context_manager_function": "def get_db_connection():",
        "connection_setup": [
            'db_path = Path("app/database/academic.db")',
            "db_path.parent.mkdir(parents=True, exist_ok=True)",
            "conn = sqlite3.connect(str(db_path))",
            "conn.row_factory = sqlite3.Row",
        ],
        "exception_handling": [
            "try:",
            "yield conn",
            "except Exception:",
            "conn.rollback()",
            "raise",
            "finally:",
            "conn.close()",
        ],
        "dependency_function": ["def get_db():", "with get_db_connection() as conn:", "yield conn"],
        "required_patterns": [
            "@contextmanager",
            "try:",
            "yield conn",
            "except Exception:",
            "conn.rollback()",
            "finally:",
            "conn.close()",
        ],
        "forbidden_patterns": [
            "sqlite3.connect without context manager",
            "conn = sqlite3.connect without try/finally",
            "missing rollback in exception handler",
        ],
    }

    # HTTP status code requirements (CRITICAL - TechLeadSWEA requirement)
    HTTP_STATUS_CODES = {
        "POST": {
            "decorator": "status_code=status.HTTP_201_CREATED",
            "value": "201",
            "usage": '@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)',
        },
        "GET": {
            "decorator": "status_code=status.HTTP_200_OK",
            "value": "200",
            "usage": '@router.get("/", response_model=List[EntityResponse])',
        },
        "PUT": {
            "decorator": "status_code=status.HTTP_200_OK",
            "value": "200",
            "usage": '@router.put("/{id}", response_model=EntityResponse)',
        },
        "DELETE": {
            "decorator": "status_code=status.HTTP_204_NO_CONTENT",
            "value": "204",
            "usage": '@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)',
            "return_pattern": "return Response(status_code=status.HTTP_204_NO_CONTENT)",
        },
    }

    # Error handling patterns (CRITICAL - TechLeadSWEA requirement)
    ERROR_HANDLING = {
        "database_operations": {
            "pattern": [
                "try:",
                "# database operations",
                "db.commit()",
                "except HTTPException:",
                "raise",
                "except Exception as e:",
                "db.rollback()",
                'logger.error(f"Error message: {e}")',
                'raise HTTPException(status_code=500, detail="Error message")',
            ],
            "required_elements": [
                "try/except blocks",
                "db.rollback() in except",
                "HTTPException with status_code=500",
                "logger.error() call",
            ],
        },
        "http_exceptions": {
            "not_found": 'raise HTTPException(status_code=404, detail="Entity not found")',
            "server_error": 'raise HTTPException(status_code=500, detail="Internal server error")',
            "bad_request": 'raise HTTPException(status_code=400, detail="Bad request")',
            "reraise_pattern": "except HTTPException:\n    raise",
        },
    }

    # Pydantic model patterns
    PYDANTIC_PATTERNS = {
        "base_model": {
            "inheritance": "class EntityBase(BaseModel):",
            "field_definition": "field_name: field_type",
            "required_fields": ["proper type hints", "field definitions"],
        },
        "create_model": {"inheritance": "class EntityCreate(EntityBase):", "pattern": "pass"},
        "update_model": {
            "inheritance": "class EntityUpdate(BaseModel):",
            "fields": "same as base but all optional",
            "pattern": "field_name: Optional[field_type] = None",
        },
        "response_model": {
            "inheritance": "class EntityResponse(EntityBase):",
            "additional_fields": ["id: int"],
            "config": "class Config:\n    from_attributes = True",
        },
    }

    # API endpoint patterns
    API_PATTERNS = {
        "router_setup": {
            "definition": 'router = APIRouter(prefix="/entities", tags=["entities"])',
            "required_elements": ["prefix", "tags"],
        },
        "crud_endpoints": {
            "create": {
                "decorator": '@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)',
                "function": "async def create_entity(entity_data: EntityCreate, db: sqlite3.Connection = Depends(get_db)):",
                "error_handling": "required",
                "return_type": "EntityResponse",
            },
            "read_list": {
                "decorator": '@router.get("/", response_model=List[EntityResponse])',
                "function": "async def list_entities(db: sqlite3.Connection = Depends(get_db)):",
                "return_type": "List[EntityResponse]",
            },
            "read_one": {
                "decorator": '@router.get("/{id}", response_model=EntityResponse)',
                "function": "async def get_entity(id: int, db: sqlite3.Connection = Depends(get_db)):",
                "error_handling": "404 for not found",
                "return_type": "EntityResponse",
            },
            "update": {
                "decorator": '@router.put("/{id}", response_model=EntityResponse)',
                "function": "async def update_entity(id: int, entity_data: EntityUpdate, db: sqlite3.Connection = Depends(get_db)):",
                "error_handling": "404 for not found",
                "return_type": "EntityResponse",
            },
            "delete": {
                "decorator": '@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)',
                "function": "async def delete_entity(id: int, db: sqlite3.Connection = Depends(get_db)):",
                "return_pattern": "return Response(status_code=status.HTTP_204_NO_CONTENT)",
                "error_handling": "404 for not found",
            },
        },
    }

    # Validation methods specific to backend code
    @classmethod
    def validate_database_connection(cls, code: str) -> Dict[str, Any]:
        """
        Validate database connection patterns against TechLeadSWEA requirements.

        This addresses the main cause of max_retries: improper database connection handling.
        """
        issues = []
        suggestions = []

        # Check for context manager decorator
        if "@contextmanager" not in code:
            issues.append("Missing @contextmanager decorator for database connection")
            suggestions.append("Add @contextmanager decorator to get_db_connection function")

        # Check for proper exception handling
        if "try:" in code and "finally:" not in code:
            issues.append(
                "Database connection is not managed properly; connections are not closed in a finally block"
            )
            suggestions.append(
                "Use context manager pattern: @contextmanager def get_db_connection(): try: yield conn; finally: conn.close()"
            )

        # Check for rollback in exception handler
        if "except" in code and "rollback" not in code:
            issues.append("Missing database rollback in exception handlers")
            suggestions.append("Add db.rollback() in except blocks for all database operations")

        # Check for connection closing
        if "sqlite3.connect" in code and "conn.close()" not in code:
            issues.append("Database connections are not properly closed")
            suggestions.append("Ensure connections are closed in finally block")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL",
        }

    @classmethod
    def validate_http_status_codes(cls, code: str) -> Dict[str, Any]:
        """
        Validate HTTP status codes against TechLeadSWEA requirements.

        Ensures proper status codes, especially 204 for DELETE operations.
        """
        issues = []
        suggestions = []

        # Check DELETE endpoint status code
        if "@router.delete" in code:
            if "status.HTTP_204_NO_CONTENT" not in code:
                issues.append(
                    "The DELETE endpoint does not return a 204 No Content status code upon successful deletion"
                )
                suggestions.append(
                    "Change the response for the DELETE endpoint to return status code 204 instead of a JSON response"
                )

            if "return Response(status_code=status.HTTP_204_NO_CONTENT)" not in code:
                issues.append("DELETE endpoint does not return proper HTTP status code")
                suggestions.append(
                    "Return Response(status_code=status.HTTP_204_NO_CONTENT) for DELETE operations"
                )

        # Check POST endpoint status code
        if "@router.post" in code and "status.HTTP_201_CREATED" not in code:
            issues.append("POST endpoint missing 201 Created status code")
            suggestions.append("Add status_code=status.HTTP_201_CREATED to POST decorator")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL",
        }

    @classmethod
    def validate_error_handling(cls, code: str) -> Dict[str, Any]:
        """
        Validate error handling patterns against TechLeadSWEA requirements.
        """
        issues = []
        suggestions = []

        # Check for HTTPException usage
        if "def " in code and "HTTPException" not in code:
            issues.append("Missing HTTPException for proper error responses")
            suggestions.append(
                "Add try/except blocks with HTTPException for all database operations"
            )

        # Check for proper exception handling in database operations
        if "cursor.execute" in code and "try:" not in code:
            issues.append("Database operations without proper error handling")
            suggestions.append(
                "Add try/except blocks with HTTPException for all database operations"
            )

        # Check for logging in error handlers
        if "except" in code and "logger.error" not in code:
            issues.append("Missing error logging in exception handlers")
            suggestions.append("Implement logging for error handling to capture exceptions")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "REQUIRED",
        }

    @classmethod
    def validate_api_completeness(cls, code: str, entity: str) -> Dict[str, Any]:
        """
        Validate that all required CRUD endpoints are implemented.
        """
        issues = []
        suggestions = []

        required_endpoints = ["create_", "get_", "update_", "delete_", "list_"]
        crud_decorators = ["@router.post", "@router.get", "@router.put", "@router.delete"]

        # Check for all CRUD operations
        for endpoint in required_endpoints:
            if endpoint not in code:
                issues.append(f"Missing {endpoint} endpoint implementation")
                suggestions.append(f"Add missing CRUD endpoints: {', '.join(required_endpoints)}")
                break

        # Check for router decorators
        for decorator in crud_decorators:
            if decorator not in code:
                issues.append(f"Missing {decorator} endpoint")
                suggestions.append("Add missing CRUD endpoints with proper decorators")
                break

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "priority": "CRITICAL",
        }

    @classmethod
    def get_backend_validation(cls, code: str, entity: str) -> Dict[str, Any]:
        """
        Run comprehensive backend validation against all standards.

        This method performs all the validations that TechLeadSWEA should use
        to ensure consistency between generation and validation.
        """
        # Run all backend-specific validations
        db_validation = cls.validate_database_connection(code)
        status_validation = cls.validate_http_status_codes(code)
        error_validation = cls.validate_error_handling(code)
        api_validation = cls.validate_api_completeness(code, entity)

        # Run base validations
        base_validation = cls.get_comprehensive_validation(code)

        # Combine all issues and suggestions
        all_issues = (
            db_validation["issues"]
            + status_validation["issues"]
            + error_validation["issues"]
            + api_validation["issues"]
            + base_validation["issues"]
        )

        all_suggestions = (
            db_validation["suggestions"]
            + status_validation["suggestions"]
            + error_validation["suggestions"]
            + api_validation["suggestions"]
            + base_validation["suggestions"]
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
                "database_connection": db_validation,
                "http_status_codes": status_validation,
                "error_handling": error_validation,
                "api_completeness": api_validation,
                "base_standards": base_validation,
            },
            "entity": entity,
        }
