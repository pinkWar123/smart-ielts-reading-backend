"""Violation type enumeration for attempt tracking"""

from enum import Enum


class ViolationType(str, Enum):
    """Types of violations that can be recorded during a test attempt"""

    TAB_SWITCH = "TAB_SWITCH"
    WINDOW_BLUR = "WINDOW_BLUR"
    COPY_PASTE = "COPY_PASTE"
    FULL_SCREEN_EXIT = "FULL_SCREEN_EXIT"
    CONTEXT_MENU = "CONTEXT_MENU"
