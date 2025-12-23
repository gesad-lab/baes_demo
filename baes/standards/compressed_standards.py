"""
Compressed standards for token-efficient LLM prompts.

This module provides condensed versions of full coding standards documents,
reducing prompt token consumption by 15-20% while maintaining code quality.

Constitutional Compliance:
- PEP 8: Type hints, docstrings, proper formatting
- DRY: Centralizes standard compression logic
- Observability: Tracks token counts and compression effectiveness
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompressedStandard:
    """Condensed coding standard for a specific SWEA type.
    
    Contains essential rules only, omitting redundant information that
    LLMs already know from training data.
    
    Attributes:
        swea_type: SWEA type (backend, database, frontend, test)
        version: Standard version for tracking changes
        content: Compressed standard text (~25 lines)
        token_count: Approximate tokens (for monitoring)
        full_standard_path: Path to full standard if fallback needed
    """
    swea_type: str
    version: str
    content: str
    token_count: int
    full_standard_path: str


# Backend Compressed Standards
BACKEND_COMPRESSED = CompressedStandard(
    swea_type="backend",
    version="1.0.0",
    content="""
# Backend Code Standards (Compressed)

## Context Management (CRITICAL)
@contextmanager
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

## HTTP Status Codes (CRITICAL)
POST = 201 Created
DELETE = 204 No Content
GET/PUT = 200 OK

## Error Handling (CRITICAL)
try:
    operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise

## PEP 8 Essentials
- Line length: 100 chars
- Functions/variables: snake_case
- Classes: PascalCase
- Type hints: Required for all functions

## DRY Principle
- Use base classes for common patterns
- Extract repeated logic to utils
- Avoid code duplication

## Response Models
- Always return typed Pydantic models
- Use response_model parameter in routes
""",
    token_count=200,
    full_standard_path="baes/standards/backend_standards.py"
)


# Database Compressed Standards
DATABASE_COMPRESSED = CompressedStandard(
    swea_type="database",
    version="1.0.0",
    content="""
# Database Standards (Compressed)

## Primary Keys (CRITICAL)
- Every table MUST have PRIMARY KEY
- Use INTEGER AUTOINCREMENT for ID columns

## Indexes (CRITICAL)
- Foreign keys MUST have indexes
- Add indexes for frequently queried columns

## Constraints (CRITICAL)
- Use NOT NULL for required fields
- Use CHECK constraints for validation
- Use UNIQUE for unique fields

## Schema Pattern
CREATE TABLE entity_name (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entity_name ON entity_name(name);
""",
    token_count=150,
    full_standard_path="baes/standards/database_standards.py"
)


# Frontend Compressed Standards
FRONTEND_COMPRESSED = CompressedStandard(
    swea_type="frontend",
    version="1.0.0",
    content="""
# Frontend Standards (Compressed)

## Form Validation (CRITICAL)
- Use st.form for grouped inputs
- Validate BEFORE submission
- Show errors with st.error()

## User Feedback (CRITICAL)
- Success: st.success("Operation successful")
- Errors: st.error("Error: details")
- Warnings: st.warning("Warning: details")

## State Management
- Use st.session_state for persistence
- Clear state after operations
- Handle None/empty values

## Layout
- Use st.columns for horizontal layout
- Use st.expander for collapsible sections
- Consistent button placement
""",
    token_count=120,
    full_standard_path="baes/standards/frontend_standards.py"
)


# Test Compressed Standards
TEST_COMPRESSED = CompressedStandard(
    swea_type="test",
    version="1.0.0",
    content="""
# Test Standards (Compressed)

## Integration Testing (CRITICAL)
- Test full CRUD lifecycle
- Test success AND error paths
- Clean up after each test

## Test Structure
def test_entity_lifecycle():
    # Setup
    # Create
    # Read
    # Update
    # Delete
    # Verify cleanup

## Assertions
- Use specific assertions (assertEqual, assertIn)
- Include meaningful error messages
- Test edge cases

## Cleanup
- Delete created resources
- Close connections
- Reset state
""",
    token_count=110,
    full_standard_path="baes/standards/test_standards.py"
)


# Registry of all compressed standards
COMPRESSED_STANDARDS_REGISTRY = {
    "backend": BACKEND_COMPRESSED,
    "database": DATABASE_COMPRESSED,
    "frontend": FRONTEND_COMPRESSED,
    "test": TEST_COMPRESSED
}


def get_compressed_standard(swea_type: str) -> Optional[CompressedStandard]:
    """Retrieve compressed standard for SWEA type.
    
    Args:
        swea_type: SWEA type (backend, database, frontend, test)
        
    Returns:
        CompressedStandard if found, None otherwise
    """
    standard = COMPRESSED_STANDARDS_REGISTRY.get(swea_type.lower())
    if standard:
        logger.debug(
            f"Retrieved compressed standard for {swea_type}",
            extra={
                "swea_type": swea_type,
                "token_count": standard.token_count,
                "version": standard.version
            }
        )
    else:
        logger.warning(f"No compressed standard found for SWEA type: {swea_type}")
    return standard


def estimate_token_count(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken for OpenAI models.
    
    Falls back to simple heuristic (~4 characters per token) if tiktoken
    is not available.
    
    Args:
        text: Text to estimate tokens for
        model: OpenAI model name for encoding (default: gpt-4)
        
    Returns:
        Token count (accurate if tiktoken available, approximate otherwise)
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        logger.warning(
            "tiktoken not installed, using approximate token count (1 token ≈ 4 characters). "
            "Install tiktoken for accurate counts: pip install tiktoken"
        )
        return len(text) // 4
    except Exception as e:
        logger.warning(f"Failed to count tokens with tiktoken: {e}, using approximate count")
        return len(text) // 4


def calculate_compression_ratio(compressed_tokens: int, full_tokens: int) -> float:
    """Calculate compression ratio percentage.
    
    Args:
        compressed_tokens: Token count for compressed version
        full_tokens: Token count for full standard
        
    Returns:
        Compression percentage (e.g., 85.0 means 85% reduction)
    """
    if full_tokens == 0:
        return 0.0
    return ((full_tokens - compressed_tokens) / full_tokens) * 100.0
