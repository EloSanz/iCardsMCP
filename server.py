"""
iCards MCP Server
A FastMCP server for managing flashcards and study sessions.
"""

import logging
import sys
import asyncio
import httpx
from fastmcp import FastMCP

from app.mcp.tools import register_icards_tools
from app.config.config import config

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

async def validate_api_connection():
    """Validate API connection and token on startup."""
    try:
        logger.info("🔍 Validating API connection...")

        base_url = (config.get("API_BASE_URL") or "http://localhost:3000").rstrip("/")
        timeout = config.get("API_TIMEOUT") or 30

        # Get auth token
        auth_token = None
        if hasattr(sys.modules.get('os'), 'getenv'):
            import os
            auth_token = os.getenv("AUTH_TOKEN")

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # 1. Health check
            logger.info(f"🏥 Checking API health at {base_url}/api/health...")
            health_response = await client.get(f"{base_url}/api/health")
            health_response.raise_for_status()
            health_data = health_response.json()
            logger.info(f"✅ API health check passed: {health_data}")

            # 2. Token validation - try to get user decks
            logger.info("🔐 Validating token by fetching decks...")
            decks_response = await client.get(f"{base_url}/api/decks")
            decks_response.raise_for_status()
            decks_data = decks_response.json()
            logger.info(f"✅ Token validation passed - found {len(decks_data.get('decks', []))} decks")

        logger.info("🎉 API connection and token validation successful!")
        return True

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.error("❌ Authentication failed - invalid or missing AUTH_TOKEN")
            logger.error("💡 Make sure AUTH_TOKEN environment variable is set with a valid JWT token")
        elif e.response.status_code == 404:
            logger.error(f"❌ API endpoint not found: {e.request.url}")
        else:
            logger.error(f"❌ API error: {e.response.status_code} - {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"❌ Cannot connect to API at {base_url}")
        logger.error(f"💡 Make sure your iCards API server is running on {base_url}")
        logger.error(f"   Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during API validation: {str(e)}")
        return False

async def main():
    try:
        logger.info("🚀 Initializing iCards MCP Server...")

        # Validate API connection before starting MCP server
        if not await validate_api_connection():
            logger.error("💥 API validation failed - MCP server will not start")
            logger.error("💡 Please check your API server and AUTH_TOKEN configuration")
            sys.exit(1)

        # Initialize FastMCP server
        mcp = FastMCP("iCards 🎴")
        logger.info("✅ FastMCP server created")

        # Register all iCards tools
        register_icards_tools(mcp)
        logger.info("✅ Tools registered")

        # Run the MCP server
        logger.info("🎯 Starting MCP server and waiting for requests...")
        await mcp.run_async()

    except Exception as e:
        logger.error(f"💥 Error in MCP server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Use asyncio.run for proper async execution
    asyncio.run(main())

