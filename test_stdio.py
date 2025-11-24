#!/usr/bin/env python3
"""
Test script to run the MCP server in stdio mode for testing tools directly.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set the auth token for testing
os.environ["AUTH_TOKEN"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImlhdCI6MTc2Mzk1NjY3OCwiZXhwIjoxNzY0MDQzMDc4fQ.ap0Q-DyMtbIr91rh-vP6LeZaWCuuqiMAFZRE1iVjt64"

from server import mcp
import asyncio

async def main():
    print("Starting MCP server in stdio mode...")
    await mcp.run_async()

if __name__ == "__main__":
    asyncio.run(main())
