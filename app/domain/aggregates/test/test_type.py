"""Test type enumeration"""
from enum import Enum


class TestType(str, Enum):
    """IELTS Reading test types"""
    FULL_TEST = "FULL_TEST"  # 3 passages, ~40 questions, 60 minutes
    SINGLE_PASSAGE = "SINGLE_PASSAGE"  # 1 passage, ~13 questions, 20 minutes
