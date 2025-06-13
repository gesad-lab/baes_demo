import logging
from typing import List

from ..base_bae import BaseBae

logger = logging.getLogger(__name__)


class StudentBae(BaseBae):
    """
    Business Autonomous Entity representing the Student domain entity.
    Specialized BAE for managing student-related operations, academic records,
    and maintaining semantic coherence between business vocabulary and technical artifacts.
    """

    def __init__(self):
        super().__init__(
            entity_name="Student", domain_keywords=["student", "aluno", "estudante", "discente"]
        )

        # Add compatibility attributes for integration tests
        self.primary_entity = "Student"
        self.current_entity = "Student"

        logger.info("StudentBAE initialized for student domain entity management")

    def _initialize_domain_knowledge(self):
        """Initialize student-specific domain knowledge"""
        self.domain_knowledge = {
            "academic": {
                "entity": "Student",
                "core_attributes": self._get_default_attributes(),
                "business_rules": self._get_business_rules(),
                "relationships": ["enrolled_courses", "academic_records", "institution"],
                "contexts": ["university", "open_courses", "corporate_training"],
            }
        }

        # Student-specific business vocabulary
        self.business_vocabulary = [
            "student",
            "registration",
            "enrollment",
            "academic",
            "learning",
            "course",
            "grade",
            "education",
            "curriculum",
            "institution",
        ]

    def _get_default_attributes(self) -> List[str]:
        """Get default attributes for Student domain entity"""
        return [
            "name: str",
            "registration_number: str",
            "course: str",
        ]

    def _get_business_rules(self) -> List[str]:
        """Get business rules specific to Student domain entity"""
        return [
            "Registration number must be unique within institution",
            "Email must be valid and unique",
            "Age must be positive and reasonable for students (typically 16-65)",
            "GPA must be within valid range (0.0-4.0 or institutional scale)",
            "Student must be enrolled in at least one course",
            "Birth date must be consistent with declared age",
        ]

    def _generate_context_rules(self, context: str, modifications: List[str]) -> List[str]:
        """Generate context-specific business rules for Student entity"""
        rules = super()._generate_context_rules(context, modifications)

        if context == "university":
            rules.extend(
                [
                    "Student must have valid academic status",
                    "Course load limits must be respected",
                    "Prerequisites must be satisfied for course enrollment",
                    "Academic probation rules apply for low GPA",
                ]
            )
        elif context == "open_courses":
            rules.extend(
                [
                    "Registration number may be optional",
                    "Flexible enrollment criteria apply",
                    "Payment verification may be required",
                    "Certificate completion requirements vary",
                ]
            )
        elif context == "corporate_training":
            rules.extend(
                [
                    "Employee ID may substitute for registration number",
                    "Department affiliation is required",
                    "Training completion impacts performance review",
                    "Corporate learning objectives must be met",
                ]
            )

        return rules
