"""Class status enumeration"""

from enum import Enum


class ClassStatus(str, Enum):
    """Teaching class_ lifecycle status"""

    ACTIVE = "ACTIVE"  # Class is active and accepting students
    ARCHIVED = "ARCHIVED"  # Class is archived and no longer active
