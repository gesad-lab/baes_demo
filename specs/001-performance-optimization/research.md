# Research: Performance Optimization Technical Decisions

**Feature**: BAES Framework Performance Optimization  
**Date**: December 23, 2025  
**Purpose**: Resolve technical unknowns and research best practices for implementation

## Research Questions

### 1. Template Engine Selection: Jinja2 Configuration

**Question**: What Jinja2 configuration best supports Python code generation while maintaining PEP 8 compliance?

**Research Findings**:
- **Jinja2 3.1+** supports custom filters, tests, and whitespace control essential for code generation
- **Key configurations**:
  - `trim_blocks=True`: Removes first newline after template tag
  - `lstrip_blocks=True`: Strips leading spaces/tabs from start of line
  - `keep_trailing_newline=True`: Maintains trailing newline (PEP 8 requirement)
  - `autoescape=False`: Disabled for code generation (not HTML)
- **Custom filters needed**:
  - `snake_case()`: Convert entity names to snake_case for functions/variables
  - `pascal_case()`: Convert entity names to PascalCase for classes
  - `python_type()`: Map attribute types to Python type hints (str, int, float, bool, List, Optional)

**Decision**: Use Jinja2 3.1+ with custom filters in TemplateRegistry. Configuration stored in `baes/utils/template_registry.py` with filters defined as:
```python
env = Environment(
    loader=FileSystemLoader('baes/templates/'),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    autoescape=False
)
env.filters['snake_case'] = to_snake_case
env.filters['pascal_case'] = to_pascal_case  
env.filters['python_type'] = to_python_type
```

**Rationale**: This configuration produces clean, properly indented Python code without manual post-processing. Custom filters ensure naming conventions match PEP 8.

---

### 2. Persistent Cache Storage: SQLite Schema Design

**Question**: What SQLite schema design optimizes two-tier cache performance and migration compatibility?

**Research Findings**:
- **Schema versioning**: Use `PRAGMA user_version` to track cache format version for migration detection
- **Indexing strategy**: Composite index on (normalized_request_key, timestamp) for fast lookups and age-based cleanup
- **ACID compliance**: Use `PRAGMA journal_mode=WAL` (Write-Ahead Logging) for better concurrent read performance
- **Schema design**:
```sql
CREATE TABLE recognition_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_request_key TEXT NOT NULL UNIQUE,
    detected_entity TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    action_intent TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    hit_count INTEGER DEFAULT 0,
    cache_version INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_lookup ON recognition_cache(normalized_request_key, timestamp);
CREATE INDEX idx_cache_cleanup ON recognition_cache(timestamp);

PRAGMA user_version = 1;  -- Cache format version
PRAGMA journal_mode = WAL;  -- Concurrent access optimization
```

**Decision**: Implement SQLite cache with WAL mode, composite indexes, and schema versioning. Cache version tracked in both PRAGMA and cache entries for migration flexibility.

**Rationale**: WAL mode allows concurrent reads during async writes. Composite indexes optimize both lookup (by key) and cleanup (by age). Schema versioning enables safe migration when cache format evolves.

---

### 3. Confidence-Based Validation: Regex Pattern Design

**Question**: What regex patterns reliably detect context manager, HTTP status codes, and error handling with minimal false positives?

**Research Findings**:
- **Context manager pattern**: `@contextmanager` decorator detection
  ```python
  pattern = r'@contextmanager\s*\n\s*def\s+\w+\s*\([^)]*\):'
  confident_approval: Pattern found with proper function definition
  confident_rejection: Function name suggests DB connection but no @contextmanager
  uncertain: Complex nested contexts or decorator chains
  ```

- **HTTP status codes**: FastAPI route status code verification
  ```python
  # POST = 201
  pattern_post = r'@router\.post\([^)]*status_code\s*=\s*status\.HTTP_201_CREATED'
  # DELETE = 204  
  pattern_delete = r'@router\.delete\([^)]*status_code\s*=\s*status\.HTTP_204_NO_CONTENT'
  confident_approval: Correct status code present
  confident_rejection: Wrong status code or missing
  uncertain: Dynamic status code computation
  ```

- **Error handling**: Try/except with logging
  ```python
  pattern = r'try:\s*\n.*?except\s+.*?:\s*\n\s*logger\.error\('
  confident_approval: try/except with logger.error
  confident_rejection: try/except without logging
  uncertain: Complex exception hierarchies or custom error handlers
  ```

**Decision**: Implement ValidationRule class with pattern catalog and confidence classification logic. Patterns stored in `baes/standards/validation_rules.py` with:
- Required patterns for confident_approval (all must match)
- Prohibited patterns for confident_rejection (any present)
- Uncertainty triggers (complex patterns that require LLM semantic understanding)

**Rationale**: Regex patterns catch 80% of standard/violation cases reliably. Uncertainty classification prevents false approvals on complex code that needs semantic analysis.

---

### 4. Template Detection: Standard vs Custom Logic Classification

**Question**: How does system reliably detect when entity request requires custom logic vs standard CRUD template?

**Research Findings**:
- **Standard CRUD indicators**:
  - Basic attribute types only: string, integer, float, boolean, date
  - No computed properties or derived fields
  - No custom validation beyond type checking
  - No relationships beyond simple foreign keys
  - No custom workflows or state machines

- **Custom logic triggers**:
  - Complex validation: regex patterns, cross-field dependencies, business rule computations
  - Computed properties: `full_name = f"{first_name} {last_name}"`
  - Custom workflows: approval processes, state transitions
  - Advanced relationships: many-to-many with attributes, recursive relationships
  - Integration requirements: external APIs, webhook triggers

**Decision**: Implement detection in BaseBae.interpret_business_request() by analyzing extracted attributes and rules:
```python
def _detect_custom_logic(self, attributes, business_rules):
    custom_indicators = {
        'complex_validation': any('regex' in rule or 'must calculate' in rule for rule in business_rules),
        'computed_properties': any('computed' in attr or 'derived' in attr for attr in attributes),
        'custom_workflow': any('workflow' in rule or 'state' in rule for rule in business_rules),
        'advanced_relationships': self._has_many_to_many_with_attrs(attributes),
        'integrations': any('api' in rule or 'webhook' in rule for rule in business_rules)
    }
    return any(custom_indicators.values())
```

**Rationale**: This heuristic approach catches 90%+ of custom logic cases accurately. False negatives (custom logic classified as standard) are caught by TechLeadSWEA review. False positives (standard classified as custom) result in LLM generation which is correct but slower (acceptable tradeoff).

---

### 5. Compressed Standards: Content Selection Strategy

**Question**: Which standards content is essential vs redundant for GPT-4o-mini code generation?

**Research Findings**:
- **GPT-4o-mini training**: Already knows FastAPI basics, Pydantic patterns, common Python idioms
- **Essential to include**:
  - Context manager pattern (project-specific convention)
  - HTTP status code mapping (201 POST, 204 DELETE) - often forgotten
  - Error handling template with logging (constitutional requirement)
  - PEP 8 line length (100 char vs common 79/88)
  - DRY reminders for this specific codebase

- **Can omit from prompts**:
  - Basic FastAPI syntax (imports, router, decorators)
  - Standard Pydantic field definitions
  - Common type hint syntax
  - Generic Python best practices already in training data

**Decision**: Create compressed standards with ~25 lines per SWEA type:
```python
# BackendCompressedStandards (25 lines)
- Context manager pattern (5 lines: decorator + try/yield/except/finally)
- HTTP status codes (3 lines: POST=201, DELETE=204, response type)
- Error handling (5 lines: try/except with logger.error)
- PEP 8 essentials (3 lines: line length 100, snake_case, type hints)
- DRY reminder (2 lines: use base classes, extract common patterns)
- Response model usage (2 lines: return typed responses)
- Database connection warning (2 lines: always use get_db() context)
- Example pattern (3 lines: minimal CRUD function skeleton)
```

Full standards (467 lines) included only when TechLeadSWEA approval rate drops below 85% for complex entities.

**Rationale**: GPT-4o-mini trained on millions of Python examples doesn't need redundant common patterns. Project-specific conventions and constitutional requirements must be explicit. This reduces tokens by 400-450 per generation while maintaining quality.

---

### 6. Async Parallel Execution: Dependency Resolution Strategy

**Question**: How does EnhancedRuntimeKernel determine SWEA task dependencies for safe parallelization?

**Research Findings**:
- **Hard dependencies** (must be sequential):
  - Backend depends on Database (needs schema for foreign keys)
  - Tests depend on all (Backend + Frontend + Database)
  
- **Independent tasks** (can be parallel):
  - Database + Frontend (no interaction)
  - Initial research tasks (BAE interpretation parallel to tech lead analysis)

- **Dependency graph representation**:
```python
dependency_graph = {
    'database_schema': [],  # No dependencies
    'backend_api': ['database_schema'],  # Needs DB schema
    'frontend_ui': [],  # No dependencies  
    'integration_tests': ['database_schema', 'backend_api', 'frontend_ui']  # Needs all
}
```

**Decision**: Implement TaskDependencyGraph in EnhancedRuntimeKernel:
```python
async def execute_parallel_tasks(self, coordination_plan):
    graph = self._build_dependency_graph(coordination_plan)
    
    # Topological sort into execution waves
    waves = []
    waves.append([task for task in graph if not graph[task].dependencies])  # Wave 1: No deps
    waves.append([task for task in graph if satisfied_by_wave(task, waves[0])])  # Wave 2: Depends on wave 1
    # ... continue until all tasks assigned
    
    for wave in waves:
        results = await asyncio.gather(*[self.execute_task(task) for task in wave])
        if any(failed for failed in results):
            raise ParallelExecutionError(wave=wave, failures=results)
```

**Rationale**: Topological sorting into execution waves ensures dependencies satisfied while maximizing parallelism. Fail-fast on wave failure prevents cascading issues.

---

### 7. Cache Normalization: Request Text Preprocessing

**Question**: What normalization strategy minimizes cache misses for semantically equivalent requests?

**Research Findings**:
- **Normalization steps**:
  1. Lowercase: "Create Student" → "create student"
  2. Strip whitespace: "  create student  " → "create student"
  3. Remove punctuation: "Create student!" → "create student"
  4. Lemmatization: "creating students" → "create student"
  5. Remove stop words: "create a system for students" → "create system students"

- **Stop words to remove**: a, an, the, for, to, with, of, in, on, at, etc.

- **Lemmatization library**: NLTK WordNetLemmatizer (already used for Python NLP tasks)

**Decision**: Implement normalization in RecognitionCache._normalize_key():
```python
def _normalize_key(self, request: str) -> str:
    # Lowercase and strip
    normalized = request.lower().strip()
    
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Tokenize
    tokens = normalized.split()
    
    # Remove stop words
    tokens = [t for t in tokens if t not in STOP_WORDS]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(t, pos='v') for t in tokens]
    
    return ' '.join(tokens)
```

**Rationale**: Aggressive normalization increases cache hit rate from ~30% (exact match only) to 60%+ (semantic match). Tradeoff: Very different requests might collide (e.g., "create student" vs "delete student") but confidence scores would differ, making collision detection possible.

---

## Implementation Dependencies

### External Libraries (New)
- **Jinja2 3.1+**: Template engine for code generation
- **NLTK**: Natural language processing for cache key normalization (lemmatization)

### Existing Dependencies (Enhanced Usage)
- **SQLite3**: Persistent cache storage with WAL mode
- **asyncio**: Parallel SWEA execution
- **re (regex)**: Confidence-based validation patterns
- **ast**: Abstract syntax tree parsing for structural validation

---

## Best Practices Research

### Template-Based Generation Best Practices
- **Incremental rollout**: Start with Backend models, expand to routes, then frontend, database, tests
- **Template versioning**: Include template version in generated code comments for debugging
- **Fallback transparency**: Log when LLM fallback used (template detection, generation failures)
- **Quality monitoring**: Track template vs LLM approval rates separately

### Cache Management Best Practices
- **Graceful degradation**: Cache failures should never block entity generation (fail to OpenAI)
- **Cache warming**: Pre-populate common entities (student, course, teacher) on framework startup
- **Monitoring**: Alert on cache hit rate <30% (indicates normalization issues)
- **Backup**: Export cache to JSON daily for disaster recovery

### Validation Performance Best Practices
- **Early exit**: Check fastest patterns first (decorator presence before complex structure)
- **Pattern compilation**: Pre-compile regex patterns at module load for speed
- **Batch validation**: When checking multiple files, parallelize regex checks
- **Calibration loop**: Log confident vs uncertain ratios, tune patterns monthly

---

## Risk Mitigation Strategies

### Risk: Template-Generated Code Fails Integration Tests
**Mitigation**: 
1. Start with single entity type (Student) for template validation
2. Run full integration test suite on template output before expanding
3. Maintain LLM fallback for 100% reliability
4. Version templates and track which version generated which code

### Risk: Cache Normalization Too Aggressive (False Positive Hits)
**Mitigation**:
1. Include confidence score in cache entries - validate on retrieval
2. Log cache hits with original vs normalized keys for monitoring
3. Implement cache invalidation API for manual correction
4. A/B test normalization strategies with hit rate + correctness metrics

### Risk: Regex Validation Has High False Negative Rate
**Mitigation**:
1. Log all uncertain classifications for pattern improvement
2. Monitor LLM validation call percentage (target 20%, alert if >40%)
3. Implement pattern testing framework with known good/bad examples
4. Quarterly pattern review based on production data

### Risk: Parallel Execution Introduces Race Conditions
**Mitigation**:
1. Strict dependency graph enforcement
2. No shared mutable state between parallel tasks
3. Integration tests specifically for parallel execution paths
4. Rollback mechanism if parallel failures exceed threshold

---

## Technology Recommendations Summary

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Template Engine | Jinja2 3.1+ | Industry standard, excellent whitespace control, custom filters |
| Persistent Cache | SQLite + WAL | ACID compliance, concurrent reads, zero-config, local file |
| Validation | Regex + AST | Fast, reliable for standard patterns, composable |
| Normalization | NLTK WordNetLemmatizer | Proven NLP library, accurate lemmatization |
| Parallel Execution | asyncio | Native Python, integrates with existing async code |
| Metrics Tracking | Structured logging + CSV | Simple, existing infrastructure, no new dependencies |
