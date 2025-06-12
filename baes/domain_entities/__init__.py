"""
Business Autonomous Entities (BAEs) Package

This package contains all BAE implementations organized by domain.
BAEs represent domain entities as living, autonomous agents within the system,
maintaining semantic coherence between business vocabulary and technical artifacts.
"""

# Note: To avoid circular imports, individual BAEs should be imported directly:
# from baes.domain_entities.base_bae import BaseBae
# from baes.domain_entities.academic.student_bae import StudentBae
# etc.

# Lazy imports to avoid circular dependencies
def get_base_bae():
    from .base_bae import BaseBae
    return BaseBae

def get_generic_bae():
    from .generic_bae import GenericBae
    return GenericBae

def get_student_bae():
    from .academic.student_bae import StudentBae
    return StudentBae

def get_teacher_bae():
    from .academic.teacher_bae import TeacherBae
    return TeacherBae

def get_course_bae():
    from .academic.course_bae import CourseBae
    return CourseBae

__all__ = [
    'get_base_bae',
    'get_generic_bae', 
    'get_student_bae',
    'get_teacher_bae',
    'get_course_bae'
] 