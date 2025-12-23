"""
Validation Rules for Confidence-Based Code Validation
(Feature: 001-performance-optimization / US2)

Implements hybrid validation approach:
- Regex pattern matching for confident approval/rejection (70-80% cases)
- AST-based structural validation for type hints, docstrings, PEP 8
- Confidence classification: confident_approval, confident_rejection, uncertain
- LLM fallback only for uncertain cases (20-30%)

Constitutional compliance:
- Fail-fast: Confident rejection provides specific line numbers and feedback
- Observability: All validation outcomes logged with confidence scores
- Generator-first: Validation rules guide improvements, not block progress

Usage:
    validator = ValidationRuleEngine()
    result = validator.validate_code(code, swea_type="backend")
    
    if result.overall_outcome == "confident_approval":
        # Accept immediately, 0 tokens, <100ms
    elif result.overall_outcome == "confident_rejection":
        # Reject with specific feedback, 0 tokens
    else:  # uncertain
        # Fall back to LLM validation
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ValidationOutcome(Enum):
    """Validation outcome classification"""
    CONFIDENT_APPROVAL = "confident_approval"
    CONFIDENT_REJECTION = "confident_rejection"
    UNCERTAIN = "uncertain"


class SWEAType(Enum):
    """SWEA type for validation context"""
    BACKEND = "backend"
    DATABASE = "database"
    FRONTEND = "frontend"
    TEST = "test"


@dataclass
class RuleMatch:
    """Result of a single rule match"""
    rule_id: str
    rule_name: str
    passed: bool
    confidence: float  # 0.0 to 1.0
    line_number: Optional[int] = None
    message: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Complete validation result for code artifact"""
    overall_outcome: str  # confident_approval, confident_rejection, uncertain
    confidence_score: float  # 0.0 to 1.0
    rule_results: List[RuleMatch] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    uncertain_count: int = 0
    validation_time_ms: float = 0.0
    requires_llm: bool = False
    feedback_message: str = ""


@dataclass
class ValidationRule:
    """Single validation rule with pattern matching"""
    rule_id: str
    rule_name: str
    swea_type: SWEAType
    pattern: str  # Regex pattern to match
    pattern_type: str  # "must_have" or "must_not_have"
    confidence: float  # How confident we are in this rule (0.0 to 1.0)
    message: str  # Human-readable message
    suggestion: str = ""  # How to fix the issue
    enabled: bool = True
    
    def matches(self, code: str) -> Tuple[bool, Optional[int]]:
        """
        Check if pattern matches code
        
        Returns:
            (matches, line_number) tuple
        """
        if not self.enabled:
            return (True, None)  # Disabled rules always pass
        
        pattern = re.compile(self.pattern, re.MULTILINE | re.IGNORECASE)
        
        if self.pattern_type == "must_have":
            match = pattern.search(code)
            if match:
                line_num = code[:match.start()].count('\n') + 1
                return (True, line_num)
            return (False, None)
        
        elif self.pattern_type == "must_not_have":
            match = pattern.search(code)
            if match:
                line_num = code[:match.start()].count('\n') + 1
                return (False, line_num)
            return (True, None)
        
        return (True, None)


class ValidationRuleEngine:
    """
    Central validation engine with rule catalog and validation logic
    
    Supports:
    - Backend validation: FastAPI, SQLAlchemy, error handling
    - Database validation: primary keys, indexes, constraints
    - Frontend validation: Streamlit, form validation, error display
    - Test validation: pytest, lifecycle testing, cleanup
    - AST-based structural validation
    """
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {
            "backend": [],
            "database": [],
            "frontend": [],
            "test": []
        }
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize validation rule catalog"""
        # Backend rules (FastAPI + SQLAlchemy patterns)
        self.rules["backend"].extend([
            ValidationRule(
                rule_id="BE001",
                rule_name="context_manager_usage",
                swea_type=SWEAType.BACKEND,
                pattern=r"@contextmanager|with\s+\w+\s*\(",
                pattern_type="must_have",
                confidence=0.9,
                message="Backend code should use context managers for database sessions",
                suggestion="Add @contextmanager decorator or use 'with' statement for database sessions"
            ),
            ValidationRule(
                rule_id="BE002",
                rule_name="http_status_codes",
                swea_type=SWEAType.BACKEND,
                pattern=r"status_code\s*=\s*\d{3}|HTTPException|status\.\w+",
                pattern_type="must_have",
                confidence=0.85,
                message="Backend code should use proper HTTP status codes",
                suggestion="Use fastapi.status constants or HTTPException with status_code"
            ),
            ValidationRule(
                rule_id="BE003",
                rule_name="error_handling",
                swea_type=SWEAType.BACKEND,
                pattern=r"try\s*:|except\s+\w+|raise\s+\w+",
                pattern_type="must_have",
                confidence=0.8,
                message="Backend code should include error handling",
                suggestion="Add try-except blocks for database and validation errors"
            ),
            ValidationRule(
                rule_id="BE004",
                rule_name="response_models",
                swea_type=SWEAType.BACKEND,
                pattern=r"response_model\s*=|BaseModel|Schema",
                pattern_type="must_have",
                confidence=0.85,
                message="Backend endpoints should define response models",
                suggestion="Add response_model parameter to endpoint decorators"
            ),
            ValidationRule(
                rule_id="BE005",
                rule_name="dependency_injection",
                swea_type=SWEAType.BACKEND,
                pattern=r"Depends\(|def\s+get_\w+\(",
                pattern_type="must_have",
                confidence=0.75,
                message="Backend code should use dependency injection",
                suggestion="Use Depends() for database sessions and shared dependencies"
            ),
            ValidationRule(
                rule_id="BE006",
                rule_name="no_hardcoded_values",
                swea_type=SWEAType.BACKEND,
                pattern=r'(host\s*=\s*["\']localhost|port\s*=\s*\d{4}|password\s*=\s*["\'].+["\'])',
                pattern_type="must_not_have",
                confidence=0.95,
                message="Backend code should not contain hardcoded connection details",
                suggestion="Use environment variables or config files for connection details"
            ),
        ])
        
        # Database rules (SQL patterns)
        self.rules["database"].extend([
            ValidationRule(
                rule_id="DB001",
                rule_name="primary_key",
                swea_type=SWEAType.DATABASE,
                pattern=r"PRIMARY\s+KEY|SERIAL\s+PRIMARY\s+KEY|id\s+SERIAL",
                pattern_type="must_have",
                confidence=0.95,
                message="Database schema must define primary key",
                suggestion="Add PRIMARY KEY constraint to id column"
            ),
            ValidationRule(
                rule_id="DB002",
                rule_name="indexes",
                swea_type=SWEAType.DATABASE,
                pattern=r"CREATE\s+INDEX|INDEX\s+\w+|UNIQUE\s+INDEX",
                pattern_type="must_have",
                confidence=0.7,
                message="Database schema should include indexes for common queries",
                suggestion="Add CREATE INDEX statements for foreign keys and frequently queried columns"
            ),
            ValidationRule(
                rule_id="DB003",
                rule_name="foreign_key_constraints",
                swea_type=SWEAType.DATABASE,
                pattern=r"FOREIGN\s+KEY|REFERENCES\s+\w+",
                pattern_type="must_have",
                confidence=0.8,
                message="Database schema should define foreign key constraints",
                suggestion="Add FOREIGN KEY constraints for relationship columns"
            ),
            ValidationRule(
                rule_id="DB004",
                rule_name="not_null_constraints",
                swea_type=SWEAType.DATABASE,
                pattern=r"NOT\s+NULL",
                pattern_type="must_have",
                confidence=0.75,
                message="Database schema should use NOT NULL constraints appropriately",
                suggestion="Add NOT NULL to required columns"
            ),
            ValidationRule(
                rule_id="DB005",
                rule_name="no_sql_injection_risk",
                swea_type=SWEAType.DATABASE,
                pattern=r'f["\'].*SELECT.*\{|format\(.*SELECT|%s.*SELECT',
                pattern_type="must_not_have",
                confidence=0.99,
                message="Database code must not use string formatting in SQL queries",
                suggestion="Use parameterized queries or ORM methods instead"
            ),
        ])
        
        # Frontend rules (Streamlit patterns)
        self.rules["frontend"].extend([
            ValidationRule(
                rule_id="FE001",
                rule_name="form_validation",
                swea_type=SWEAType.FRONTEND,
                pattern=r"st\.error\(|st\.warning\(|if\s+not\s+\w+:",
                pattern_type="must_have",
                confidence=0.85,
                message="Frontend forms should include input validation",
                suggestion="Add validation checks and display errors with st.error()"
            ),
            ValidationRule(
                rule_id="FE002",
                rule_name="success_feedback",
                swea_type=SWEAType.FRONTEND,
                pattern=r"st\.success\(|st\.info\(",
                pattern_type="must_have",
                confidence=0.8,
                message="Frontend should provide success feedback",
                suggestion="Add st.success() message after successful operations"
            ),
            ValidationRule(
                rule_id="FE003",
                rule_name="error_display",
                swea_type=SWEAType.FRONTEND,
                pattern=r"except\s+\w+.*st\.error|try:.*st\.error",
                pattern_type="must_have",
                confidence=0.75,
                message="Frontend should display errors to users",
                suggestion="Wrap API calls in try-except and show errors with st.error()"
            ),
            ValidationRule(
                rule_id="FE004",
                rule_name="streamlit_imports",
                swea_type=SWEAType.FRONTEND,
                pattern=r"import\s+streamlit\s+as\s+st",
                pattern_type="must_have",
                confidence=0.95,
                message="Frontend code must import streamlit",
                suggestion="Add 'import streamlit as st' at the top"
            ),
            ValidationRule(
                rule_id="FE005",
                rule_name="no_hardcoded_urls",
                swea_type=SWEAType.FRONTEND,
                pattern=r'(http://localhost:\d+|https?://\d+\.\d+\.\d+\.\d+)',
                pattern_type="must_not_have",
                confidence=0.9,
                message="Frontend should not hardcode API URLs",
                suggestion="Use environment variables or config for API endpoints"
            ),
        ])
        
        # Test rules (pytest patterns)
        self.rules["test"].extend([
            ValidationRule(
                rule_id="TE001",
                rule_name="integration_lifecycle",
                swea_type=SWEAType.TEST,
                pattern=r"def\s+test_\w+_crud|def\s+test_create|def\s+test_read|def\s+test_update|def\s+test_delete",
                pattern_type="must_have",
                confidence=0.9,
                message="Integration tests should cover CRUD lifecycle",
                suggestion="Add test methods for create, read, update, delete operations"
            ),
            ValidationRule(
                rule_id="TE002",
                rule_name="error_case_testing",
                swea_type=SWEAType.TEST,
                pattern=r"test_\w+_error|test_\w+_invalid|test_\w+_not_found|assert.*raises",
                pattern_type="must_have",
                confidence=0.8,
                message="Tests should include error cases",
                suggestion="Add test cases for invalid inputs and error conditions"
            ),
            ValidationRule(
                rule_id="TE003",
                rule_name="cleanup",
                swea_type=SWEAType.TEST,
                pattern=r"@pytest\.fixture|yield|teardown|cleanup",
                pattern_type="must_have",
                confidence=0.85,
                message="Tests should include cleanup logic",
                suggestion="Use pytest fixtures with yield or add cleanup in finally blocks"
            ),
            ValidationRule(
                rule_id="TE004",
                rule_name="pytest_imports",
                swea_type=SWEAType.TEST,
                pattern=r"import\s+pytest",
                pattern_type="must_have",
                confidence=0.95,
                message="Test code must import pytest",
                suggestion="Add 'import pytest' at the top"
            ),
            ValidationRule(
                rule_id="TE005",
                rule_name="assertions",
                swea_type=SWEAType.TEST,
                pattern=r"assert\s+\w+",
                pattern_type="must_have",
                confidence=0.95,
                message="Test code must include assertions",
                suggestion="Add assert statements to verify expected behavior"
            ),
        ])
    
    def validate_code(self, code: str, swea_type: str) -> ValidationResult:
        """
        Validate code using rule-based patterns
        
        Args:
            code: Source code to validate
            swea_type: Type of SWEA (backend, database, frontend, test)
        
        Returns:
            ValidationResult with outcome and detailed rule matches
        """
        import time
        start_time = time.time()
        
        result = ValidationResult(
            overall_outcome="uncertain",
            confidence_score=0.0,
            rule_results=[],
            passed_count=0,
            failed_count=0,
            uncertain_count=0
        )
        
        # Get rules for this SWEA type
        rules = self.rules.get(swea_type, [])
        if not rules:
            result.overall_outcome = "uncertain"
            result.requires_llm = True
            result.feedback_message = f"No validation rules defined for {swea_type}"
            return result
        
        # Run each rule
        total_confidence = 0.0
        for rule in rules:
            passed, line_num = rule.matches(code)
            
            match = RuleMatch(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                passed=passed,
                confidence=rule.confidence,
                line_number=line_num,
                message=rule.message,
                suggestion=rule.suggestion
            )
            
            result.rule_results.append(match)
            
            if passed:
                result.passed_count += 1
                total_confidence += rule.confidence
            else:
                result.failed_count += 1
                total_confidence -= rule.confidence  # Negative contribution
        
        # Calculate overall confidence score
        result.confidence_score = total_confidence / len(rules) if rules else 0.0
        
        # Determine outcome based on confidence score
        if result.confidence_score >= 0.7:
            result.overall_outcome = "confident_approval"
            result.requires_llm = False
            result.feedback_message = f"Code passes {result.passed_count}/{len(rules)} validation rules"
        elif result.confidence_score <= -0.3:
            result.overall_outcome = "confident_rejection"
            result.requires_llm = False
            # Build detailed feedback
            failed_rules = [m for m in result.rule_results if not m.passed]
            feedback_lines = [f"Code validation failed ({len(failed_rules)} issues):"]
            for match in failed_rules:
                location = f" (line {match.line_number})" if match.line_number else ""
                feedback_lines.append(f"  - [{match.rule_id}] {match.message}{location}")
                if match.suggestion:
                    feedback_lines.append(f"    → {match.suggestion}")
            result.feedback_message = "\n".join(feedback_lines)
        else:
            result.overall_outcome = "uncertain"
            result.requires_llm = True
            result.feedback_message = f"Validation uncertain (score: {result.confidence_score:.2f}), requires LLM review"
        
        result.validation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def validate_code_structure(self, code: str) -> ValidationResult:
        """
        Validate code structure using AST analysis
        
        Checks:
        - Type hints on function parameters and return values
        - Docstrings on classes and functions
        - PEP 8 naming conventions (snake_case functions, PascalCase classes)
        
        Returns:
            ValidationResult with structural validation results
        """
        import time
        start_time = time.time()
        
        result = ValidationResult(
            overall_outcome="uncertain",
            confidence_score=0.0,
            rule_results=[]
        )
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result.overall_outcome = "confident_rejection"
            result.confidence_score = -1.0
            result.failed_count = 1
            result.feedback_message = f"Syntax error at line {e.lineno}: {e.msg}"
            result.validation_time_ms = (time.time() - start_time) * 1000
            return result
        
        # Check functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function naming (snake_case)
                if not self._is_snake_case(node.name) and not node.name.startswith('test_'):
                    result.rule_results.append(RuleMatch(
                        rule_id="ST001",
                        rule_name="function_naming",
                        passed=False,
                        confidence=0.8,
                        line_number=node.lineno,
                        message=f"Function '{node.name}' should use snake_case naming",
                        suggestion="Rename function to follow PEP 8 snake_case convention"
                    ))
                    result.failed_count += 1
                else:
                    result.passed_count += 1
                
                # Check for type hints
                has_type_hints = any(arg.annotation for arg in node.args.args)
                has_return_type = node.returns is not None
                
                if not has_type_hints or not has_return_type:
                    result.rule_results.append(RuleMatch(
                        rule_id="ST002",
                        rule_name="type_hints",
                        passed=False,
                        confidence=0.7,
                        line_number=node.lineno,
                        message=f"Function '{node.name}' should include type hints",
                        suggestion="Add type hints to parameters and return value"
                    ))
                    result.failed_count += 1
                else:
                    result.passed_count += 1
                
                # Check for docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    result.rule_results.append(RuleMatch(
                        rule_id="ST003",
                        rule_name="function_docstring",
                        passed=False,
                        confidence=0.6,
                        line_number=node.lineno,
                        message=f"Function '{node.name}' should have a docstring",
                        suggestion="Add docstring describing function purpose and parameters"
                    ))
                    result.failed_count += 1
                else:
                    result.passed_count += 1
            
            elif isinstance(node, ast.ClassDef):
                # Check class naming (PascalCase)
                if not self._is_pascal_case(node.name):
                    result.rule_results.append(RuleMatch(
                        rule_id="ST004",
                        rule_name="class_naming",
                        passed=False,
                        confidence=0.85,
                        line_number=node.lineno,
                        message=f"Class '{node.name}' should use PascalCase naming",
                        suggestion="Rename class to follow PEP 8 PascalCase convention"
                    ))
                    result.failed_count += 1
                else:
                    result.passed_count += 1
                
                # Check for class docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    result.rule_results.append(RuleMatch(
                        rule_id="ST005",
                        rule_name="class_docstring",
                        passed=False,
                        confidence=0.6,
                        line_number=node.lineno,
                        message=f"Class '{node.name}' should have a docstring",
                        suggestion="Add docstring describing class purpose"
                    ))
                    result.failed_count += 1
                else:
                    result.passed_count += 1
        
        # Calculate confidence score
        total_checks = result.passed_count + result.failed_count
        if total_checks > 0:
            result.confidence_score = (result.passed_count - result.failed_count) / total_checks
        
        # Determine outcome
        if result.confidence_score >= 0.5:
            result.overall_outcome = "confident_approval"
            result.requires_llm = False
            result.feedback_message = f"Code structure passes {result.passed_count}/{total_checks} checks"
        elif result.confidence_score <= -0.3:
            result.overall_outcome = "confident_rejection"
            result.requires_llm = False
            failed_rules = [m for m in result.rule_results if not m.passed]
            result.feedback_message = f"Code structure has {len(failed_rules)} issues"
        else:
            result.overall_outcome = "uncertain"
            result.requires_llm = True
            result.feedback_message = "Code structure validation uncertain, requires LLM review"
        
        result.validation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention"""
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention"""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def add_rule(self, rule: ValidationRule):
        """Add a new validation rule"""
        swea_type = rule.swea_type.value
        if swea_type in self.rules:
            self.rules[swea_type].append(rule)
    
    def update_rule(self, rule_id: str, **kwargs):
        """Update existing rule properties"""
        for swea_type, rules in self.rules.items():
            for rule in rules:
                if rule.rule_id == rule_id:
                    for key, value in kwargs.items():
                        if hasattr(rule, key):
                            setattr(rule, key, value)
                    return True
        return False
    
    def disable_rule(self, rule_id: str):
        """Disable a rule without removing it"""
        return self.update_rule(rule_id, enabled=False)
    
    def enable_rule(self, rule_id: str):
        """Enable a previously disabled rule"""
        return self.update_rule(rule_id, enabled=True)
    
    def list_rules(self, swea_type: Optional[str] = None) -> List[ValidationRule]:
        """List all rules, optionally filtered by SWEA type"""
        if swea_type:
            return self.rules.get(swea_type, [])
        
        all_rules = []
        for rules in self.rules.values():
            all_rules.extend(rules)
        return all_rules
    
    def get_rule_stats(self) -> Dict[str, int]:
        """Get statistics about validation rules"""
        stats = {}
        for swea_type, rules in self.rules.items():
            enabled = sum(1 for r in rules if r.enabled)
            disabled = sum(1 for r in rules if not r.enabled)
            stats[swea_type] = {
                "total": len(rules),
                "enabled": enabled,
                "disabled": disabled
            }
        return stats
