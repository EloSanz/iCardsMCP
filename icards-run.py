#!/usr/bin/env python3
"""
Wrapper script to run icards.server with uvx
"""
import sys
import subprocess

if __name__ == "__main__":
    # Add current directory to Python path for imports
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Run the server module with remaining arguments
    args = ["uv", "run", "python", "-m", "icards.server"] + sys.argv[1:]
    subprocess.run(args)
