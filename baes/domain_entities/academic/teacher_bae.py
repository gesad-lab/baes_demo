import logging
from typing import List, Dict, Any

from ..base_bae import BaseBae

logger = logging.getLogger(__name__)


class TeacherBae(BaseBae):
    """
    Business Autonomous Entity representing the Teacher domain entity.
    Specialized BAE for managing teacher-related operations, instruction management,
    and maintaining semantic coherence between business vocabulary and technical artifacts.
    """

    def __init__(self):
        super().__init__(
            entity_name="Teacher",
            domain_keywords=["teacher", "professor", "docente", "instrutor", "instructor"],
        )

        # Set domain for this BAE
        self.domain = "academic"

        logger.info("TeacherBAE initialized for teacher domain entity management")

    def _initialize_domain_knowledge(self):
        """Initialize teacher-specific domain knowledge"""
        self.domain_knowledge = {
            "academic": {
                "entity": "Teacher",
                "core_attributes": self._get_default_attributes(),
                "business_rules": self._get_business_rules(),
                "relationships": ["assigned_courses", "student_groups", "department"],
                "contexts": ["university", "corporate_training", "online_education"],
            }
        }

        # Teacher-specific business vocabulary
        self.business_vocabulary = [
            "teacher",
            "instructor",
            "faculty",
            "pedagogy",
            "curriculum",
            "assessment",
            "qualification",
            "expertise",
            "academic",
            "education",
        ]

    def _get_default_attributes(self) -> List[Dict[str, Any]]:
        """Get default attributes for Teacher domain entity"""
        return [
            {"name": "name", "type": "str"},
            {"name": "employee_id", "type": "str"},
            {"name": "department", "type": "str"},
        ]

    def _get_business_rules(self) -> List[str]:
        """Get business rules specific to Teacher domain entity"""
        return [
            "Employee ID must be unique within institution",
            "Department must be valid and existing",
            "At least one subject assignment required",
            "Email must be valid institutional format",
            "Qualifications must be verifiable",
            "Subject expertise must match assigned courses",
        ]

    def _generate_context_rules(self, context: str, modifications: List[str]) -> List[str]:
        """Generate context-specific business rules for Teacher entity"""
        rules = super()._generate_context_rules(context, modifications)

        if context == "university":
            rules.extend(
                [
                    "Teacher must have appropriate academic credentials",
                    "Research activities may be required",
                    "Tenure track requirements may apply",
                    "Student evaluation processes must be followed",
                ]
            )
        elif context == "corporate_training":
            rules.extend(
                [
                    "Teacher must have industry experience",
                    "Business domain expertise is required",
                    "Corporate training certifications may be needed",
                    "ROI and performance metrics are important",
                ]
            )
        elif context == "online_education":
            rules.extend(
                [
                    "Digital teaching competencies required",
                    "Online platform proficiency needed",
                    "Remote assessment capabilities required",
                    "Technology support availability important",
                ]
            )

        return rules
