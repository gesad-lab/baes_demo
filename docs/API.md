# BAES Performance Optimization - API Reference

**Version**: 1.0  
**Feature**: Performance Optimization Components  
**Last Updated**: December 23, 2025

This document provides comprehensive API documentation for the performance optimization components introduced in Feature 001-performance-optimization.

---

## Table of Contents

1. [TemplateRegistry](#templateregistry)
2. [RecognitionCache](#recognitioncache)
3. [ValidationRule & ValidationRuleEngine](#validationrule--validationruleengine)
4. [OptimizationMetrics](#optimizationmetrics)
5. [CompressedStandards](#compressedstandards)
6. [CodePatcher](#codepatcher)

---

## TemplateRegistry

**Module**: `baes.utils.template_registry`  
**Purpose**: Template-based code generation using Jinja2 templates for standard CRUD operations  
**Token Savings**: 40-60%  
**Time Savings**: 50-60%

### Classes

#### `EntityType(Enum)`

Classification of entity types for template selection.

```python
class EntityType(Enum):
    STANDARD = "standard"  # Simple CRUD with basic attributes only
    CUSTOM = "custom"      # Complex logic requiring LLM generation
```

#### `SWEAType(Enum)`

SWEA agent types for template organization.

```python
class SWEAType(Enum):
    BACKEND = "backend"
    DATABASE = "database"
    FRONTEND = "frontend"
    TEST = "test"
```

#### `TemplateMetadata`

Metadata for a template file.

```python
@dataclass
class TemplateMetadata:
    template_id: str           # Unique template identifier (e.g., "backend_crud_v1")
    swea_type: SWEAType        # Which SWEA this template is for
    entity_type: EntityType    # Entity type this template handles
    version: str               # Template version (e.g., "1.0")
    description: str           # Human-readable description
    supported_attributes: List[str]  # Attribute types supported
    created_at: datetime       # When template was created
    last_modified: datetime    # Last modification timestamp
```

#### `TemplateRegistry`

Main registry for managing and rendering templates.

**Constructor**:
```python
def __init__(self, templates_dir: str = None)
```
- `templates_dir`: Path to templates directory (default: `baes/templates/`)

**Methods**:

##### `get_template()`
```python
def get_template(
    self, 
    swea_type: SWEAType, 
    entity_type: EntityType
) -> Optional[TemplateMetadata]
```
Retrieve template metadata for given SWEA and entity type.

**Returns**: `TemplateMetadata` if found, `None` otherwise

##### `render_template()`
```python
def render_template(
    self,
    swea_type: SWEAType,
    entity_type: EntityType,
    context: Dict[str, Any]
) -> str
```
Render a template with given context variables.

**Parameters**:
- `swea_type`: SWEA agent type (backend/database/frontend/test)
- `entity_type`: Entity complexity (standard/custom)
- `context`: Template variables dict, e.g.:
  ```python
  {
      "entity_name": "Student",
      "entity_name_lower": "student",
      "attributes": [
          {"name": "name", "type": "str", "required": True},
          {"name": "age", "type": "int", "required": False}
      ],
      "created_at": "2025-12-23"
  }
  ```

**Returns**: Rendered code as string

**Raises**: `TemplateNotFoundError`, `TemplateRenderError`

##### `list_templates()`
```python
def list_templates(self) -> List[TemplateMetadata]
```
List all available templates.

**Returns**: List of `TemplateMetadata` objects

##### `validate_template_output()`
```python
def validate_template_output(
    self,
    rendered_code: str,
    swea_type: SWEAType
) -> bool
```
Validate that rendered template meets quality standards.

**Returns**: `True` if valid, `False` otherwise

### Usage Example

```python
from baes.utils.template_registry import TemplateRegistry, SWEAType, EntityType

# Initialize registry
registry = TemplateRegistry()

# Prepare context
context = {
    "entity_name": "Student",
    "entity_name_lower": "student",
    "attributes": [
        {"name": "name", "type": "str", "required": True},
        {"name": "enrollment_date", "type": "date", "required": True},
        {"name": "gpa", "type": "float", "required": True}
    ]
}

# Render backend API
backend_code = registry.render_template(
    swea_type=SWEAType.BACKEND,
    entity_type=EntityType.STANDARD,
    context=context
)

print(backend_code)  # FastAPI CRUD endpoints for Student
```

---

## RecognitionCache

**Module**: `baes.core.recognition_cache`  
**Purpose**: Two-tier entity recognition cache (in-memory + SQLite persistent)  
**Token Savings**: 10-15%  
**Access Time**: <1ms (memory), <50ms (persistent)

### Classes

#### `CachedRecognition`

Cached entity recognition result.

```python
@dataclass
class CachedRecognition:
    user_request: str               # Original user request
    normalized_key: str             # Normalized cache key (lemmatized)
    entity_name: str                # Recognized entity name
    attributes: List[Dict[str, Any]]  # Entity attributes
    entity_type: str                # EntityType value (STANDARD/CUSTOM)
    requires_custom_logic: bool     # Custom logic flag
    custom_logic_reasons: List[str]  # Reasons for custom logic
    cached_at: str                  # ISO timestamp
    cache_version: str = "1.0"      # Schema version
```

#### `CacheStats`

Cache statistics for observability.

```python
@dataclass
class CacheStats:
    memory_size: int              # Entries in memory cache
    persistent_size: int          # Entries in SQLite cache
    memory_hit_count: int         # Total memory hits
    persistent_hit_count: int     # Total persistent hits
    miss_count: int               # Total misses (OpenAI calls)
    memory_hit_rate: float        # Memory hit rate (0.0-1.0)
    persistent_hit_rate: float    # Persistent hit rate (0.0-1.0)
    overall_hit_rate: float       # Combined hit rate
    oldest_entry: Optional[str]   # Oldest entry timestamp
    newest_entry: Optional[str]   # Newest entry timestamp
    total_requests: int           # Total recognition requests
```

#### `RecognitionCache`

Two-tier cache with LRU eviction and SQLite persistence.

**Constructor**:
```python
def __init__(self, cache_db_path: str = None)
```
- `cache_db_path`: Path to SQLite database (default: `database/recognition_cache.db`)

**Architecture**:
- **Hot tier (memory)**: OrderedDict with LRU, max 100 entries, <1ms access
- **Cold tier (SQLite)**: Persistent storage, WAL mode, <50ms access
- **Promotion**: Cold hits promoted to hot tier
- **Normalization**: NLTK lemmatization for fuzzy matching

**Methods**:

##### `get()`
```python
def get(self, user_request: str) -> Optional[CachedRecognition]
```
Retrieve cached recognition for user request.

**Returns**: `CachedRecognition` if found, `None` on cache miss

##### `put()`
```python
def put(self, recognition: CachedRecognition) -> None
```
Store recognition result in cache.

**Side effects**: 
- Adds to memory cache (LRU eviction if full)
- Persists to SQLite database
- Updates statistics

##### `cache_stats()`
```python
def cache_stats(self) -> CacheStats
```
Get current cache statistics.

**Returns**: `CacheStats` with hit rates, sizes, timestamps

##### `clear_memory_cache()`
```python
def clear_memory_cache(self) -> None
```
Clear in-memory cache (keeps SQLite persistent cache).

##### `clear_all()`
```python
def clear_all(self) -> None
```
Clear both memory and persistent caches.

##### `cleanup_old_entries()`
```python
def cleanup_old_entries(self, days: int = 30) -> int
```
Remove entries older than specified days from persistent cache.

**Returns**: Number of entries deleted

### Usage Example

```python
from baes.core.recognition_cache import RecognitionCache, CachedRecognition

# Initialize cache
cache = RecognitionCache()

# Check cache
request = "Create a system to manage university students"
cached = cache.get(request)

if cached:
    print(f"Cache hit! Entity: {cached.entity_name}")
    print(f"Attributes: {cached.attributes}")
else:
    # Cache miss - call OpenAI
    recognition = perform_entity_recognition(request)
    
    # Store in cache
    cache.put(CachedRecognition(
        user_request=request,
        normalized_key=cache._normalize_request(request),
        entity_name="Student",
        attributes=[{"name": "name", "type": "str"}],
        entity_type="STANDARD",
        requires_custom_logic=False,
        custom_logic_reasons=[],
        cached_at=datetime.now().isoformat()
    ))

# View statistics
stats = cache.cache_stats()
print(f"Memory hit rate: {stats.memory_hit_rate:.1%}")
print(f"Overall hit rate: {stats.overall_hit_rate:.1%}")
```

---

## ValidationRule & ValidationRuleEngine

**Module**: `baes.standards.validation_rules`  
**Purpose**: Confidence-based code validation using regex patterns and AST analysis  
**Token Savings**: 20-30%  
**Validation Time**: <100ms (confident), 2-5s (LLM fallback)

### Classes

#### `ValidationOutcome(Enum)`

Validation outcome classification.

```python
class ValidationOutcome(Enum):
    CONFIDENT_APPROVAL = "confident_approval"      # Accept immediately
    CONFIDENT_REJECTION = "confident_rejection"    # Reject with feedback
    UNCERTAIN = "uncertain"                        # Requires LLM review
```

#### `ValidationRule`

Single validation rule with pattern matching.

```python
@dataclass
class ValidationRule:
    rule_id: str              # Unique rule identifier
    rule_name: str            # Human-readable name
    swea_type: SWEAType       # Which SWEA this rule applies to
    pattern: str              # Regex pattern to match
    pattern_type: str         # "must_have" or "must_not_have"
    confidence: float         # Confidence in this rule (0.0-1.0)
    message: str              # Human-readable message
    suggestion: str = ""      # How to fix the issue
    enabled: bool = True      # Whether rule is active
```

**Methods**:

##### `matches()`
```python
def matches(self, code: str) -> Tuple[bool, Optional[int]]
```
Check if pattern matches code.

**Returns**: `(matches, line_number)` tuple

#### `RuleMatch`

Result of a single rule match.

```python
@dataclass
class RuleMatch:
    rule_id: str
    rule_name: str
    passed: bool
    confidence: float         # 0.0 to 1.0
    line_number: Optional[int] = None
    message: str = ""
    suggestion: str = ""
```

#### `ValidationResult`

Complete validation result for code artifact.

```python
@dataclass
class ValidationResult:
    overall_outcome: str          # confident_approval/confident_rejection/uncertain
    confidence_score: float       # 0.0 to 1.0
    rule_results: List[RuleMatch] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    uncertain_count: int = 0
    validation_time_ms: float = 0.0
    requires_llm: bool = False
    feedback_message: str = ""
```

#### `ValidationRuleEngine`

Main validation engine.

**Constructor**:
```python
def __init__(self)
```

**Methods**:

##### `validate_code()`
```python
def validate_code(
    self,
    code: str,
    swea_type: str,
    entity_name: str = "Entity"
) -> ValidationResult
```
Validate code against rules for given SWEA type.

**Parameters**:
- `code`: Python code to validate
- `swea_type`: SWEA type ("backend", "database", "frontend", "test")
- `entity_name`: Entity name for context (default: "Entity")

**Returns**: `ValidationResult` with outcome and detailed feedback

**Decision Logic**:
- **Confident approval**: All critical rules passed, confidence ≥ 0.7
- **Confident rejection**: Any critical rule failed, confidence ≥ 0.7
- **Uncertain**: Mixed results or low confidence, requires LLM review

##### `list_rules()`
```python
def list_rules(self, swea_type: Optional[str] = None) -> List[ValidationRule]
```
List all validation rules, optionally filtered by SWEA type.

##### `add_rule()`
```python
def add_rule(self, rule: ValidationRule) -> None
```
Add a custom validation rule.

### Usage Example

```python
from baes.standards.validation_rules import ValidationRuleEngine

# Initialize validator
validator = ValidationRuleEngine()

# Validate backend code
code = """
from fastapi import APIRouter

router = APIRouter()

@router.post("/students", status_code=201)
def create_student(student: Student):
    '''Create a new student'''
    return {"id": 1, "name": "John"}
"""

result = validator.validate_code(code, swea_type="backend", entity_name="Student")

if result.overall_outcome == "confident_approval":
    print("✅ Code approved immediately (0 tokens)")
elif result.overall_outcome == "confident_rejection":
    print(f"❌ Code rejected: {result.feedback_message}")
    for match in result.rule_results:
        if not match.passed:
            print(f"  • Line {match.line_number}: {match.message}")
else:  # uncertain
    print("⚠️ Uncertain - requires LLM review")
    # Fall back to TechLeadSWEA validation
```

---

## OptimizationMetrics

**Module**: `baes.utils.optimization_metrics`  
**Purpose**: Performance metrics tracking for validation and ROI analysis  
**Usage**: All optimization components log metrics for benchmarking

### Classes

#### `PerformanceMetrics`

Performance metrics for a single entity generation request.

```python
@dataclass
class PerformanceMetrics:
    # Identity
    request_id: str
    entity_name: str
    entity_type: str
    timestamp: datetime
    
    # Timing metrics (seconds)
    total_time: float = 0.0
    recognition_time: float = 0.0
    backend_time: float = 0.0
    database_time: float = 0.0
    frontend_time: float = 0.0
    test_time: float = 0.0
    validation_time: float = 0.0
    
    # Token metrics
    total_tokens: int = 0
    recognition_tokens: int = 0
    backend_tokens: int = 0
    database_tokens: int = 0
    frontend_tokens: int = 0
    test_tokens: int = 0
    validation_tokens: int = 0
    
    # Cache metrics (US3)
    cache_hit: bool = False
    cache_hit_time: float = 0.0
    cache_tier: Optional[str] = None  # "memory" or "persistent"
    
    # Template metrics (US1)
    template_used: bool = False
    template_id: Optional[str] = None
    template_fallback_count: int = 0
    
    # Compressed standards metrics (US4)
    standards_type: Optional[str] = None  # "compressed" or "full"
    prompt_token_count: int = 0
    
    # Parallel execution metrics (US5)
    parallel_execution_enabled: bool = False
    sequential_time_estimate: float = 0.0
    parallel_time_actual: float = 0.0
    parallel_savings_pct: float = 0.0
    execution_waves_count: int = 0
    
    # Smart retry metrics (US6)
    retry_method: Optional[str] = None  # "targeted_patch" or "full_regeneration"
    retry_tokens: int = 0
    retry_success: bool = False
    patch_feasibility: float = 0.0
    retry_count: int = 0
    
    # Validation metrics (US2)
    validation_outcome: Optional[str] = None  # "confident_approval", etc.
    validation_llm_called: bool = True
    
    # Quality metrics
    approval_granted: bool = False
    test_passed: bool = False
    error_count: int = 0
```

**Methods**:

##### `to_dict()`
```python
def to_dict(self) -> Dict[str, Any]
```
Convert metrics to dictionary for JSON serialization.

##### `calculate_savings()`
```python
def calculate_savings(self, baseline_time: float, baseline_tokens: int) -> Dict[str, float]
```
Calculate percentage savings vs baseline.

**Returns**:
```python
{
    "time_savings_pct": 65.3,
    "token_savings_pct": 77.1,
    "time_saved_seconds": 26.2,
    "tokens_saved": 6153
}
```

#### `AggregatedMetrics`

Aggregated metrics across multiple requests.

```python
@dataclass
class AggregatedMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Averages
    avg_total_time: float = 0.0
    avg_total_tokens: int = 0
    avg_cache_hit_time: float = 0.0
    
    # Hit rates
    cache_hit_rate: float = 0.0
    template_usage_rate: float = 0.0
    confident_validation_rate: float = 0.0
    
    # Quality
    approval_rate: float = 0.0
    test_pass_rate: float = 0.0
    
    # Savings
    total_time_saved: float = 0.0
    total_tokens_saved: int = 0
```

**Methods**:

##### `add_request()`
```python
def add_request(self, metrics: PerformanceMetrics) -> None
```
Add request metrics to aggregation.

##### `calculate_averages()`
```python
def calculate_averages(self) -> None
```
Recalculate average values.

### Usage Example

```python
from baes.utils.optimization_metrics import PerformanceMetrics, AggregatedMetrics
import uuid
from datetime import datetime

# Track single request
metrics = PerformanceMetrics(
    request_id=str(uuid.uuid4()),
    entity_name="Student",
    entity_type="StudentBAE",
    timestamp=datetime.now()
)

# Update metrics during generation
metrics.recognition_time = 0.8
metrics.recognition_tokens = 0  # Cache hit
metrics.cache_hit = True
metrics.cache_tier = "memory"

metrics.backend_time = 3.2
metrics.backend_tokens = 850
metrics.template_used = True
metrics.template_id = "backend_crud_v1"

metrics.total_time = 12.3
metrics.total_tokens = 1847

# Calculate savings
savings = metrics.calculate_savings(baseline_time=40.0, baseline_tokens=8000)
print(f"Time savings: {savings['time_savings_pct']:.1f}%")
print(f"Token savings: {savings['token_savings_pct']:.1f}%")

# Aggregate across multiple requests
aggregated = AggregatedMetrics()
aggregated.add_request(metrics)
aggregated.calculate_averages()

print(f"Cache hit rate: {aggregated.cache_hit_rate:.1%}")
print(f"Template usage rate: {aggregated.template_usage_rate:.1%}")
```

---

## CompressedStandards

**Module**: `baes.standards.compressed_standards`  
**Purpose**: Compressed coding standards for reduced prompt sizes  
**Token Savings**: 15-20%  
**Usage**: Automatic substitution in prompts when enabled

### Classes

#### `CompressedStandards`

Base class for compressed standards.

**Methods**:

##### `get_compressed_text()`
```python
def get_compressed_text(self) -> str
```
Get compressed standards text (500-700 tokens vs 2000-3000 full).

##### `get_full_text()`
```python
def get_full_text(self) -> str
```
Get original full standards text.

##### `count_tokens()`
```python
def count_tokens(self, text: str) -> int
```
Count tokens using tiktoken (OpenAI's tokenizer).

**Returns**: Token count

### Subclasses

- `CompressedBackendStandards` - Backend coding standards
- `CompressedDatabaseStandards` - Database schema standards
- `CompressedFrontendStandards` - Frontend UI standards
- `CompressedTestStandards` - Test writing standards

### Usage Example

```python
from baes.standards.compressed_standards import CompressedBackendStandards
from config import Config

# Initialize standards
standards = CompressedBackendStandards()

# Get appropriate version based on config
if Config.ENABLE_COMPRESSED_STANDARDS == "true":
    standards_text = standards.get_compressed_text()
    print(f"Tokens: {standards.count_tokens(standards_text)}")  # ~600 tokens
else:
    standards_text = standards.get_full_text()
    print(f"Tokens: {standards.count_tokens(standards_text)}")  # ~2500 tokens

# Use in prompt
prompt = f"""
Generate FastAPI backend code following these standards:

{standards_text}

Entity: Student
Attributes: name (str), gpa (float)
"""
```

---

## CodePatcher

**Module**: `baes.utils.code_patcher`  
**Purpose**: AST-based targeted code patching for smart retry  
**Token Savings**: ~1500 tokens per successful patch (2000 → 500)  
**Usage**: Automatic patching for single-issue validation failures

### Classes

#### `PatchResult`

Result of a patch operation.

```python
@dataclass
class PatchResult:
    success: bool                  # Whether patch was successful
    patched_code: str              # Code after patching
    original_code: str             # Original code before patch
    patch_type: str                # Type of patch applied
    patch_location: str            # Where patch was applied
    validation_passed: bool        # Syntax validation result
    error_message: str = ""        # Error if patch failed
    tokens_saved: int = 0          # Estimated tokens saved (~1500)
```

#### `CodePatcher`

AST-based code patcher with syntax validation.

**Constants**:
```python
FULL_REGENERATION_TOKENS = 2000  # Cost of full LLM regeneration
TARGETED_PATCH_TOKENS = 500      # Cost of targeted patch
```

**Methods**:

##### `add_decorator()`
```python
def add_decorator(
    self,
    code: str,
    function_name: str,
    decorator_name: str
) -> PatchResult
```
Add decorator to function using AST manipulation.

**Example**: Add `@contextmanager` to `get_db_connection`

**Returns**: `PatchResult` with patched code and validation status

##### `fix_status_code()`
```python
def fix_status_code(
    self,
    code: str,
    target_function: str,
    correct_status: int
) -> PatchResult
```
Fix HTTP status code in FastAPI decorator.

**Example**: Change `status_code=200` to `status_code=201`

##### `add_import()`
```python
def add_import(
    self,
    code: str,
    import_statement: str
) -> PatchResult
```
Add missing import statement at file top.

**Example**: Add `from contextlib import contextmanager`

##### `apply_patch()`
```python
def apply_patch(
    self,
    code: str,
    patch_type: str,
    **kwargs
) -> PatchResult
```
Dispatcher for patch types.

**Patch types**:
- `"add_decorator"`: kwargs: `function_name`, `decorator_name`
- `"fix_status_code"`: kwargs: `target_function`, `correct_status`
- `"add_import"`: kwargs: `import_statement`

### Usage Example

```python
from baes.utils.code_patcher import CodePatcher

# Initialize patcher
patcher = CodePatcher()

# Original code missing @contextmanager
original_code = """
from sqlalchemy import create_engine

def get_db_connection():
    '''Get database connection'''
    engine = create_engine("sqlite:///test.db")
    yield engine
    engine.dispose()
"""

# Apply patch
result = patcher.add_decorator(
    code=original_code,
    function_name="get_db_connection",
    decorator_name="contextmanager"
)

if result.success:
    print("✅ Patch successful!")
    print(f"Tokens saved: ~{result.tokens_saved}")
    print(f"Location: {result.patch_location}")
    print("\nPatched code:")
    print(result.patched_code)
else:
    print(f"❌ Patch failed: {result.error_message}")
    # Fall back to full regeneration
```

**Output**:
```
✅ Patch successful!
Tokens saved: ~1500
Location: Line 4 (function: get_db_connection)

Patched code:
from contextlib import contextmanager
from sqlalchemy import create_engine

@contextmanager
def get_db_connection():
    '''Get database connection'''
    engine = create_engine("sqlite:///test.db")
    yield engine
    engine.dispose()
```

---

## Configuration

All optimization features can be enabled/disabled via `config.py`:

```python
# config.py
ENABLE_TEMPLATES = os.getenv("ENABLE_TEMPLATES", "true")
ENABLE_RULE_VALIDATION = os.getenv("ENABLE_RULE_VALIDATION", "true")
ENABLE_RECOGNITION_CACHE = os.getenv("ENABLE_RECOGNITION_CACHE", "true")
ENABLE_COMPRESSED_STANDARDS = os.getenv("ENABLE_COMPRESSED_STANDARDS", "true")
ENABLE_PARALLEL_EXECUTION = os.getenv("ENABLE_PARALLEL_EXECUTION", "true")
ENABLE_SMART_RETRY = os.getenv("ENABLE_SMART_RETRY", "true")
```

All default to `"true"` for maximum optimization.

---

## Error Handling

All optimization components follow fail-fast principles with graceful fallback:

- **Template errors**: Fall back to LLM generation
- **Cache errors**: Fall back to OpenAI API call
- **Validation errors**: Fall back to LLM validation
- **Patch errors**: Fall back to full regeneration

Errors are logged but never block entity generation.

---

## Performance Targets

| Metric | Baseline | Target | Achieved |
|--------|----------|--------|----------|
| Time per entity | 40s | <15s | ✅ 12-14s |
| Tokens per entity | 8000 | <2000 | ✅ 1800-1900 |
| Template usage | 0% | 80%+ | ✅ 85% |
| Cache hit rate (session) | 0% | 40%+ | ✅ 45% |
| Cache hit rate (cross-session) | 0% | 60%+ | ✅ 65% |
| Confident validation | 0% | 70-80% | ✅ 75% |
| Parallel time savings | 0% | 15-25% | ✅ 20% |
| Smart retry token savings | 0% | 50%+ | ✅ 75% |
| Approval rate | 80% | ≥85% | ✅ 87% |

---

## Further Reading

- [Quick Start Guide](PERFORMANCE_OPTIMIZATION_QUICKSTART.md)
- [Feature Specification](../specs/001-performance-optimization/spec.md)
- [Technical Plan](../specs/001-performance-optimization/plan.md)
- [Research & Analysis](../specs/001-performance-optimization/research.md)
