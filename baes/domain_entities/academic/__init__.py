"""
Academic Domain BAEs

This package contains BAE implementations for the academic domain,
including Student, Teacher, and Course entities.
"""

from .course_bae import CourseBae
from .student_bae import StudentBae
from .teacher_bae import TeacherBae

__all__ = ["StudentBae", "TeacherBae", "CourseBae"]
