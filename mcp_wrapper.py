#!/usr/bin/env python3
"""
Wrapper script for mcp-proxy that reads AUTH_TOKEN from environment
and passes it as Authorization header.
"""

import os
import sys
import subprocess

def main():
    # Read token and URL from environment
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        print("❌ AUTH_TOKEN not found in environment variables")
        sys.exit(1)

    sse_url = os.getenv("SSE_URL", "http://localhost:3001/sse")
    if not sse_url:
        print("❌ SSE_URL not found in environment variables")
        sys.exit(1)

    # Build mcp-proxy command with Authorization header
    cmd = [
        "uvx", "mcp-proxy",
        "-H", "Authorization", auth_token,
        sse_url
    ]

    print(f"🚀 Starting mcp-proxy with Authorization header...")
    print(f"   URL: {sse_url}")
    print(f"   Token: {auth_token[:20]}...")

    # Run mcp-proxy
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 MCP proxy stopped")
    except Exception as e:
        print(f"❌ Error running mcp-proxy: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
