"""
Software Engineering Autonomous Agents (SWEAs) Package

This package contains SWEA implementations that are coordinated by BAEs
to perform technical software engineering tasks while maintaining
semantic coherence with domain entities.
"""

from .database_swea import DatabaseSWEA
from .frontend_swea import FrontendSWEA
from .programmer_swea import ProgrammerSWEA

__all__ = ["ProgrammerSWEA", "FrontendSWEA", "DatabaseSWEA"]
