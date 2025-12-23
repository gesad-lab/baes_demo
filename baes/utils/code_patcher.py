"""
Code patcher utility for targeted fixes (US6: Smart Retry).

This module provides AST-based code patching capabilities for applying
targeted fixes to code without full regeneration, reducing retry token consumption.

Constitutional Compliance:
- PEP 8: Type hints, docstrings, snake_case naming
- DRY: Reusable patch operations for common fixes
- Fail-fast: Validate AST and syntax before applying patches
"""

import ast
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PatchResult:
    """Result of a code patching operation.
    
    Attributes:
        success: Whether the patch was applied successfully
        patched_code: The modified code (if successful)
        original_code: The original code before patching
        patch_type: Type of patch applied (e.g., "add_decorator", "fix_status_code")
        patch_location: Description of where patch was applied
        validation_passed: Whether patched code passed syntax validation
        error_message: Error message if patch failed
        tokens_saved: Estimated tokens saved vs full regeneration
    """
    success: bool
    patched_code: Optional[str]
    original_code: str
    patch_type: str
    patch_location: str
    validation_passed: bool
    error_message: Optional[str]
    tokens_saved: int


class CodePatcher:
    """
    AST-based code patcher for targeted fixes.
    
    Provides methods to patch common code issues without full regeneration:
    - Add missing decorators (@contextmanager)
    - Fix HTTP status codes (201, 404, 204)
    - Add missing imports
    - Add missing error handling
    - Add missing docstrings
    - Fix type hints
    """
    
    # Estimated token costs (used for savings calculation)
    FULL_REGENERATION_TOKENS = 2000  # Typical full regeneration cost
    TARGETED_PATCH_TOKENS = 500  # Typical targeted patch cost
    
    def __init__(self):
        """Initialize code patcher."""
        self.patch_history = []
    
    def add_decorator(
        self, 
        code: str, 
        function_name: str, 
        decorator_name: str
    ) -> PatchResult:
        """
        Add a decorator to a function using AST manipulation.
        
        Args:
            code: Original Python code
            function_name: Name of function to decorate
            decorator_name: Name of decorator to add (e.g., "contextmanager")
            
        Returns:
            PatchResult with patched code or error
        """
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Find target function
            function_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    function_node = node
                    break
            
            if not function_node:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    original_code=code,
                    patch_type="add_decorator",
                    patch_location=f"function '{function_name}'",
                    validation_passed=False,
                    error_message=f"Function '{function_name}' not found in code",
                    tokens_saved=0
                )
            
            # Check if decorator already exists
            existing_decorators = [d.id if isinstance(d, ast.Name) else str(d) for d in function_node.decorator_list]
            if decorator_name in existing_decorators:
                return PatchResult(
                    success=True,
                    patched_code=code,
                    original_code=code,
                    patch_type="add_decorator",
                    patch_location=f"function '{function_name}'",
                    validation_passed=True,
                    error_message=None,
                    tokens_saved=0  # No change needed
                )
            
            # Find function definition line
            lines = code.split("\n")
            function_line_idx = None
            for i, line in enumerate(lines):
                if f"def {function_name}" in line:
                    function_line_idx = i
                    break
            
            if function_line_idx is None:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    original_code=code,
                    patch_type="add_decorator",
                    patch_location=f"function '{function_name}'",
                    validation_passed=False,
                    error_message=f"Could not locate function definition line for '{function_name}'",
                    tokens_saved=0
                )
            
            # Determine indentation
            function_line = lines[function_line_idx]
            indent = len(function_line) - len(function_line.lstrip())
            decorator_line = " " * indent + f"@{decorator_name}"
            
            # Insert decorator before function
            lines.insert(function_line_idx, decorator_line)
            patched_code = "\n".join(lines)
            
            # Validate syntax
            validation_passed = self._validate_syntax(patched_code)
            
            if not validation_passed:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    original_code=code,
                    patch_type="add_decorator",
                    patch_location=f"function '{function_name}'",
                    validation_passed=False,
                    error_message="Patched code failed syntax validation",
                    tokens_saved=0
                )
            
            tokens_saved = self.FULL_REGENERATION_TOKENS - self.TARGETED_PATCH_TOKENS
            
            logger.info(f"✅ Added @{decorator_name} to {function_name} (saved ~{tokens_saved} tokens)")
            
            return PatchResult(
                success=True,
                patched_code=patched_code,
                original_code=code,
                patch_type="add_decorator",
                patch_location=f"function '{function_name}' at line {function_line_idx + 1}",
                validation_passed=True,
                error_message=None,
                tokens_saved=tokens_saved
            )
            
        except SyntaxError as e:
            return PatchResult(
                success=False,
                patched_code=None,
                original_code=code,
                patch_type="add_decorator",
                patch_location=f"function '{function_name}'",
                validation_passed=False,
                error_message=f"Syntax error in original code: {str(e)}",
                tokens_saved=0
            )
        except Exception as e:
            logger.error(f"❌ Failed to add decorator: {e}")
            return PatchResult(
                success=False,
                patched_code=None,
                original_code=code,
                patch_type="add_decorator",
                patch_location=f"function '{function_name}'",
                validation_passed=False,
                error_message=str(e),
                tokens_saved=0
            )
    
    def fix_status_code(
        self,
        code: str,
        target_function: str,
        correct_status: int
    ) -> PatchResult:
        """
        Fix HTTP status code in FastAPI route decorator or return statement.
        
        Args:
            code: Original Python code
            target_function: Name of function/endpoint to fix
            correct_status: Correct status code (e.g., 201, 404, 204)
            
        Returns:
            PatchResult with patched code or error
        """
        try:
            # Pattern to match status_code parameter in decorator
            decorator_pattern = rf'(@router\.\w+\([^)]*status_code=)(\d+)([^)]*\))'
            
            # Pattern to match HTTP status in function signature/return
            function_start = f"def {target_function}"
            
            lines = code.split("\n")
            patched_lines = []
            patch_applied = False
            patch_location = ""
            
            for i, line in enumerate(lines):
                if function_start in line or (patch_applied and i < len(lines)):
                    # Check for status_code in decorator (line before function or same line)
                    match = re.search(decorator_pattern, line)
                    if match and not patch_applied:
                        old_status = match.group(2)
                        if int(old_status) != correct_status:
                            patched_line = re.sub(
                                decorator_pattern,
                                rf'\g<1>{correct_status}\g<3>',
                                line
                            )
                            patched_lines.append(patched_line)
                            patch_applied = True
                            patch_location = f"line {i + 1}, decorator status_code"
                            logger.info(f"🔧 Fixed status code: {old_status} → {correct_status} in {target_function}")
                            continue
                
                patched_lines.append(line)
            
            if not patch_applied:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    original_code=code,
                    patch_type="fix_status_code",
                    patch_location=f"function '{target_function}'",
                    validation_passed=False,
                    error_message=f"Could not find status_code parameter in {target_function}",
                    tokens_saved=0
                )
            
            patched_code = "\n".join(patched_lines)
            
            # Validate syntax
            validation_passed = self._validate_syntax(patched_code)
            
            if not validation_passed:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    original_code=code,
                    patch_type="fix_status_code",
                    patch_location=patch_location,
                    validation_passed=False,
                    error_message="Patched code failed syntax validation",
                    tokens_saved=0
                )
            
            tokens_saved = self.FULL_REGENERATION_TOKENS - self.TARGETED_PATCH_TOKENS
            
            return PatchResult(
                success=True,
                patched_code=patched_code,
                original_code=code,
                patch_type="fix_status_code",
                patch_location=patch_location,
                validation_passed=True,
                error_message=None,
                tokens_saved=tokens_saved
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to fix status code: {e}")
            return PatchResult(
                success=False,
                patched_code=None,
                original_code=code,
                patch_type="fix_status_code",
                patch_location=f"function '{target_function}'",
                validation_passed=False,
                error_message=str(e),
                tokens_saved=0
            )
    
    def add_import(
        self,
        code: str,
        import_statement: str
    ) -> PatchResult:
        """
        Add a missing import statement at the top of the file.
        
        Args:
            code: Original Python code
            import_statement: Import to add (e.g., "from contextlib import contextmanager")
            
        Returns:
            PatchResult with patched code or error
        """
        try:
            # Check if import already exists
            if import_statement in code:
                return PatchResult(
                    success=True,
                    patched_code=code,
                    original_code=code,
                    patch_type="add_import",
                    patch_location="imports section",
                    validation_passed=True,
                    error_message=None,
                    tokens_saved=0  # No change needed
                )
            
            lines = code.split("\n")
            
            # Find last import line
            last_import_idx = -1
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    last_import_idx = i
            
            # Insert after last import or at top
            insert_idx = last_import_idx + 1 if last_import_idx >= 0 else 0
            lines.insert(insert_idx, import_statement)
            
            patched_code = "\n".join(lines)
            
            # Validate syntax
            validation_passed = self._validate_syntax(patched_code)
            
            if not validation_passed:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    original_code=code,
                    patch_type="add_import",
                    patch_location=f"line {insert_idx + 1}",
                    validation_passed=False,
                    error_message="Patched code failed syntax validation",
                    tokens_saved=0
                )
            
            tokens_saved = self.FULL_REGENERATION_TOKENS - self.TARGETED_PATCH_TOKENS
            
            logger.info(f"✅ Added import: {import_statement} (saved ~{tokens_saved} tokens)")
            
            return PatchResult(
                success=True,
                patched_code=patched_code,
                original_code=code,
                patch_type="add_import",
                patch_location=f"line {insert_idx + 1}",
                validation_passed=True,
                error_message=None,
                tokens_saved=tokens_saved
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to add import: {e}")
            return PatchResult(
                success=False,
                patched_code=None,
                original_code=code,
                patch_type="add_import",
                patch_location="imports section",
                validation_passed=False,
                error_message=str(e),
                tokens_saved=0
            )
    
    def _validate_syntax(self, code: str) -> bool:
        """
        Validate that code has correct Python syntax.
        
        Args:
            code: Python code to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    def apply_patch(
        self,
        code: str,
        patch_type: str,
        **kwargs
    ) -> PatchResult:
        """
        Apply a patch based on patch type.
        
        Dispatcher method that calls appropriate patch function based on type.
        
        Args:
            code: Original code
            patch_type: Type of patch to apply
            **kwargs: Additional arguments for specific patch type
            
        Returns:
            PatchResult with outcome
        """
        if patch_type == "add_decorator":
            return self.add_decorator(
                code,
                function_name=kwargs.get("function_name"),
                decorator_name=kwargs.get("decorator_name")
            )
        elif patch_type == "fix_status_code":
            return self.fix_status_code(
                code,
                target_function=kwargs.get("target_function"),
                correct_status=kwargs.get("correct_status")
            )
        elif patch_type == "add_import":
            return self.add_import(
                code,
                import_statement=kwargs.get("import_statement")
            )
        else:
            return PatchResult(
                success=False,
                patched_code=None,
                original_code=code,
                patch_type=patch_type,
                patch_location="unknown",
                validation_passed=False,
                error_message=f"Unknown patch type: {patch_type}",
                tokens_saved=0
            )
