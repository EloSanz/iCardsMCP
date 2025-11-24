#!/usr/bin/env python3
"""Test script for iCards MCP tools."""

import asyncio
import os
from fastmcp import FastMCP
from app.config.config import config
from app.mcp.instructions import load_instructions
from app.mcp.tools import register_icards_tools

async def test_list_decks():
    """Test the list_decks tool."""
    try:
        # Set environment variables
        os.environ['AUTH_TOKEN'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImlhdCI6MTc2Mzk1MDMwMSwiZXhwIjoxNzY0MDM2NzAxfQ.hUB8vX8T4OIyRQzmwYgmo3vUvXmyWz-hiWTrqBK6RsM'

        # Load instructions
        instructions_path = config.get("MCP_ICARDS_INSTRUCTIONS_PATH")
        instructions = load_instructions(instructions_path)

        # Create MCP server instance
        mcp = FastMCP("iCards Test", instructions=instructions)

        # Register tools
        register_icards_tools(mcp)

        # Get the list_decks tool function
        list_decks_tool = None
        for tool_name, tool_obj in mcp._tool_manager._tools.items():
            if tool_name == 'list_decks':
                list_decks_tool = tool_obj.fn
                break

        if not list_decks_tool:
            print("❌ list_decks tool not found")
            return

        # Call the tool
        print("🔍 Calling list_decks tool...")
        result = await list_decks_tool()

        print("✅ Tool executed successfully!")
        print("📊 Result:")
        print(result)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_list_decks())
