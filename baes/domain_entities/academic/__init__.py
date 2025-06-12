"""
Academic Domain BAEs

This package contains BAE implementations for the academic domain,
including Student, Teacher, and Course entities.
"""

from .student_bae import StudentBae
from .teacher_bae import TeacherBae
from .course_bae import CourseBae

__all__ = [
    'StudentBae',
    'TeacherBae', 
    'CourseBae'
] 