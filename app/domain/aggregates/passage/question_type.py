"""Question type enumeration"""
from enum import Enum


class QuestionType(str, Enum):
    """IELTS Reading question types"""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOTGIVEN = "TRUE_FALSE_NOTGIVEN"
    YES_NO_NOTGIVEN = "YES_NO_NOTGIVEN"
    MATCHING_HEADINGS = "MATCHING_HEADINGS"
    MATCHING_INFORMATION = "MATCHING_INFORMATION"
    MATCHING_FEATURES = "MATCHING_FEATURES"
    MATCHING_SENTENCE_ENDINGS = "MATCHING_SENTENCE_ENDINGS"
    SENTENCE_COMPLETION = "SENTENCE_COMPLETION"
    SUMMARY_COMPLETION = "SUMMARY_COMPLETION"
    NOTE_COMPLETION = "NOTE_COMPLETION"
    TABLE_COMPLETION = "TABLE_COMPLETION"
    FLOW_CHART_COMPLETION = "FLOW_CHART_COMPLETION"
    DIAGRAM_LABEL_COMPLETION = "DIAGRAM_LABEL_COMPLETION"
    SHORT_ANSWER = "SHORT_ANSWER"

    @classmethod
    def requires_options(cls, question_type: 'QuestionType') -> bool:
        """Check if question type requires options"""
        return question_type in [
            cls.MULTIPLE_CHOICE,
            cls.MATCHING_HEADINGS,
            cls.MATCHING_INFORMATION,
            cls.MATCHING_FEATURES,
            cls.MATCHING_SENTENCE_ENDINGS,
        ]
