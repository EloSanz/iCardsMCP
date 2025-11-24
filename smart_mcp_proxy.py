#!/usr/bin/env python3
"""
Smart MCP proxy that automatically adds Authorization header from AUTH_TOKEN env var.
Drop-in replacement for mcp-proxy that adds auth support.
"""

import os
import sys
import subprocess

def main():
    # Get all arguments passed to this script
    args = sys.argv[1:]

    # Check if we have an AUTH_TOKEN in environment
    auth_token = os.getenv("AUTH_TOKEN")

    # If we have a token, add the Authorization header
    if auth_token:
        # Insert the header arguments before the URL
        # Find the URL (should be the last argument)
        if args:
            url = args[-1]
            header_args = ["-H", "Authorization", auth_token]
            args = args[:-1] + header_args + [url]

    # Build the full mcp-proxy command
    cmd = ["uvx", "mcp-proxy"] + args

    print(f"🚀 Running: {' '.join(cmd)}")
    if auth_token:
        print(f"   ✅ Added Authorization header from AUTH_TOKEN")

    # Run the actual mcp-proxy
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 MCP proxy stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
