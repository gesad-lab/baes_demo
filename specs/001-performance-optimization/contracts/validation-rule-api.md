# ValidationRule API Contract

## Overview
Internal API contract for confidence-based code validation used by TechLeadSWEA to approve/reject generated code without LLM calls.

## API Specification

### 1. Validate Code

**Method**: `validate_code(code: str, swea_type: str, rules: List[str]) -> ValidationResult`

**Description**: Validates generated code against pattern-based rules, returning confidence-based outcome.

**Request**:
```python
{
    "code": """
@contextmanager
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.post("/students/", status_code=status.HTTP_201_CREATED, response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    try:
        db_student = Student(**student.dict())
        db.add(db_student)
        db.commit()
        return StudentResponse.from_orm(db_student)
    except Exception as e:
        logger.error(f"Failed to create student: {e}")
        raise
""",
    "swea_type": "backend",
    "rules": ["backend_context_manager", "backend_http_status", "backend_error_handling"]
}
```

**Response**:
```python
{
    "overall_outcome": "confident_approval",
    "overall_confidence": 0.96,
    "rule_results": [
        {
            "rule_id": "backend_context_manager",
            "outcome": "confident_approval",
            "confidence": 0.98,
            "matched_patterns": ["@contextmanager", "def get_db", "try:", "yield db", "finally:", "db.close()"],
            "failed_patterns": [],
            "reason": "Context manager pattern correctly implemented with try/yield/finally"
        },
        {
            "rule_id": "backend_http_status",
            "outcome": "confident_approval",
            "confidence": 0.95,
            "matched_patterns": ["@router.post", "status_code=status.HTTP_201_CREATED"],
            "failed_patterns": [],
            "reason": "POST endpoint correctly uses 201 Created status code"
        },
        {
            "rule_id": "backend_error_handling",
            "outcome": "confident_approval",
            "confidence": 0.95,
            "matched_patterns": ["try:", "except Exception", "logger.error"],
            "failed_patterns": [],
            "reason": "Error handling with logging present"
        }
    ],
    "requires_llm_review": false,
    "approval_recommendation": "approve"
}
```

**Outcome Logic**:
- **confident_approval**: All required patterns matched, no prohibited patterns, no uncertainty triggers (confidence ≥ 0.90)
- **confident_rejection**: Required patterns missing OR prohibited patterns present (confidence ≥ 0.90)
- **uncertain**: Uncertainty triggers detected OR confidence < 0.90 (requires LLM fallback)

**Performance**: <20ms for typical code (200 lines, 3 rules)

---

### 2. Get Rule

**Method**: `get_rule(rule_id: str) -> ValidationRule`

**Description**: Retrieves specific validation rule by ID.

**Request**:
```python
{
    "rule_id": "backend_context_manager"
}
```

**Response**:
```python
{
    "rule_id": "backend_context_manager",
    "description": "Database operations must use context managers",
    "category": "backend",
    "required_patterns": [
        "@contextmanager",
        "def\\s+get_db\\s*\\(\\):",
        "try:\\s*\\n\\s+yield\\s+db",
        "finally:\\s*\\n\\s+db\\.close\\(\\)"
    ],
    "prohibited_patterns": [
        "db\\s*=\\s*SessionLocal\\(\\)(?!\\s*\\n\\s*try:)"
    ],
    "uncertainty_triggers": [
        "@contextmanager.*@contextmanager",
        "yield\\s+.*if.*else"
    ],
    "confidence_threshold": 0.95,
    "enabled": true
}
```

**Performance**: <1ms (in-memory lookup)

---

### 3. List Rules

**Method**: `list_rules(category: Optional[str] = None, enabled_only: bool = True) -> List[ValidationRule]`

**Description**: Lists all validation rules, optionally filtered by category.

**Request**:
```python
{
    "category": "backend",
    "enabled_only": true
}
```

**Response**:
```python
[
    {
        "rule_id": "backend_context_manager",
        "description": "Database operations must use context managers",
        "category": "backend",
        "enabled": true
    },
    {
        "rule_id": "backend_http_status",
        "description": "REST endpoints must use correct HTTP status codes",
        "category": "backend",
        "enabled": true
    },
    {
        "rule_id": "backend_error_handling",
        "description": "All database operations must have error handling with logging",
        "category": "backend",
        "enabled": true
    }
]
```

**Performance**: <5ms

---

### 4. Add Rule

**Method**: `add_rule(rule: ValidationRule) -> None`

**Description**: Adds new validation rule to registry.

**Request**:
```python
{
    "rule": {
        "rule_id": "backend_pagination",
        "description": "List endpoints must implement pagination with skip/limit parameters",
        "category": "backend",
        "required_patterns": [
            "@router\\.get.*response_model=List",
            "skip:\\s*int\\s*=\\s*0",
            "limit:\\s*int\\s*=\\s*100"
        ],
        "prohibited_patterns": [
            "\\.all\\(\\)(?!\\[skip:)"
        ],
        "uncertainty_triggers": [
            "cursor.*pagination"
        ],
        "confidence_threshold": 0.90,
        "enabled": true
    }
}
```

**Response**: None (void)

**Side Effects**:
- Rule added to registry
- Patterns validated (regex syntax check)

**Errors**:
- `DuplicateRuleError`: If rule_id already exists
- `InvalidPatternError`: If regex pattern invalid

**Performance**: <10ms

---

### 5. Update Rule

**Method**: `update_rule(rule_id: str, updates: Dict[str, Any]) -> None`

**Description**: Updates existing validation rule.

**Request**:
```python
{
    "rule_id": "backend_context_manager",
    "updates": {
        "confidence_threshold": 0.98,
        "required_patterns": [
            "@contextmanager",
            "def\\s+get_db\\s*\\(\\):",
            "try:\\s*\\n\\s+yield\\s+db",
            "finally:\\s*\\n\\s+db\\.close\\(\\)",
            "db\\.rollback\\(\\)"  # NEW: Require explicit rollback on error
        ]
    }
}
```

**Response**: None (void)

**Side Effects**:
- Rule updated in registry
- Previous version backed up for rollback

**Performance**: <10ms

---

### 6. Disable Rule

**Method**: `disable_rule(rule_id: str) -> None`

**Description**: Temporarily disables rule without deleting it.

**Request**:
```python
{
    "rule_id": "backend_pagination"
}
```

**Response**: None (void)

**Side Effects**:
- Rule's `enabled` flag set to `false`
- Disabled rules skipped in validation

**Use Case**: Temporarily disable problematic rule while fixing patterns

**Performance**: <1ms

---

## Data Types

### ValidationRule
```python
@dataclass
class ValidationRule:
    rule_id: str
    description: str
    category: str  # backend, frontend, database, test
    required_patterns: List[str]  # Regex patterns that MUST be present
    prohibited_patterns: List[str]  # Regex patterns that MUST NOT be present
    uncertainty_triggers: List[str]  # Patterns that force LLM fallback
    confidence_threshold: float  # Min confidence for auto-approval (0.0-1.0)
    enabled: bool = True
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    overall_outcome: str  # "confident_approval", "confident_rejection", "uncertain"
    overall_confidence: float  # 0.0-1.0
    rule_results: List[RuleResult]
    requires_llm_review: bool
    approval_recommendation: str  # "approve", "reject", "review"
```

### RuleResult
```python
@dataclass
class RuleResult:
    rule_id: str
    outcome: str  # "confident_approval", "confident_rejection", "uncertain"
    confidence: float
    matched_patterns: List[str]
    failed_patterns: List[str]
    reason: str
```

---

## Validation Logic Flow

```
┌─────────────────────────┐
│  validate_code()        │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ For each enabled rule:  │
│ 1. Check required_patterns
│ 2. Check prohibited_patterns
│ 3. Check uncertainty_triggers
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ Calculate confidence:   │
│ - All required matched: +30%
│ - No prohibited found: +30%
│ - No uncertainty: +40%
│ = Total confidence
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ Determine outcome:      │
│ - confidence ≥ threshold
│   AND all required matched
│   AND no prohibited
│   → confident_approval  │
│ - confidence ≥ threshold
│   AND (missing required
│        OR has prohibited)
│   → confident_rejection │
│ - Otherwise
│   → uncertain (LLM)     │
└─────────────────────────┘
```

---

## Standard Rule Catalog

### Backend Rules
1. **backend_context_manager**: Database context manager pattern
2. **backend_http_status**: Correct HTTP status codes (POST=201, DELETE=204)
3. **backend_error_handling**: Try/except with logger.error
4. **backend_response_models**: Typed Pydantic response models
5. **backend_dependency_injection**: Depends(get_db) for database access

### Frontend Rules
1. **frontend_form_validation**: st.form with validation before submission
2. **frontend_error_display**: st.error() for error messages
3. **frontend_success_feedback**: st.success() for successful operations

### Database Rules
1. **database_primary_key**: Every table has PRIMARY KEY
2. **database_indexes**: Foreign keys have indexes
3. **database_constraints**: NOT NULL and CHECK constraints where appropriate

### Test Rules
1. **test_integration_lifecycle**: Tests full CRUD lifecycle
2. **test_error_cases**: Tests both success and failure paths
3. **test_cleanup**: Teardown/cleanup after tests

---

## Error Handling

Validation operations are fail-safe:
- **Pattern compilation error**: Log warning, skip rule, continue validation
- **Rule not found**: Log warning, skip rule, continue validation
- **Validation exception**: Log error, return `uncertain` outcome (LLM fallback)

Validation failures should never block code review.

---

## Performance Optimization

- **Pattern pre-compilation**: All regex patterns compiled at module load
- **Early exit**: Stop checking patterns after first uncertainty trigger
- **Parallel checking**: Multiple rules checked in parallel for large codebases
- **Pattern caching**: Compiled patterns cached in memory

---

## Monitoring

Validation operations emit structured logs:
```json
{
    "event": "validation_completed",
    "swea_type": "backend",
    "outcome": "confident_approval",
    "confidence": 0.96,
    "rules_checked": 3,
    "validation_time_ms": 18,
    "llm_required": false
}
```

Alert conditions:
- Uncertain rate > 40% (patterns need improvement)
- Avg validation time > 50ms (performance regression)
- Rule failures > 20% (template quality issue)
