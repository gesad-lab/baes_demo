"""
BAE Standards Package

This package contains unified code generation and validation standards
used across all SWEA agents to ensure consistency and reduce retry failures.

The standards follow validation rules format with moderate granularity,
organized by functionality for clear separation of concerns.
"""

from .backend_standards import BackendStandards
from .base_standards import BaseStandards

__all__ = ["BaseStandards", "BackendStandards"]
