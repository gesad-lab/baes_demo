# Data Model: Performance Optimization Components

**Feature**: BAES Framework Performance Optimization  
**Version**: 1.0  
**Last Updated**: December 23, 2025

## Overview
This document defines the data models, schemas, and structures for all new components introduced by the performance optimization feature.

---

## 1. RecognitionCache

### Purpose
Two-tier cache (in-memory + SQLite persistent) for storing entity recognition results to avoid redundant OpenAI calls.

### Schema

#### Python Class Definition
```python
@dataclass
class CachedRecognition:
    """Represents a cached entity recognition result."""
    
    normalized_request_key: str  # Normalized/lemmatized user request
    detected_entity: str          # Entity type (Student, Course, Teacher, etc.)
    confidence_score: float       # Recognition confidence (0.0-1.0)
    action_intent: str            # Action type (create, read, update, delete, list)
    timestamp: datetime          # When cached
    hit_count: int = 0           # Number of times this cache entry was used
    cache_version: int = 1       # Cache format version for migration
```

#### SQLite Schema
```sql
CREATE TABLE IF NOT EXISTS recognition_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_request_key TEXT NOT NULL UNIQUE,
    detected_entity TEXT NOT NULL,
    confidence_score REAL NOT NULL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    action_intent TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    hit_count INTEGER DEFAULT 0,
    cache_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_lookup 
ON recognition_cache(normalized_request_key, timestamp);

CREATE INDEX IF NOT EXISTS idx_cache_cleanup 
ON recognition_cache(timestamp);

PRAGMA user_version = 1;
PRAGMA journal_mode = WAL;
```

### Relationships
- **Parent**: EntityRecognizer (owner of cache)
- **Children**: None

### Validation Rules
1. `normalized_request_key` must be non-empty string
2. `confidence_score` must be float in range [0.0, 1.0]
3. `action_intent` must be one of: create, read, update, delete, list, custom
4. `timestamp` must be valid ISO 8601 datetime
5. `hit_count` must be non-negative integer
6. `cache_version` must be positive integer

### State Transitions
```
[New Entry] --cache_write()--> [Cached] --cache_hit()--> [Used] (hit_count++)
                                 |                           |
                                 |                           v
                                 +---------evict()------> [Expired]
```

### Lifecycle
- **Creation**: First time a user request is processed and entity recognized
- **Update**: hit_count incremented on cache hit
- **Expiration**: Entries older than 30 days auto-evicted on cleanup
- **Migration**: cache_version mismatch triggers re-recognition and cache update

---

## 2. ValidationRule

### Purpose
Pattern-based validation rules for confidence-based code review, enabling fast approval/rejection without LLM calls.

### Schema

#### Python Class Definition
```python
@dataclass
class ValidationRule:
    """Defines a pattern-based validation rule for code quality checks."""
    
    rule_id: str                    # Unique identifier (e.g., "context_manager_pattern")
    description: str                # Human-readable description
    category: str                   # Rule category (backend, frontend, database, test)
    required_patterns: List[str]    # Regex patterns that MUST be present for approval
    prohibited_patterns: List[str]  # Regex patterns that MUST NOT be present
    uncertainty_triggers: List[str] # Patterns that force LLM fallback
    confidence_threshold: float     # Min confidence for auto-approval (default 0.95)
    enabled: bool = True           # Rule can be disabled without deletion

class ValidationResult:
    """Result of applying a ValidationRule to code."""
    
    rule_id: str
    outcome: str  # "confident_approval", "confident_rejection", "uncertain"
    confidence: float
    matched_patterns: List[str]
    failed_patterns: List[str]
    reason: str  # Explanation of outcome
```

### Example Rules

#### Backend: Context Manager Pattern
```python
ValidationRule(
    rule_id="backend_context_manager",
    description="Database operations must use context managers",
    category="backend",
    required_patterns=[
        r'@contextmanager',
        r'def\s+get_db\s*\(\):',
        r'try:\s*\n\s+yield\s+db',
        r'finally:\s*\n\s+db\.close\(\)'
    ],
    prohibited_patterns=[
        r'db\s*=\s*SessionLocal\(\)(?!\s*\n\s*try:)'  # DB without try/finally
    ],
    uncertainty_triggers=[
        r'@contextmanager.*@contextmanager',  # Nested decorators
        r'yield\s+.*if.*else'  # Conditional yield
    ],
    confidence_threshold=0.95
)
```

#### Backend: HTTP Status Codes
```python
ValidationRule(
    rule_id="backend_http_status",
    description="REST endpoints must use correct HTTP status codes",
    category="backend",
    required_patterns=[
        r'@router\.post\(.*status_code\s*=\s*status\.HTTP_201_CREATED',  # POST = 201
        r'@router\.delete\(.*status_code\s*=\s*status\.HTTP_204_NO_CONTENT'  # DELETE = 204
    ],
    prohibited_patterns=[
        r'@router\.post\(.*status_code\s*=\s*200',  # POST should not be 200
        r'@router\.delete\(.*status_code\s*=\s*200'  # DELETE should not be 200
    ],
    uncertainty_triggers=[
        r'status_code\s*=\s*get_status_code\(',  # Dynamic status computation
    ],
    confidence_threshold=0.90
)
```

### Relationships
- **Parent**: TechLeadSWEA (uses rules for validation)
- **Storage**: Loaded from `baes/standards/validation_rules.py`

### Validation Rules
1. `rule_id` must be unique across all rules
2. `required_patterns` and `prohibited_patterns` must be valid regex
3. `confidence_threshold` must be in range [0.0, 1.0]
4. At least one of `required_patterns` or `prohibited_patterns` must be non-empty

---

## 3. TemplateRegistry

### Purpose
Manages Jinja2 templates for code generation, handling template selection, rendering, and version tracking.

### Schema

#### Python Class Definition
```python
@dataclass
class TemplateMetadata:
    """Metadata about a code generation template."""
    
    template_id: str          # Unique identifier (e.g., "backend_model_crud")
    template_path: str        # Relative path in baes/templates/
    entity_types: List[str]   # Entity types supported (["Student", "Course"] or ["*"])
    swea_type: str           # SWEA that uses template (backend, database, frontend, test)
    version: str             # Template version (semver)
    description: str         # What the template generates
    requires_custom_logic: bool = False  # If True, only for standard CRUD

class TemplateInput:
    """Input data for template rendering."""
    
    entity_name: str              # Entity name (Student, Course, etc.)
    attributes: List[Dict]        # [{name: str, type: str, required: bool, default: Any}]
    business_rules: List[str]     # Business rule descriptions
    relationships: List[Dict]     # [{related_entity: str, type: str, field_name: str}]
    standards_context: str        # Compressed standards to follow

class TemplateOutput:
    """Rendered template output."""
    
    generated_code: str
    template_id: str
    template_version: str
    warnings: List[str]  # Any issues during rendering
    fallback_used: bool  # True if LLM fallback was needed
```

### Template Catalog

#### Backend Templates
```python
templates = {
    "backend_model_crud": TemplateMetadata(
        template_id="backend_model_crud",
        template_path="backend/model_crud.py.j2",
        entity_types=["*"],  # Works for any entity
        swea_type="backend",
        version="1.0.0",
        description="SQLAlchemy model + Pydantic schema for standard CRUD entity"
    ),
    "backend_routes_crud": TemplateMetadata(
        template_id="backend_routes_crud",
        template_path="backend/routes_crud.py.j2",
        entity_types=["*"],
        swea_type="backend",
        version="1.0.0",
        description="FastAPI routes for create, read, update, delete, list operations"
    )
}
```

#### Database Templates
```python
templates = {
    "database_schema_crud": TemplateMetadata(
        template_id="database_schema_crud",
        template_path="database/schema_crud.sql.j2",
        entity_types=["*"],
        swea_type="database",
        version="1.0.0",
        description="SQLite CREATE TABLE with indexes for standard CRUD"
    )
}
```

#### Frontend Templates
```python
templates = {
    "frontend_streamlit_form": TemplateMetadata(
        template_id="frontend_streamlit_form",
        template_path="frontend/streamlit_form.py.j2",
        entity_types=["*"],
        swea_type="frontend",
        version="1.0.0",
        description="Streamlit form for create/update with validation"
    ),
    "frontend_streamlit_table": TemplateMetadata(
        template_id="frontend_streamlit_table",
        template_path="frontend/streamlit_table.py.j2",
        entity_types=["*"],
        swea_type="frontend",
        version="1.0.0",
        description="Streamlit table view with pagination and delete"
    )
}
```

#### Test Templates
```python
templates = {
    "test_integration_crud": TemplateMetadata(
        template_id="test_integration_crud",
        template_path="tests/integration_crud.py.j2",
        entity_types=["*"],
        swea_type="test",
        version="1.0.0",
        description="Pytest integration tests for full CRUD lifecycle"
    )
}
```

### Relationships
- **Parent**: SWEA agents (BackendSWEA, DatabaseSWEA, FrontendSWEA, TestSWEA)
- **Storage**: Templates stored in `baes/templates/` directory tree

### Validation Rules
1. `template_id` must be unique across all templates
2. `template_path` must reference existing file in baes/templates/
3. `version` must follow semver format (X.Y.Z)
4. `entity_types` must contain at least one element

---

## 4. OptimizationMetrics

### Purpose
Track performance metrics before/after optimization for validation and monitoring.

### Schema

#### Python Class Definition
```python
@dataclass
class PerformanceMetrics:
    """Performance metrics for a single entity generation."""
    
    request_id: str              # Unique request identifier
    entity_name: str             # Entity generated
    entity_type: str             # Entity class name
    timestamp: datetime
    
    # Timing metrics (seconds)
    total_time: float
    recognition_time: float
    backend_time: float
    database_time: float
    frontend_time: float
    test_time: float
    validation_time: float
    
    # Token metrics
    total_tokens: int
    recognition_tokens: int
    backend_tokens: int
    database_tokens: int
    frontend_tokens: int
    test_tokens: int
    validation_tokens: int
    
    # Cache metrics
    cache_hit: bool
    cache_hit_time: float
    
    # Template metrics
    template_used: bool
    template_id: Optional[str]
    template_fallback_count: int
    
    # Validation metrics
    validation_outcome: str  # confident_approval, confident_rejection, uncertain
    validation_llm_called: bool
    
    # Quality metrics
    approval_granted: bool
    test_passed: bool
    error_count: int

class AggregatedMetrics:
    """Aggregated metrics over multiple entity generations."""
    
    period: str  # "daily", "weekly", "monthly"
    start_date: date
    end_date: date
    total_requests: int
    
    # Average timing
    avg_total_time: float
    avg_tokens: float
    
    # Optimization effectiveness
    cache_hit_rate: float  # % of recognition requests served from cache
    template_usage_rate: float  # % of generations using templates
    confident_validation_rate: float  # % of validations without LLM
    
    # Quality assurance
    approval_rate: float  # % of generated code approved by TechLead
    test_pass_rate: float  # % of generated code passing integration tests
    
    # Savings calculations
    token_reduction_pct: float  # vs baseline (8000 tokens)
    time_reduction_pct: float   # vs baseline (40 seconds)
```

### Storage
- **Real-time**: Structured logs in `logs/optimization_metrics/`
- **Aggregated**: CSV exports for analysis in `logs/optimization_metrics/aggregated/`

### Relationships
- **Parent**: EnhancedRuntimeKernel (collects metrics during execution)
- **Consumers**: MetricsTracker utility, CLI reporting tools

### Validation Rules
1. All time values must be non-negative
2. All token counts must be non-negative integers
3. `cache_hit_rate`, `template_usage_rate` must be in range [0.0, 1.0]
4. `approval_rate`, `test_pass_rate` must be in range [0.0, 1.0]
5. `timestamp` must be valid ISO 8601 datetime

---

## 5. CompressedStandards

### Purpose
Condensed versions of full coding standards for token-efficient prompts.

### Schema

#### Python Class Definition
```python
@dataclass
class CompressedStandard:
    """Condensed coding standard for a specific SWEA type."""
    
    swea_type: str  # backend, database, frontend, test
    version: str    # Standard version (tracks changes)
    content: str    # Compressed standard text (~25 lines)
    token_count: int  # Approximate tokens
    full_standard_path: str  # Path to full standard if needed

# Example: BackendCompressedStandard
compressed_backend = CompressedStandard(
    swea_type="backend",
    version="1.0.0",
    content="""
# Backend Code Standards (Compressed)

## Context Management
@contextmanager
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

## HTTP Status Codes
POST = 201 Created
DELETE = 204 No Content

## Error Handling
try:
    operation()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise

## PEP 8
- Line length: 100 chars
- snake_case: functions/variables
- PascalCase: classes
- Type hints: all functions

## DRY
- Use base classes for common patterns
- Extract repeated logic to utils

## Response Models
def create_item(item: ItemCreate) -> ItemResponse:
    # Always return typed Pydantic models
""",
    token_count=~200,
    full_standard_path="baes/standards/backend_standards.py"
)
```

### Relationships
- **Parent**: BaseSWEA (injects compressed standards into prompts)
- **Fallback**: Full standards loaded if approval rate drops below 85%

### Validation Rules
1. `content` must be non-empty
2. `token_count` should be < 300 for effectiveness
3. `version` must follow semver format

---

## Entity Relationship Diagram

```
┌─────────────────────────┐
│  EnhancedRuntimeKernel  │
│  (orchestrator)         │
└───────────┬─────────────┘
            │
            ├──> PerformanceMetrics (collects)
            │
            ├──> EntityRecognizer
            │    └──> RecognitionCache (in-memory + SQLite)
            │
            ├──> BaseBae (interpret_business_request)
            │    └──> _detect_custom_logic()
            │
            ├──> BackendSWEA
            │    ├──> TemplateRegistry (uses)
            │    │    └──> TemplateMetadata
            │    └──> CompressedStandards (injects)
            │
            ├──> DatabaseSWEA
            │    ├──> TemplateRegistry
            │    └──> CompressedStandards
            │
            ├──> FrontendSWEA
            │    ├──> TemplateRegistry
            │    └──> CompressedStandards
            │
            ├──> TestSWEA
            │    ├──> TemplateRegistry
            │    └──> CompressedStandards
            │
            └──> TechLeadSWEA
                 └──> ValidationRule (applies)
```

---

## Data Model Changes Summary

| Component | Type | Lines of Code (Est.) | Dependencies |
|-----------|------|---------------------|--------------|
| RecognitionCache | New Class | ~300 | SQLite3, NLTK |
| ValidationRule | New Class | ~200 | re (regex), ast |
| TemplateRegistry | New Class | ~250 | Jinja2 |
| TemplateMetadata | New Dataclass | ~50 | None |
| OptimizationMetrics | New Dataclass | ~150 | datetime, json |
| CompressedStandards | New Dataclass | ~100 | None |
| **Total New Code** | | **~1050 LOC** | |
