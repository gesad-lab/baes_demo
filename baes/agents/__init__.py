"""
BAES Agents Package

This package contains the base agent architecture.
BAEs have been moved to domain_entities/ and SWEAs to swea_agents/
for better architectural organization.

This module maintains the base agent class and backward compatibility.
"""

import sys

# Expose this package as top-level 'agents' for backward compatibility in tests
sys.modules.setdefault("agents", sys.modules[__name__])

# Base agent class (remains in agents/)
from .base_agent import BaseAgent

# Note: BAEs and SWEAs are now imported from their specific packages:
# - domain_entities.academic.student_bae import StudentBae
# - swea_agents.programmer_swea import ProgrammerSWEA
# This prevents circular imports while maintaining clean architecture

__all__ = [
    "BaseAgent",
]
