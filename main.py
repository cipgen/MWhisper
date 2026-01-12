#!/usr/bin/env python3
"""
MWhisper - Voice Dictation for Mac M1
Entry point for the application
"""

import sys
import os
import time

def setup_debug_logging():
    """Setup logging to ~/Desktop/mwhisper_debug.log for frozen apps"""
    if getattr(sys, 'frozen', False):
        try:
            log_path = os.path.expanduser("~/Desktop/mwhisper_debug.log")
            # Open in append mode to capture restarts
            sys.stdout = open(log_path, "a", buffering=1, encoding='utf-8')
            sys.stderr = sys.stdout
            print(f"\n{'='*50}")
            print(f"MWhisper Debug Log started at {time.ctime()}")
            print(f"{'='*50}\n")
        except Exception as e:
            pass

# Setup logging before imports to capture import errors
setup_debug_logging()

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.app import run_app
except Exception as e:
    print(f"CRITICAL: Failed to import app: {e}")
    sys.exit(1)

def main():
    """Main entry point"""
    # Check arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--settings":
            print("Launching Settings GUI...")
            from src.settings_gui import run_settings
            run_settings()
            return

    print("Starting MWhisper...")
    run_app()


if __name__ == "__main__":
    main()
