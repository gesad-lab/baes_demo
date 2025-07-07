import logging
from typing import Any, Dict, List

from ..base_bae import BaseBae

logger = logging.getLogger(__name__)


class CourseBae(BaseBae):
    """
    Business Autonomous Entity representing the Course domain entity.
    Specialized BAE for managing course-related operations, curriculum management,
    and maintaining semantic coherence between business vocabulary and technical artifacts.
    """

    def __init__(self):
        super().__init__(
            entity_name="Course",
            domain_keywords=["course", "curso", "disciplina", "matéria", "subject"],
        )

        # Set domain for this BAE
        self.domain = "academic"

        logger.info("CourseBAE initialized for course domain entity management")

    def _initialize_domain_knowledge(self):
        """Initialize course-specific domain knowledge"""
        self.domain_knowledge = {
            "academic": {
                "entity": "Course",
                "core_attributes": self._get_default_attributes(),
                "business_rules": self._get_business_rules(),
                "relationships": ["prerequisite_courses", "enrolled_students", "assigned_teachers"],
                "contexts": ["university", "online_learning", "corporate_training"],
            }
        }

        # Course-specific business vocabulary
        self.business_vocabulary = [
            "course",
            "curriculum",
            "syllabus",
            "credit",
            "semester",
            "prerequisite",
            "enrollment",
            "assessment",
            "academic",
        ]

    def _get_default_attributes(self) -> List[Dict[str, Any]]:
        """Get default attributes for Course domain entity"""
        return [
            {"name": "name", "type": "str"},
            # {"name": "code", "type": "str"},
            # {"name": "credits", "type": "int"},
            # {"name": "duration", "type": "int"},
            # {"name": "description", "type": "str"},
            # {"name": "prerequisites", "type": "List[str]"},
            # {"name": "department", "type": "str"},
            # {"name": "level", "type": "str"},
        ]

    def _get_business_rules(self) -> List[str]:
        """Get business rules specific to Course domain entity"""
        return [
            "Course code must be unique within institution",
            "Credits must be positive integer",
            "Prerequisites must reference existing courses",
            "Duration must be specified in hours or weeks",
            "Course must be assigned to a valid department",
            "Level must be appropriate (undergraduate, graduate, etc.)",
        ]

    def _generate_context_rules(self, context: str, modifications: List[str]) -> List[str]:
        """Generate context-specific business rules for Course entity"""
        rules = super()._generate_context_rules(context, modifications)

        if context == "online_learning":
            rules.extend(
                [
                    "Course must have digital content requirements",
                    "Online delivery method must be specified",
                    "Technical requirements for students must be defined",
                ]
            )
        elif context == "corporate_training":
            rules.extend(
                [
                    "Course must align with business objectives",
                    "Competency mapping is required",
                    "ROI measurement criteria must be defined",
                ]
            )
        elif context == "university":
            rules.extend(
                [
                    "Course must fit within degree program requirements",
                    "Academic calendar constraints must be considered",
                    "Faculty qualifications must be verified",
                ]
            )

        return rules
