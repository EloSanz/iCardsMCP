"""
iCards MCP Server
A FastMCP server for managing flashcards and study sessions.
"""

import logging
from fastmcp import FastMCP

from app.mcp.tools import register_icards_tools

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("iCards 🎴")

# Register all iCards tools
register_icards_tools(mcp)

if __name__ == "__main__":
    # Run the MCP server
    logger.info("Starting iCards MCP Server...")
    mcp.run()

