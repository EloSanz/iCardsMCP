"""
iCards MCP Server
A FastMCP server for managing flashcards and study sessions.
"""

import asyncio
import logging
import os
import sys

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

from app.config.config import config
from app.mcp.tools import register_icards_tools

# Load environment variables from .env.local if it exists
try:
    # Load .env.local if it exists, otherwise .env
    env_file = ".env.local" if os.path.exists(".env.local") else ".env"
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"📄 Loaded environment variables from {env_file}")
    else:
        print("⚠️  No environment file found (.env.local or .env)")
except ImportError:
    print("⚠️  python-dotenv not available, environment variables must be set manually")

# Setup rich logging
try:
    from rich.console import Console
    from rich.logging import RichHandler

    console = Console(stderr=True)

    # Configure rich logging
    logging.basicConfig(
        level=logging.INFO, format="%(message)s", handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

    # Create custom logger with better formatting
    logger = logging.getLogger("icards-mcp")
    logger.setLevel(logging.INFO)

    # Disable httpx and other library loggers to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

except ImportError:
    # Fallback to basic logging if rich is not available
    console = None
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s", stream=sys.stderr)
    logger = logging.getLogger(__name__)


async def validate_api_connection():
    """Validate API connection and token on startup."""
    try:
        logger.info("🔍 Validating API connection...")

        base_url = (config.get("API_BASE_URL") or "http://localhost:3000").rstrip("/")
        timeout = config.get("API_TIMEOUT") or 30

        # Get auth token from environment
        import os

        auth_token = os.getenv("AUTH_TOKEN")

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            # Mask token for logging (show first 8 chars + ...)
            masked_token = auth_token[:8] + "..." if len(auth_token) > 8 else auth_token
            logger.info(f"🔐 Authentication token found: [dim]{masked_token}[/dim]")

            if console:
                # Show full headers in dimmed text for debugging
                console.print("📋 Request headers configured", style="dim")
        else:
            logger.error("❌ AUTH_TOKEN not configured!")
            if console:
                console.print("\n[bold red]🔑 Authentication Setup Required:[/bold red]")
                console.print("1. Get JWT token by logging in:")
                console.print("   [cyan]curl -X POST http://localhost:3000/api/auth/login \\[/cyan]")
                console.print("   [cyan]  -H 'Content-Type: application/json' \\[/cyan]")
                console.print('   [cyan]  -d \'{"username": "your-username", "password": "your-password"}\'[/cyan]')
                console.print("2. Copy the 'token' field from the response")
                console.print("3. Set environment variable:")
                console.print("   [green]export AUTH_TOKEN='your_jwt_token_here'[/green]")
                console.print("4. Or create .env.local file:")
                console.print("   [green]echo 'AUTH_TOKEN=your_jwt_token_here' > .env.local[/green]")
                console.print()
            return False

        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # 1. Health check
            logger.info(f"🏥 Checking API health at {base_url}/api/health...")
            health_response = await client.get(f"{base_url}/api/health")
            health_response.raise_for_status()
            logger.info("✅ API health check passed")

            # 2. Token validation - try to get user decks
            logger.info("🔐 Validating authentication token...")
            decks_response = await client.get(f"{base_url}/api/decks")
            decks_response.raise_for_status()
            decks_data = decks_response.json()
            deck_count = len(decks_data.get("decks", []))
            logger.info(f"✅ Authentication validated - found {deck_count} deck{'s' if deck_count != 1 else ''}")

        if console:
            console.print("🎉 [bold green]API connection and authentication successful![/bold green]")
        else:
            logger.info("🎉 API connection and authentication successful!")
        return True

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            if console:
                console.print("[bold red]❌ Authentication failed![/bold red]")
                console.print("💡 Check that AUTH_TOKEN contains a valid JWT token")
            else:
                logger.error("❌ Authentication failed - invalid or missing AUTH_TOKEN")
        elif e.response.status_code == 404:
            if console:
                console.print(f"[bold red]❌ API endpoint not found:[/bold red] {e.request.url}")
            else:
                logger.error(f"❌ API endpoint not found: {e.request.url}")
        else:
            if console:
                console.print(f"[bold red]❌ API error {e.response.status_code}:[/bold red] {e.response.text}")
            else:
                logger.error(f"❌ API error: {e.response.status_code} - {e.response.text}")
        return False
    except httpx.RequestError as e:
        if console:
            console.print("[bold red]❌ Cannot connect to API server[/bold red]")
            console.print(f"💡 Make sure iCards API is running on: [cyan]{base_url}[/cyan]")
            console.print(f"   [dim]Error: {str(e)}[/dim]")
        else:
            logger.error(f"❌ Cannot connect to API at {base_url}")
            logger.error(f"💡 Make sure your iCards API server is running on {base_url}")
        return False
    except Exception as e:
        if console:
            console.print(f"[bold red]❌ Unexpected error during validation:[/bold red] {str(e)}")
        else:
            logger.error(f"❌ Unexpected error during API validation: {str(e)}")
        return False


async def main():
    try:
        if console:
            console.print("🚀 [bold blue]Initializing iCards MCP Server...[/bold blue]")
        else:
            logger.info("🚀 Initializing iCards MCP Server...")

        # Validate API connection before starting MCP server
        if not await validate_api_connection():
            if console:
                console.print("\n[bold red]💥 Server startup aborted![/bold red]")
                console.print("💡 Check your API server and authentication configuration")
            else:
                logger.error("💥 API validation failed - MCP server will not start")
                logger.error("💡 Please check your API server and AUTH_TOKEN configuration")
            sys.exit(1)

        # Initialize FastMCP server
        mcp = FastMCP("iCards 🎴")
        if console:
            console.print("✅ [green]FastMCP server initialized[/green]")
        else:
            logger.info("✅ FastMCP server created")

        # Register all iCards tools
        register_icards_tools(mcp)
        if console:
            console.print("✅ [green]Tools registered successfully[/green]")
        else:
            logger.info("✅ Tools registered")

        # Run the MCP server
        if console:
            console.print("\n🎯 [bold cyan]Starting MCP server and waiting for requests...[/bold cyan]")
        else:
            logger.info("🎯 Starting MCP server and waiting for requests...")
        await mcp.run_async()

    except Exception as e:
        if console:
            console.print(f"\n[bold red]💥 Critical error in MCP server:[/bold red] {e}")
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        else:
            logger.error(f"💥 Error in MCP server: {e}")
            import traceback

            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # Use asyncio.run for proper async execution
    asyncio.run(main())
