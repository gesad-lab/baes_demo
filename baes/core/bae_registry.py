from typing import Dict, List, Optional, Any
from baes.agents.base_bae import BaseBAE
from baes.agents.student_bae import StudentBAE
from baes.agents.course_bae import CourseBAE
from baes.agents.teacher_bae import TeacherBAE
import logging

logger = logging.getLogger(__name__)

class EnhancedBAERegistry:
    """
    Enhanced registry for managing Business Autonomous Entities (BAEs)
    with metadata support and centralized BAE lifecycle management.
    """
    
    def __init__(self):
        self.baes: Dict[str, BaseBAE] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._initialize_baes()
        logger.info(f"BAE Registry initialized with {len(self.baes)} entities")
    
    def _initialize_baes(self):
        """Initialize all supported BAEs with their metadata"""
        
        # Student BAE
        try:
            student_bae = StudentBAE()
            self.baes["student"] = student_bae
            self.metadata["student"] = {
                "keywords": ["student", "aluno", "estudante", "discente"],
                "description": "Manages student entities and academic operations",
                "domain_attributes": ["name", "registration_number", "course", "email", "age", "birth_date", "gpa"],
                "business_rules": [
                    "Registration number must be unique",
                    "Email validation required",
                    "Age must be positive and reasonable for students"
                ],
                "contexts": ["university", "open_courses", "corporate_training"],
                "status": "active",
                "version": "1.0",
                "last_updated": None
            }
            logger.info("StudentBAE initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize StudentBAE: {e}")
        
        # Course BAE
        try:
            course_bae = CourseBAE()
            self.baes["course"] = course_bae
            self.metadata["course"] = {
                "keywords": ["course", "curso", "disciplina", "matéria", "subject"],
                "description": "Manages course entities and curriculum operations",
                "domain_attributes": ["name", "code", "credits", "duration", "description", "prerequisites"],
                "business_rules": [
                    "Course code must be unique",
                    "Credits must be positive",
                    "Prerequisites must exist in system"
                ],
                "contexts": ["university", "open_courses", "corporate_training"],
                "status": "active",
                "version": "1.0",
                "last_updated": None
            }
            logger.info("CourseBAE initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CourseBAE: {e}")
        
        # Teacher BAE
        try:
            teacher_bae = TeacherBAE()
            self.baes["teacher"] = teacher_bae
            self.metadata["teacher"] = {
                "keywords": ["teacher", "professor", "docente", "instrutor", "instructor"],
                "description": "Manages teacher entities and instruction operations",
                "domain_attributes": ["name", "employee_id", "department", "subjects", "email", "phone"],
                "business_rules": [
                    "Employee ID must be unique",
                    "Department must be valid",
                    "At least one subject assignment required"
                ],
                "contexts": ["university", "corporate_training", "open_courses"],
                "status": "active",
                "version": "1.0", 
                "last_updated": None
            }
            logger.info("TeacherBAE initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TeacherBAE: {e}")
    
    def get_bae(self, entity_type: str) -> Optional[BaseBAE]:
        """Get BAE instance by entity type"""
        bae = self.baes.get(entity_type.lower())
        if bae:
            logger.debug(f"Retrieved {entity_type} BAE")
        else:
            logger.warning(f"BAE not found for entity type: {entity_type}")
        return bae
    
    def get_bae_metadata(self, entity_type: str) -> Dict[str, Any]:
        """Get metadata for specific BAE"""
        return self.metadata.get(entity_type.lower(), {})
    
    def get_all_baes_info(self) -> Dict[str, Dict[str, Any]]:
        """Get complete information about all BAEs"""
        return {
            entity: {
                "bae": bae,
                "metadata": self.metadata.get(entity, {})
            }
            for entity, bae in self.baes.items()
        }
    
    def get_supported_entities(self) -> List[str]:
        """Get list of all supported entity types"""
        return list(self.baes.keys())
    
    def get_entity_keywords(self, entity_type: str) -> List[str]:
        """Get keywords for specific entity type"""
        metadata = self.get_bae_metadata(entity_type)
        return metadata.get("keywords", [])
    
    def get_all_keywords(self) -> Dict[str, List[str]]:
        """Get all keywords for all entities"""
        return {
            entity: metadata.get("keywords", [])
            for entity, metadata in self.metadata.items()
        }
    
    def is_entity_supported(self, entity_type: str) -> bool:
        """Check if entity type is supported"""
        return entity_type.lower() in self.baes
    
    def get_entity_status(self, entity_type: str) -> str:
        """Get status of specific entity BAE"""
        metadata = self.get_bae_metadata(entity_type)
        return metadata.get("status", "unknown")
    
    def update_bae_metadata(self, entity_type: str, key: str, value: Any):
        """Update metadata for specific BAE"""
        if entity_type in self.metadata:
            self.metadata[entity_type][key] = value
            logger.info(f"Updated {entity_type} BAE metadata: {key} = {value}")
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registry status"""
        active_baes = sum(1 for metadata in self.metadata.values() if metadata.get("status") == "active")
        
        return {
            "total_baes": len(self.baes),
            "active_baes": active_baes,
            "supported_entities": self.get_supported_entities(),
            "total_keywords": sum(len(metadata.get("keywords", [])) for metadata in self.metadata.values()),
            "registry_status": "healthy" if active_baes == len(self.baes) else "degraded"
        } 