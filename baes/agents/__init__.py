"""
BAES Agents Package

Contains Business Autonomous Entities (BAEs) and Software Engineering Autonomous Agents (SWEAs).

BAEs represent domain entities as autonomous agents that maintain semantic coherence
between business vocabulary and technical artifacts.

SWEAs handle technical implementation tasks under coordination of BAEs.
"""

import sys

# Expose this package as top-level 'agents' for backward compatibility in tests
sys.modules.setdefault('agents', sys.modules[__name__])

# BAE Agents (Business Autonomous Entities)
from .base_agent import BaseAgent
from .student_bae import StudentBAE

# Compatibility aliases for import resolution
BaseAgent = BaseAgent
StudentBAE = StudentBAE

__all__ = [
    "BaseAgent",
    "StudentBAE",
]
