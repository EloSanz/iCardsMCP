"""
iCards MCP Server
A FastMCP server for managing flashcards and study sessions.
"""

import logging
import sys
import asyncio
from fastmcp import FastMCP

from app.mcp.tools import register_icards_tools

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Initializing iCards MCP Server...")

        # Initialize FastMCP server
        mcp = FastMCP("iCards 🎴")
        logger.info("FastMCP server created")

        # Register all iCards tools
        register_icards_tools(mcp)
        logger.info("Tools registered")

        # Run the MCP server
        logger.info("Starting MCP server...")
        await mcp.run_async()

    except Exception as e:
        logger.error(f"Error in MCP server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Use asyncio.run for proper async execution
    asyncio.run(main())

