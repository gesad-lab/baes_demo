"""
LLM Request Logger for BAE System

This module provides comprehensive logging of all LLM requests and responses
for debugging, research, and analysis purposes. It persists the complete
interaction history to enable detailed analysis of LLM behavior and performance.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of LLM requests for categorization"""
    CODE_GENERATION = "code_generation"
    INTERPRETATION = "interpretation"
    VALIDATION = "validation"
    FEEDBACK_ANALYSIS = "feedback_analysis"
    FALLBACK_GENERATION = "fallback_generation"


@dataclass
class LLMRequest:
    """Structured representation of an LLM request"""
    timestamp: str
    request_id: str
    agent_name: str
    request_type: RequestType
    entity: str
    task: str
    prompt: str
    system_prompt: Optional[str]
    context: Dict[str, Any]
    retry_count: int
    session_id: str


@dataclass
class LLMResponse:
    """Structured representation of an LLM response"""
    timestamp: str
    request_id: str
    response_text: str
    success: bool
    error_message: Optional[str]
    response_time_ms: float
    token_count: Optional[int]
    model_used: str


@dataclass
class LLMInteraction:
    """Complete LLM interaction including request and response"""
    request: LLMRequest
    response: LLMResponse
    validation_result: Optional[Dict[str, Any]] = None
    feedback_loop: Optional[Dict[str, Any]] = None


class LLMRequestLogger:
    """
    Comprehensive logger for LLM requests and responses.
    
    This logger persists all LLM interactions to enable:
    - Debugging of LLM generation issues
    - Research on prompt effectiveness
    - Analysis of validation feedback loops
    - Performance monitoring
    - Quality improvement tracking
    """
    
    def __init__(self, log_dir: str = "logs/llm_requests"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different types of logs
        self.requests_dir = self.log_dir / "requests"
        self.responses_dir = self.log_dir / "responses"
        self.interactions_dir = self.log_dir / "interactions"
        self.analytics_dir = self.log_dir / "analytics"
        
        for dir_path in [self.requests_dir, self.responses_dir, self.interactions_dir, self.analytics_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def log_request(
        self,
        agent_name: str,
        request_type: RequestType,
        entity: str,
        task: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Log an LLM request and return the request ID.
        
        Args:
            agent_name: Name of the agent making the request
            request_type: Type of request (code generation, interpretation, etc.)
            entity: Target entity for the request
            task: Specific task being performed
            prompt: The actual prompt sent to the LLM
            system_prompt: Optional system prompt
            context: Additional context information
            retry_count: Number of retries for this request
            session_id: Session identifier for grouping related requests
            
        Returns:
            Request ID for tracking the response
        """
        timestamp = datetime.now().isoformat()
        request_id = f"{agent_name}_{entity}_{task}_{timestamp.replace(':', '-')}"
        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request = LLMRequest(
            timestamp=timestamp,
            request_id=request_id,
            agent_name=agent_name,
            request_type=request_type,
            entity=entity,
            task=task,
            prompt=prompt,
            system_prompt=system_prompt,
            context=context or {},
            retry_count=retry_count,
            session_id=session_id,
        )
        
        # Save request to file
        request_file = self.requests_dir / f"{request_id}.json"
        with open(request_file, 'w') as f:
            json.dump(asdict(request), f, indent=2, default=str)
        
        logger.info(f"📝 LLM Request logged: {request_id} ({request_type.value})")
        return request_id
    
    def log_response(
        self,
        request_id: str,
        response_text: str,
        success: bool,
        error_message: Optional[str] = None,
        response_time_ms: float = 0.0,
        token_count: Optional[int] = None,
        model_used: str = "gpt-4o-mini",
    ) -> None:
        """
        Log an LLM response.
        
        Args:
            request_id: ID of the corresponding request
            response_text: The response from the LLM
            success: Whether the request was successful
            error_message: Error message if failed
            response_time_ms: Response time in milliseconds
            token_count: Number of tokens used
            model_used: Model that generated the response
        """
        timestamp = datetime.now().isoformat()
        
        response = LLMResponse(
            timestamp=timestamp,
            request_id=request_id,
            response_text=response_text,
            success=success,
            error_message=error_message,
            response_time_ms=response_time_ms,
            token_count=token_count,
            model_used=model_used,
        )
        
        # Save response to file
        response_file = self.responses_dir / f"{request_id}.json"
        with open(response_file, 'w') as f:
            json.dump(asdict(response), f, indent=2, default=str)
        
        logger.info(f"📝 LLM Response logged: {request_id} (success: {success}, time: {response_time_ms:.0f}ms)")
    
    def log_interaction(
        self,
        request: LLMRequest,
        response: LLMResponse,
        validation_result: Optional[Dict[str, Any]] = None,
        feedback_loop: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a complete LLM interaction including request, response, and validation.
        
        Args:
            request: The LLM request
            response: The LLM response
            validation_result: Results from TechLeadSWEA validation
            feedback_loop: Information about feedback loops and retries
        """
        interaction = LLMInteraction(
            request=request,
            response=response,
            validation_result=validation_result,
            feedback_loop=feedback_loop,
        )
        
        # Save complete interaction to file
        interaction_file = self.interactions_dir / f"{request.request_id}.json"
        with open(interaction_file, 'w') as f:
            json.dump(asdict(interaction), f, indent=2, default=str)
        
        logger.info(f"📝 LLM Interaction logged: {request.request_id}")
    
    def log_validation_result(
        self,
        request_id: str,
        validation_result: Dict[str, Any],
        entity: str,
        agent_name: str,
    ) -> None:
        """
        Log validation results for analysis.
        
        Args:
            request_id: ID of the request being validated
            validation_result: Results from TechLeadSWEA validation
            entity: Entity being validated
            agent_name: Name of the agent that generated the code
        """
        validation_log = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "entity": entity,
            "agent_name": agent_name,
            "validation_result": validation_result,
        }
        
        # Save validation result
        validation_file = self.analytics_dir / f"validation_{request_id}.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_log, f, indent=2, default=str)
        
        logger.info(f"📝 Validation result logged: {request_id} (valid: {validation_result.get('is_valid', False)})")
    
    def get_session_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all interactions for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of interaction data
        """
        interactions = []
        for interaction_file in self.interactions_dir.glob("*.json"):
            try:
                with open(interaction_file, 'r') as f:
                    interaction = json.load(f)
                    if interaction.get('request', {}).get('session_id') == session_id:
                        interactions.append(interaction)
            except Exception as e:
                logger.warning(f"Failed to read interaction file {interaction_file}: {e}")
        
        return sorted(interactions, key=lambda x: x['request']['timestamp'])
    
    def get_entity_interactions(self, entity: str) -> List[Dict[str, Any]]:
        """
        Retrieve all interactions for a specific entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of interaction data
        """
        interactions = []
        for interaction_file in self.interactions_dir.glob("*.json"):
            try:
                with open(interaction_file, 'r') as f:
                    interaction = json.load(f)
                    if interaction.get('request', {}).get('entity') == entity:
                        interactions.append(interaction)
            except Exception as e:
                logger.warning(f"Failed to read interaction file {interaction_file}: {e}")
        
        return sorted(interactions, key=lambda x: x['request']['timestamp'])
    
    def generate_analytics_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate analytics report for debugging and research.
        
        Args:
            session_id: Optional session ID to filter results
            
        Returns:
            Analytics report with key metrics
        """
        interactions = self.get_session_interactions(session_id) if session_id else []
        if not session_id:
            # Get all interactions
            for interaction_file in self.interactions_dir.glob("*.json"):
                try:
                    with open(interaction_file, 'r') as f:
                        interactions.append(json.load(f))
                except Exception as e:
                    logger.warning(f"Failed to read interaction file {interaction_file}: {e}")
        
        if not interactions:
            return {"error": "No interactions found"}
        
        # Calculate metrics
        total_requests = len(interactions)
        successful_requests = sum(1 for i in interactions if i.get('response', {}).get('success', False))
        failed_requests = total_requests - successful_requests
        
        # Validation metrics
        validation_results = [i.get('validation_result') for i in interactions if i.get('validation_result')]
        valid_generations = sum(1 for v in validation_results if v and v.get('is_valid', False))
        
        # Response time metrics
        response_times = [i.get('response', {}).get('response_time_ms', 0) for i in interactions]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Request type distribution
        request_types = {}
        for interaction in interactions:
            req_type = interaction.get('request', {}).get('request_type', 'unknown')
            request_types[req_type] = request_types.get(req_type, 0) + 1
        
        # Entity distribution
        entities = {}
        for interaction in interactions:
            entity = interaction.get('request', {}).get('entity', 'unknown')
            entities[entity] = entities.get(entity, 0) + 1
        
        report = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "valid_generations": valid_generations,
                "validation_rate": (valid_generations / len(validation_results) * 100) if validation_results else 0,
                "avg_response_time_ms": avg_response_time,
            },
            "request_types": request_types,
            "entities": entities,
            "interactions": interactions,
        }
        
        # Save report
        report_file = self.analytics_dir / f"report_{session_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Analytics report generated: {report_file}")
        return report


# Global logger instance
llm_logger = LLMRequestLogger() 