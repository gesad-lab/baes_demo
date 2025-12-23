# RecognitionCache API Contract

## Overview
Internal API contract for the two-tier entity recognition cache system (in-memory + SQLite persistent).

## API Specification

### 1. Cache Write Operation

**Method**: `cache_write(request: str, recognition: EntityRecognition) -> None`

**Description**: Stores entity recognition result in both in-memory and SQLite caches.

**Request**:
```python
{
    "request": "Create a system to manage university students with name, enrollment date, and GPA",
    "recognition": {
        "detected_entity": "Student",
        "confidence_score": 0.95,
        "action_intent": "create",
        "attributes": [
            {"name": "name", "type": "string", "required": true},
            {"name": "enrollment_date", "type": "date", "required": true},
            {"name": "gpa", "type": "float", "required": true}
        ]
    }
}
```

**Response**: None (void)

**Side Effects**:
- Normalized key stored in in-memory dict (hot cache)
- Record inserted into SQLite recognition_cache table (cold cache)
- Timestamp set to current UTC time

**Errors**:
- `CacheWriteError`: If SQLite write fails (logs warning, continues with in-memory only)

**Performance**: <5ms (in-memory) + <50ms (SQLite write)

---

### 2. Cache Read Operation

**Method**: `cache_read(request: str) -> Optional[CachedRecognition]`

**Description**: Retrieves cached entity recognition result, checking in-memory first, then SQLite.

**Request**:
```python
{
    "request": "create student system with name enrollment gpa"  # Any variation
}
```

**Response**:
```python
{
    "normalized_request_key": "create student system name enrollment gpa",
    "detected_entity": "Student",
    "confidence_score": 0.95,
    "action_intent": "create",
    "timestamp": "2025-12-23T10:30:00Z",
    "hit_count": 3,
    "cache_version": 1
}
```

**Returns**: `CachedRecognition` if found, `None` if cache miss

**Side Effects**:
- `hit_count` incremented in both caches
- If found in SQLite only, promotes to in-memory cache

**Errors**: None (cache miss returns None, not error)

**Performance**: 
- In-memory hit: <1ms
- SQLite hit: <10ms
- Cache miss: <15ms (checks both)

---

### 3. Cache Cleanup Operation

**Method**: `cache_cleanup(max_age_days: int = 30) -> int`

**Description**: Removes cache entries older than specified age from SQLite.

**Request**:
```python
{
    "max_age_days": 30  # Default: 30 days
}
```

**Response**:
```python
{
    "deleted_count": 42  # Number of entries removed
}
```

**Side Effects**:
- Old entries deleted from SQLite
- In-memory cache refreshed (old entries evicted)

**Errors**:
- `CacheCleanupError`: If SQLite deletion fails

**Performance**: <100ms for up to 1000 entries

**Scheduling**: Called automatically on EnhancedRuntimeKernel startup

---

### 4. Cache Statistics Operation

**Method**: `cache_stats() -> CacheStatistics`

**Description**: Returns cache performance metrics.

**Request**: None

**Response**:
```python
{
    "in_memory_size": 150,      # Number of entries in hot cache
    "sqlite_size": 1247,        # Number of entries in cold cache
    "hit_rate": 0.62,           # Cache hit rate (0.0-1.0)
    "avg_hit_time_ms": 0.8,    # Average time for cache hits
    "miss_rate": 0.38,
    "total_hits": 3421,
    "total_misses": 2093,
    "oldest_entry": "2025-11-23T10:30:00Z",
    "newest_entry": "2025-12-23T15:45:12Z"
}
```

**Side Effects**: None (read-only)

**Performance**: <10ms

---

### 5. Cache Invalidation Operation

**Method**: `cache_invalidate(entity_name: Optional[str] = None) -> int`

**Description**: Manually invalidates cache entries, optionally filtered by entity name.

**Request**:
```python
{
    "entity_name": "Student"  # Optional, invalidates only Student entries
}
```

**Response**:
```python
{
    "invalidated_count": 8  # Number of entries removed
}
```

**Side Effects**:
- Matching entries removed from both in-memory and SQLite
- If `entity_name` is None, clears entire cache

**Errors**: None

**Performance**: <50ms

**Use Case**: Manual correction when cache contains incorrect recognition results

---

## Data Types

### CachedRecognition
```python
@dataclass
class CachedRecognition:
    normalized_request_key: str
    detected_entity: str
    confidence_score: float  # Range: 0.0-1.0
    action_intent: str       # Values: create, read, update, delete, list, custom
    timestamp: datetime
    hit_count: int
    cache_version: int
```

### CacheStatistics
```python
@dataclass
class CacheStatistics:
    in_memory_size: int
    sqlite_size: int
    hit_rate: float
    avg_hit_time_ms: float
    miss_rate: float
    total_hits: int
    total_misses: int
    oldest_entry: datetime
    newest_entry: datetime
```

---

## Error Handling

All cache operations follow fail-safe pattern:
- **Cache write failure**: Log warning, continue with in-memory only
- **Cache read failure**: Return cache miss (None), proceed to OpenAI
- **Cache cleanup failure**: Log error, retry on next startup

No cache operation should ever block entity generation.

---

## Concurrency

- **In-memory cache**: Thread-safe using `threading.Lock()`
- **SQLite cache**: WAL mode enabled for concurrent reads during writes
- **Async support**: All operations are sync (cache access <50ms doesn't justify async overhead)

---

## Monitoring

Cache operations emit structured logs:
```json
{
    "event": "cache_hit",
    "normalized_key": "create student system name enrollment gpa",
    "detected_entity": "Student",
    "hit_time_ms": 0.7,
    "cache_tier": "in-memory"
}
```

Alert conditions:
- Hit rate < 30% for 1 hour (indicates normalization issues)
- Avg hit time > 20ms for in-memory cache (indicates memory pressure)
- SQLite size > 10,000 entries (trigger aggressive cleanup)
