"""
MWhisper Platform Detection
Cross-platform compatibility layer
"""

import platform
import sys

# Platform detection
SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MACOS = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"


def is_windows() -> bool:
    """Check if running on Windows"""
    return IS_WINDOWS


def is_macos() -> bool:
    """Check if running on macOS"""
    return IS_MACOS


def is_linux() -> bool:
    """Check if running on Linux"""
    return IS_LINUX


def get_platform_name() -> str:
    """Get human-readable platform name"""
    if IS_WINDOWS:
        return "Windows"
    elif IS_MACOS:
        return "macOS"
    elif IS_LINUX:
        return "Linux"
    return SYSTEM
