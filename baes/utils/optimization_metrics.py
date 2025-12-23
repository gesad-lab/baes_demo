"""
Optimization metrics tracking for BAES Framework performance monitoring.

This module provides data classes and utilities for tracking performance metrics
before/after optimization, enabling validation and ROI analysis.

Constitutional Compliance:
- PEP 8: Type hints, docstrings, snake_case naming
- Observability: Comprehensive metrics collection for all optimization paths
- DRY: Centralized metrics structure reused across all components
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single entity generation request.
    
    Tracks timing, token consumption, optimization usage, and quality metrics
    to validate performance targets and identify optimization opportunities.
    
    Attributes:
        request_id: Unique identifier for the request
        entity_name: Name of entity generated (e.g., "Student")
        entity_type: Class name of entity (e.g., "StudentBAE")
        timestamp: When the request was processed
        
        # Timing metrics (seconds)
        total_time: Total wall-clock time for complete generation
        recognition_time: Time spent on entity recognition
        backend_time: Time spent generating backend code
        database_time: Time spent generating database schema
        frontend_time: Time spent generating frontend UI
        test_time: Time spent generating tests
        validation_time: Time spent on TechLeadSWEA validation
        
        # Token metrics
        total_tokens: Total OpenAI tokens consumed
        recognition_tokens: Tokens used for entity recognition
        backend_tokens: Tokens used for backend generation
        database_tokens: Tokens used for database generation
        frontend_tokens: Tokens used for frontend generation
        test_tokens: Tokens used for test generation
        validation_tokens: Tokens used for validation
        
        # Cache metrics
        cache_hit: Whether entity recognition was served from cache
        cache_hit_time: Time to retrieve from cache (milliseconds)
        cache_tier: Cache tier used (memory/persistent) if cache_hit is True
        
        # Template metrics
        template_used: Whether template-based generation was used
        template_id: ID of template used (if applicable)
        template_fallback_count: Number of times LLM fallback was needed
        
        # Compressed standards metrics
        standards_type: Type of standards used (compressed/full)
        prompt_token_count: Number of tokens in the prompt sent to LLM
        
        # Validation metrics
        template_used: Whether template-based generation was used
        template_id: ID of template used (if applicable)
        template_fallback_count: Number of times LLM fallback was needed
        
        # Validation metrics
        validation_outcome: Classification (confident_approval/confident_rejection/uncertain)
        validation_llm_called: Whether LLM was called for validation
        
        # Quality metrics
        approval_granted: Whether TechLeadSWEA approved the code
        test_passed: Whether integration tests passed
        error_count: Number of errors during generation
    """
    request_id: str
    entity_name: str
    entity_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Timing metrics (seconds)
    total_time: float = 0.0
    recognition_time: float = 0.0
    backend_time: float = 0.0
    database_time: float = 0.0
    frontend_time: float = 0.0
    test_time: float = 0.0
    validation_time: float = 0.0
    
    # Token metrics
    total_tokens: int = 0
    recognition_tokens: int = 0
    backend_tokens: int = 0
    database_tokens: int = 0
    frontend_tokens: int = 0
    test_tokens: int = 0
    validation_tokens: int = 0
    
    # Cache metrics
    cache_hit: bool = False
    cache_hit_time: float = 0.0
    cache_tier: Optional[str] = None  # "memory" or "persistent"
    
    # Template metrics
    template_used: bool = False
    template_id: Optional[str] = None
    template_fallback_count: int = 0
    
    # Compressed standards metrics (US4)
    standards_type: Optional[str] = None  # "compressed" or "full"
    prompt_token_count: int = 0
    
    # Validation metrics
    validation_outcome: str = "uncertain"  # confident_approval, confident_rejection, uncertain
    validation_llm_called: bool = False
    
    # Quality metrics
    approval_granted: bool = False
    test_passed: bool = False
    error_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary for logging/export."""
        return {
            "request_id": self.request_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp.isoformat(),
            "total_time": self.total_time,
            "recognition_time": self.recognition_time,
            "backend_time": self.backend_time,
            "database_time": self.database_time,
            "frontend_time": self.frontend_time,
            "test_time": self.test_time,
            "validation_time": self.validation_time,
            "total_tokens": self.total_tokens,
            "recognition_tokens": self.recognition_tokens,
            "backend_tokens": self.backend_tokens,
            "database_tokens": self.database_tokens,
            "frontend_tokens": self.frontend_tokens,
            "test_tokens": self.test_tokens,
            "validation_tokens": self.validation_tokens,
            "cache_hit": self.cache_hit,
            "cache_hit_time": self.cache_hit_time,
            "template_used": self.template_used,
            "template_id": self.template_id,
            "template_fallback_count": self.template_fallback_count,
            "validation_outcome": self.validation_outcome,
            "validation_llm_called": self.validation_llm_called,
            "approval_granted": self.approval_granted,
            "test_passed": self.test_passed,
            "error_count": self.error_count
        }


@dataclass
class AggregatedMetrics:
    """Aggregated performance metrics over multiple entity generations.
    
    Provides summary statistics for performance validation and monitoring.
    
    Attributes:
        period: Aggregation period ("daily", "weekly", "monthly")
        start_date: Start of aggregation period
        end_date: End of aggregation period
        total_requests: Number of entity generation requests
        
        # Average timing
        avg_total_time: Average total time per request (seconds)
        avg_tokens: Average tokens per request
        
        # Optimization effectiveness
        cache_hit_rate: Percentage of recognition requests served from cache
        template_usage_rate: Percentage of generations using templates
        confident_validation_rate: Percentage of validations without LLM
        
        # Quality assurance
        approval_rate: Percentage of generated code approved by TechLead
        test_pass_rate: Percentage of generated code passing integration tests
        
        # Savings calculations
        token_reduction_pct: Percentage reduction vs baseline (8000 tokens)
        time_reduction_pct: Percentage reduction vs baseline (40 seconds)
    """
    period: str  # "daily", "weekly", "monthly"
    start_date: date
    end_date: date
    total_requests: int
    
    # Average timing
    avg_total_time: float = 0.0
    avg_tokens: float = 0.0
    
    # Optimization effectiveness
    cache_hit_rate: float = 0.0  # 0.0-1.0
    template_usage_rate: float = 0.0  # 0.0-1.0
    confident_validation_rate: float = 0.0  # 0.0-1.0
    
    # Quality assurance
    approval_rate: float = 0.0  # 0.0-1.0
    test_pass_rate: float = 0.0  # 0.0-1.0
    
    # Savings calculations
    token_reduction_pct: float = 0.0  # percentage
    time_reduction_pct: float = 0.0  # percentage
    
    def to_dict(self) -> dict:
        """Convert aggregated metrics to dictionary for export."""
        return {
            "period": self.period,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_requests": self.total_requests,
            "avg_total_time": self.avg_total_time,
            "avg_tokens": self.avg_tokens,
            "cache_hit_rate": self.cache_hit_rate,
            "template_usage_rate": self.template_usage_rate,
            "confident_validation_rate": self.confident_validation_rate,
            "approval_rate": self.approval_rate,
            "test_pass_rate": self.test_pass_rate,
            "token_reduction_pct": self.token_reduction_pct,
            "time_reduction_pct": self.time_reduction_pct
        }


def calculate_token_reduction(current_tokens: int, baseline_tokens: int = 8000) -> float:
    """Calculate percentage token reduction vs baseline.
    
    Args:
        current_tokens: Actual tokens consumed
        baseline_tokens: Baseline token consumption (default 8000)
        
    Returns:
        Percentage reduction (e.g., 75.0 for 75% reduction)
    """
    if baseline_tokens == 0:
        return 0.0
    return ((baseline_tokens - current_tokens) / baseline_tokens) * 100.0


def calculate_time_reduction(current_time: float, baseline_time: float = 40.0) -> float:
    """Calculate percentage time reduction vs baseline.
    
    Args:
        current_time: Actual time taken (seconds)
        baseline_time: Baseline time (default 40 seconds)
        
    Returns:
        Percentage reduction (e.g., 60.0 for 60% reduction)
    """
    if baseline_time == 0:
        return 0.0
    return ((baseline_time - current_time) / baseline_time) * 100.0


def log_performance_metrics(metrics: PerformanceMetrics) -> None:
    """Log performance metrics as structured log entry.
    
    Args:
        metrics: Performance metrics to log
    """
    logger.info(
        "Performance metrics recorded",
        extra={
            "event": "performance_metrics",
            **metrics.to_dict()
        }
    )
