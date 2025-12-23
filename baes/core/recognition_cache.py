"""
Entity Recognition Cache for BAES Framework
(Feature: 001-performance-optimization / US3)

Two-tier caching strategy:
1. In-memory cache (hot tier): OrderedDict with LRU eviction, max 100 entries
2. SQLite persistent cache (cold tier): WAL mode, ACID transactions, 30-day retention

Performance targets:
- In-memory hit: <1ms, 0 tokens, 40%+ hit rate per session
- Persistent hit: <50ms, 0 tokens, 60%+ hit rate cross-session
- Combined savings: 10-15% token reduction

Constitutional compliance:
- Observability: cache_stats() provides visibility into hit rates and sizes
- Fail-fast: Cache errors don't block recognition, graceful fallback to OpenAI
- Generator-first: Cache accelerates but never prevents entity generation
"""

import json
import logging
import sqlite3
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class CachedRecognition:
    """Cached entity recognition result"""
    user_request: str  # Original user request
    normalized_key: str  # Normalized cache key (lemmatized, lowercase)
    entity_name: str  # Recognized entity name
    attributes: List[Dict[str, Any]]  # Entity attributes
    entity_type: str  # EntityType value (STANDARD/CUSTOM)
    requires_custom_logic: bool  # Custom logic flag
    custom_logic_reasons: List[str]  # Reasons for custom logic
    cached_at: str  # ISO timestamp
    cache_version: str = "1.0"  # Schema version for invalidation


@dataclass
class CacheStats:
    """Cache statistics for observability"""
    memory_size: int  # Number of entries in memory cache
    persistent_size: int  # Number of entries in SQLite cache
    memory_hit_count: int  # Total memory cache hits
    persistent_hit_count: int  # Total persistent cache hits
    miss_count: int  # Total cache misses (OpenAI calls)
    memory_hit_rate: float  # Memory hit rate (0.0 to 1.0)
    persistent_hit_rate: float  # Persistent hit rate (0.0 to 1.0)
    overall_hit_rate: float  # Combined hit rate
    oldest_entry: Optional[str]  # Oldest entry timestamp (ISO format)
    newest_entry: Optional[str]  # Newest entry timestamp (ISO format)
    total_requests: int  # Total recognition requests


class RecognitionCache:
    """
    Two-tier entity recognition cache with LRU eviction and SQLite persistence
    
    Architecture:
    - Hot tier (memory): OrderedDict with LRU, max 100 entries, <1ms access
    - Cold tier (SQLite): Persistent storage, WAL mode, <50ms access
    - Promotion: Cold hits promoted to hot tier
    - Normalization: NLTK lemmatization + stop word removal for fuzzy matching
    - Thread-safe: All operations protected by threading.Lock
    """
    
    def __init__(self, cache_db_path: str = None):
        """
        Initialize recognition cache
        
        Args:
            cache_db_path: Path to SQLite database (default: database/recognition_cache.db)
        """
        self.cache_version = "1.0"
        self.max_memory_entries = 100
        self.retention_days = 30
        
        # In-memory cache (hot tier): LRU with OrderedDict
        self._memory_cache: OrderedDict[str, CachedRecognition] = OrderedDict()
        self._lock = threading.Lock()
        
        # Statistics tracking
        self._memory_hits = 0
        self._persistent_hits = 0
        self._misses = 0
        
        # SQLite persistent cache (cold tier)
        if cache_db_path is None:
            cache_db_path = str(Path("database") / "recognition_cache.db")
        self.cache_db_path = cache_db_path
        
        # Initialize SQLite database
        self._initialize_database()
        
        # Initialize NLTK for normalization
        self._initialize_nltk()
    
    def _initialize_database(self):
        """Initialize SQLite database with schema and indexes"""
        try:
            # Create database directory if it doesn't exist
            Path(self.cache_db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Set cache version
            cursor.execute(f"PRAGMA user_version={int(self.cache_version.replace('.', ''))}")
            
            # Create recognition_cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recognition_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    normalized_key TEXT NOT NULL UNIQUE,
                    user_request TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    attributes TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    requires_custom_logic INTEGER NOT NULL,
                    custom_logic_reasons TEXT NOT NULL,
                    cached_at TEXT NOT NULL,
                    cache_version TEXT NOT NULL,
                    last_accessed TEXT NOT NULL
                )
            """)
            
            # Create indexes for fast lookup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_normalized_key 
                ON recognition_cache(normalized_key)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_at 
                ON recognition_cache(cached_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_name 
                ON recognition_cache(entity_name)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Recognition cache initialized at {self.cache_db_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize recognition cache database: {e}")
            # Don't raise - cache is non-critical, allow fallback to OpenAI
    
    def _initialize_nltk(self):
        """Initialize NLTK components for cache key normalization"""
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer
            
            # Download required NLTK data if not present
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords', quiet=True)
            
            try:
                nltk.data.find('corpora/wordnet')
            except LookupError:
                nltk.download('wordnet', quiet=True)
            
            try:
                nltk.data.find('corpora/omw-1.4')
            except LookupError:
                nltk.download('omw-1.4', quiet=True)
            
            self._lemmatizer = WordNetLemmatizer()
            self._stop_words = set(stopwords.words('english'))
            
            logger.info("✅ NLTK initialized for cache normalization")
            
        except Exception as e:
            logger.warning(f"⚠️  NLTK initialization failed: {e}. Cache normalization will be simplified.")
            self._lemmatizer = None
            self._stop_words = set()
    
    def _normalize_key(self, user_request: str) -> str:
        """
        Normalize user request to create cache key
        
        Process:
        1. Lowercase
        2. Remove stop words (the, a, an, etc.)
        3. Lemmatize (students → student, created → create)
        4. Sort words alphabetically
        5. Join with spaces
        
        Examples:
            "Create a student system" → "create student system"
            "I need a students management" → "management need student"
            "Build student manager" → "build manager student"
        
        Args:
            user_request: Original user request
        
        Returns:
            Normalized cache key
        """
        try:
            # Lowercase
            text = user_request.lower()
            
            # Simple tokenization (split on non-alphanumeric)
            import re
            words = re.findall(r'\b\w+\b', text)
            
            # Remove stop words
            if self._stop_words:
                words = [w for w in words if w not in self._stop_words]
            
            # Lemmatize
            if self._lemmatizer:
                words = [self._lemmatizer.lemmatize(w) for w in words]
            
            # Sort alphabetically for order-independent matching
            words = sorted(words)
            
            # Join with spaces
            normalized = ' '.join(words)
            
            logger.debug(f"🔑 Normalized: '{user_request}' → '{normalized}'")
            
            return normalized
            
        except Exception as e:
            logger.warning(f"⚠️  Cache key normalization failed: {e}. Using lowercase fallback.")
            return user_request.lower()
    
    def cache_read(self, user_request: str) -> Optional[CachedRecognition]:
        """
        Read from cache (memory first, then persistent)
        
        Process:
        1. Normalize user request to cache key
        2. Check memory cache (hot tier)
        3. If miss, check SQLite cache (cold tier)
        4. If cold hit, promote to memory cache
        5. Update statistics
        
        Args:
            user_request: User's entity generation request
        
        Returns:
            CachedRecognition if hit, None if miss
        """
        start_time = time.time()
        normalized_key = self._normalize_key(user_request)
        
        # Check memory cache first (hot tier)
        with self._lock:
            if normalized_key in self._memory_cache:
                # LRU: Move to end (most recently used)
                self._memory_cache.move_to_end(normalized_key)
                cached = self._memory_cache[normalized_key]
                self._memory_hits += 1
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"🎯 Memory cache HIT for '{user_request}' "
                    f"(entity: {cached.entity_name}, time: {elapsed_ms:.1f}ms, 0 tokens)"
                )
                
                return cached
        
        # Check persistent cache (cold tier)
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_request, entity_name, attributes, entity_type, 
                       requires_custom_logic, custom_logic_reasons, cached_at, cache_version
                FROM recognition_cache
                WHERE normalized_key = ?
            """, (normalized_key,))
            
            row = cursor.fetchone()
            
            if row:
                # Persistent hit - reconstruct CachedRecognition
                cached = CachedRecognition(
                    user_request=row[0],
                    normalized_key=normalized_key,
                    entity_name=row[1],
                    attributes=json.loads(row[2]),
                    entity_type=row[3],
                    requires_custom_logic=bool(row[4]),
                    custom_logic_reasons=json.loads(row[5]),
                    cached_at=row[6],
                    cache_version=row[7]
                )
                
                # Check cache version compatibility
                if cached.cache_version != self.cache_version:
                    logger.warning(
                        f"⚠️  Cache version mismatch: {cached.cache_version} != {self.cache_version}. "
                        f"Invalidating entry for '{user_request}'"
                    )
                    cursor.execute("DELETE FROM recognition_cache WHERE normalized_key = ?", (normalized_key,))
                    conn.commit()
                    conn.close()
                    
                    with self._lock:
                        self._misses += 1
                    
                    return None
                
                # Update last_accessed timestamp
                cursor.execute("""
                    UPDATE recognition_cache 
                    SET last_accessed = ? 
                    WHERE normalized_key = ?
                """, (datetime.now().isoformat(), normalized_key))
                
                conn.commit()
                conn.close()
                
                # Promote to memory cache (cold → hot)
                with self._lock:
                    self._promote_to_memory(normalized_key, cached)
                    self._persistent_hits += 1
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"💾 Persistent cache HIT for '{user_request}' "
                    f"(entity: {cached.entity_name}, time: {elapsed_ms:.1f}ms, 0 tokens, promoted to memory)"
                )
                
                return cached
            else:
                conn.close()
                
                # Cache miss
                with self._lock:
                    self._misses += 1
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"❌ Cache MISS for '{user_request}' "
                    f"(time: {elapsed_ms:.1f}ms, will call OpenAI)"
                )
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Persistent cache read failed: {e}")
            with self._lock:
                self._misses += 1
            return None
    
    def cache_write(self, user_request: str, recognition_result: Dict[str, Any]):
        """
        Write recognition result to cache (immediate memory, async SQLite)
        
        Process:
        1. Normalize user request to cache key
        2. Create CachedRecognition object
        3. Write to memory cache immediately
        4. Write to SQLite cache (synchronously for simplicity)
        5. Enforce LRU eviction if memory cache exceeds max size
        
        Args:
            user_request: User's entity generation request
            recognition_result: EntityRecognizer output dict
        """
        try:
            normalized_key = self._normalize_key(user_request)
            
            # Create cached recognition object
            cached = CachedRecognition(
                user_request=user_request,
                normalized_key=normalized_key,
                entity_name=recognition_result.get("entity_name", "Unknown"),
                attributes=recognition_result.get("attributes", []),
                entity_type=recognition_result.get("entity_type", "STANDARD"),
                requires_custom_logic=recognition_result.get("requires_custom_logic", False),
                custom_logic_reasons=recognition_result.get("custom_logic_reasons", []),
                cached_at=datetime.now().isoformat(),
                cache_version=self.cache_version
            )
            
            # Write to memory cache (immediate)
            with self._lock:
                self._memory_cache[normalized_key] = cached
                
                # LRU eviction if exceeds max size
                if len(self._memory_cache) > self.max_memory_entries:
                    # Remove oldest (first item in OrderedDict)
                    evicted_key, evicted_value = self._memory_cache.popitem(last=False)
                    logger.debug(
                        f"🗑️  LRU eviction: '{evicted_value.user_request}' "
                        f"(memory cache full, {len(self._memory_cache)}/{self.max_memory_entries})"
                    )
            
            # Write to persistent cache (SQLite)
            try:
                conn = sqlite3.connect(self.cache_db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO recognition_cache 
                    (normalized_key, user_request, entity_name, attributes, entity_type, 
                     requires_custom_logic, custom_logic_reasons, cached_at, cache_version, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    normalized_key,
                    user_request,
                    cached.entity_name,
                    json.dumps(cached.attributes),
                    cached.entity_type,
                    int(cached.requires_custom_logic),
                    json.dumps(cached.custom_logic_reasons),
                    cached.cached_at,
                    cached.cache_version,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(
                    f"💾 Cached recognition for '{user_request}' "
                    f"(entity: {cached.entity_name}, memory + persistent)"
                )
                
            except Exception as e:
                logger.error(f"❌ Persistent cache write failed: {e}")
                # Memory cache still works, so don't fail the operation
                
        except Exception as e:
            logger.error(f"❌ Cache write failed: {e}")
            # Cache failure should not block recognition
    
    def _promote_to_memory(self, normalized_key: str, cached: CachedRecognition):
        """
        Promote persistent cache hit to memory cache (must hold lock)
        
        Args:
            normalized_key: Normalized cache key
            cached: CachedRecognition object to promote
        """
        self._memory_cache[normalized_key] = cached
        self._memory_cache.move_to_end(normalized_key)  # Mark as most recently used
        
        # LRU eviction if exceeds max size
        if len(self._memory_cache) > self.max_memory_entries:
            evicted_key, evicted_value = self._memory_cache.popitem(last=False)
            logger.debug(
                f"🗑️  LRU eviction on promotion: '{evicted_value.user_request}' "
                f"(memory cache full, {len(self._memory_cache)}/{self.max_memory_entries})"
            )
    
    def cache_cleanup(self):
        """
        Clean up expired cache entries (older than retention_days)
        
        Removes entries from SQLite that are older than retention_days (default: 30 days)
        Memory cache is managed via LRU eviction, so no cleanup needed there.
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_iso = cutoff_date.isoformat()
            
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM recognition_cache 
                WHERE cached_at < ?
            """, (cutoff_iso,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(
                    f"🗑️  Cache cleanup: Removed {deleted_count} entries older than {self.retention_days} days"
                )
            
        except Exception as e:
            logger.error(f"❌ Cache cleanup failed: {e}")
    
    def cache_stats(self) -> CacheStats:
        """
        Get cache statistics for observability
        
        Returns:
            CacheStats with hit rates, sizes, and timestamps
        """
        with self._lock:
            memory_size = len(self._memory_cache)
            memory_hits = self._memory_hits
            persistent_hits = self._persistent_hits
            misses = self._misses
        
        # Get persistent cache size and timestamps
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM recognition_cache")
            persistent_size = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(cached_at), MAX(cached_at) FROM recognition_cache")
            oldest, newest = cursor.fetchone()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to get persistent cache stats: {e}")
            persistent_size = 0
            oldest = None
            newest = None
        
        # Calculate hit rates
        total_requests = memory_hits + persistent_hits + misses
        
        if total_requests > 0:
            memory_hit_rate = memory_hits / total_requests
            persistent_hit_rate = (memory_hits + persistent_hits) / total_requests
            overall_hit_rate = (memory_hits + persistent_hits) / total_requests
        else:
            memory_hit_rate = 0.0
            persistent_hit_rate = 0.0
            overall_hit_rate = 0.0
        
        return CacheStats(
            memory_size=memory_size,
            persistent_size=persistent_size,
            memory_hit_count=memory_hits,
            persistent_hit_count=persistent_hits,
            miss_count=misses,
            memory_hit_rate=memory_hit_rate,
            persistent_hit_rate=persistent_hit_rate,
            overall_hit_rate=overall_hit_rate,
            oldest_entry=oldest,
            newest_entry=newest,
            total_requests=total_requests
        )
    
    def cache_invalidate(self, entity_name: Optional[str] = None):
        """
        Invalidate cache entries
        
        Args:
            entity_name: If provided, only invalidate entries for this entity.
                        If None, clear entire cache.
        """
        try:
            if entity_name:
                # Invalidate specific entity
                with self._lock:
                    # Remove from memory cache
                    keys_to_remove = [
                        key for key, cached in self._memory_cache.items()
                        if cached.entity_name.lower() == entity_name.lower()
                    ]
                    for key in keys_to_remove:
                        del self._memory_cache[key]
                
                # Remove from persistent cache
                conn = sqlite3.connect(self.cache_db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM recognition_cache 
                    WHERE LOWER(entity_name) = LOWER(?)
                """, (entity_name,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.info(
                    f"🗑️  Cache invalidated for entity '{entity_name}' "
                    f"({len(keys_to_remove)} memory, {deleted_count} persistent)"
                )
                
            else:
                # Clear entire cache
                with self._lock:
                    memory_count = len(self._memory_cache)
                    self._memory_cache.clear()
                
                conn = sqlite3.connect(self.cache_db_path)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM recognition_cache")
                persistent_count = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                logger.info(
                    f"🗑️  Entire cache cleared "
                    f"({memory_count} memory, {persistent_count} persistent)"
                )
                
        except Exception as e:
            logger.error(f"❌ Cache invalidation failed: {e}")
