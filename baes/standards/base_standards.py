"""
Base Standards for all SWEA Agents

Contains common patterns, validation rules, and requirements that apply
across all SWEA agents to ensure consistency and quality.
"""

from typing import Any, Dict


class BaseStandards:
    """
    Base standards and validation rules applicable to all SWEA agents.

    These standards define common patterns for imports, error handling,
    logging, and other cross-cutting concerns that all SWEAs should follow.
    """

    # Common import patterns that most SWEAs need
    COMMON_IMPORTS = {
        "logging": "import logging",
        "typing": "from typing import List, Dict, Any, Optional",
        "pathlib": "from pathlib import Path",
    }

    # Logging patterns that all SWEAs should follow
    LOGGING_PATTERNS = {
        "logger_setup": "logger = logging.getLogger(__name__)",
        "error_logging": 'logger.error(f"Error: {e}")',
        "info_logging": 'logger.info(f"Message")',
        "debug_logging": 'logger.debug(f"Debug info")',
    }

    # Error handling patterns
    ERROR_HANDLING = {
        "required_patterns": ["try:", "except Exception as e:", "logger.error"],
        "exception_types": ["Exception", "ValueError", "TypeError", "FileNotFoundError"],
        "logging_required": True,
        "reraise_pattern": "raise SomeSpecificException(...) from e",
    }

    # File handling patterns
    FILE_HANDLING = {
        "path_creation": "Path(...).parent.mkdir(parents=True, exist_ok=True)",
        "file_writing": "with open(file_path, 'w') as f:\n    f.write(content)",
        "file_reading": "with open(file_path, 'r') as f:\n    content = f.read()",
        "pathlib_usage": "Use pathlib.Path instead of os.path",
    }

    # Code quality requirements
    QUALITY_REQUIREMENTS = {
        "docstrings": {
            "required": True,
            "format": "Google style docstrings",
            "minimum_functions": ["all public methods"],
        },
        "type_hints": {
            "required": True,
            "format": "Python 3.8+ style",
            "required_for": ["function parameters", "return types"],
        },
        "naming_conventions": {
            "functions": "snake_case",
            "classes": "PascalCase",
            "constants": "UPPER_SNAKE_CASE",
            "variables": "snake_case",
        },
        "line_length": 100,
        "indentation": 4,
    }

    # Validation methods for common patterns
    @classmethod
    def validate_imports(cls, code: str) -> Dict[str, Any]:
        """
        Validate that code contains proper import statements.

        Args:
            code: The code to validate

        Returns:
            Dict with validation results
        """
        issues = []
        suggestions = []

        # Check for logging import
        if "logger" in code and "import logging" not in code:
            issues.append("Missing logging import when logger is used")
            suggestions.append("Add: import logging")

        # Check for type hints import
        if (
            any(hint in code for hint in ["List", "Dict", "Any", "Optional"])
            and "from typing import" not in code
        ):
            issues.append("Missing typing imports when type hints are used")
            suggestions.append("Add: from typing import List, Dict, Any, Optional")

        return {"is_valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    @classmethod
    def validate_error_handling(cls, code: str) -> Dict[str, Any]:
        """
        Validate that code contains proper error handling patterns.

        Args:
            code: The code to validate

        Returns:
            Dict with validation results
        """
        issues = []
        suggestions = []

        # Check for try/except blocks
        if "try:" not in code and any(
            risky in code for risky in ["open(", "requests.", "sqlite3."]
        ):
            issues.append("Missing try/except blocks for potentially failing operations")
            suggestions.append("Add try/except blocks around risky operations")

        # Check for logging in exception handlers
        if "except" in code and "logger.error" not in code:
            issues.append("Exception handling without error logging")
            suggestions.append("Add logger.error() in except blocks")

        return {"is_valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    @classmethod
    def validate_code_quality(cls, code: str) -> Dict[str, Any]:
        """
        Validate general code quality requirements.

        Args:
            code: The code to validate

        Returns:
            Dict with validation results
        """
        issues = []
        suggestions = []

        # Check for docstrings in functions
        function_lines = [line for line in code.split("\n") if line.strip().startswith("def ")]
        if function_lines:
            # Simple check - look for triple quotes after function definitions
            if '"""' not in code and "'''" not in code:
                issues.append("Functions missing docstrings")
                suggestions.append("Add docstrings to all public functions")

        # Check for type hints
        if function_lines and "->" not in code:
            issues.append("Functions missing return type hints")
            suggestions.append("Add return type hints to functions")

        return {"is_valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    @classmethod
    def get_comprehensive_validation(cls, code: str) -> Dict[str, Any]:
        """
        Run all base validations and return comprehensive results.

        Args:
            code: The code to validate

        Returns:
            Dict with comprehensive validation results
        """
        import_validation = cls.validate_imports(code)
        error_validation = cls.validate_error_handling(code)
        quality_validation = cls.validate_code_quality(code)

        all_issues = (
            import_validation["issues"] + error_validation["issues"] + quality_validation["issues"]
        )

        all_suggestions = (
            import_validation["suggestions"]
            + error_validation["suggestions"]
            + quality_validation["suggestions"]
        )

        return {
            "is_valid": len(all_issues) == 0,
            "overall_score": max(0.0, 1.0 - (len(all_issues) * 0.1)),
            "issues": all_issues,
            "suggestions": all_suggestions,
            "validation_details": {
                "imports": import_validation,
                "error_handling": error_validation,
                "code_quality": quality_validation,
            },
        }
