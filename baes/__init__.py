"""
BAES - Business Autonomous Entities Framework

A framework for creating and managing Business Autonomous Entities (BAEs) that represent
domain entities as living, autonomous agents capable of runtime evolution and semantic
coherence between business vocabulary and technical artifacts.

This framework enables:
- Domain entity representation through autonomous agents
- Runtime system generation and evolution
- Semantic coherence between business and technical domains
- Cross-organizational reusability of domain knowledge
"""

__version__ = "0.1.0"
__author__ = "Anderson Martins Gomes"
__email__ = "your.email@example.com"
__description__ = "Business Autonomous Entities Framework for adaptive system generation"

# Core imports for easy access
from baes.agents.student_bae import StudentBAE
from baes.core.context_store import ContextStore

__all__ = [
    "StudentBAE",
    "ContextStore",
] 