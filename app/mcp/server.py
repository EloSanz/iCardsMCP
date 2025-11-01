"""MCP server provides tools, resources and prompts."""

import logging
from fastmcp import FastMCP

from app.config.config import config
from app.mcp.instructions import load_instructions

logger = logging.getLogger(__name__)

# Load instructions for MCP iCards
mcp_icards_instructions = load_instructions(config.get("MCP_ICARDS_INSTRUCTIONS_PATH"))

# Create MCP iCards instance
mcp_icards = FastMCP(config.get("MCP_ICARDS_NAME"), instructions=mcp_icards_instructions)

# Register iCards tools
from app.mcp.tools import register_icards_tools
register_icards_tools(mcp_icards)
