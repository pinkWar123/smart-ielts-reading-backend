"""Test status enumeration"""

from enum import Enum


class TestStatus(str, Enum):
    """Test lifecycle status"""

    DRAFT = "DRAFT"  # Being created/edited
    PUBLISHED = "PUBLISHED"  # Available for users
    ARCHIVED = "ARCHIVED"  # No longer active
