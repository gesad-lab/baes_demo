"""
BAES Core Package

Contains the core runtime components for the Business Autonomous Entities framework:
- Runtime kernels for orchestrating BAE and SWEA interactions
- Context store for preserving domain knowledge and agent memories
- Managed system manager for handling isolated system generation
"""

from baes.core.context_store import ContextStore

__all__ = [
    "ContextStore",
]
