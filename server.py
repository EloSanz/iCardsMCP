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
        # Don't print to stdout - it breaks MCP JSON protocol
except ImportError:
    # Don't print to stdout - it breaks MCP JSON protocol
    pass

# Setup logging - ALWAYS to stderr to avoid breaking MCP JSON protocol on stdout
try:
    from rich.console import Console
    from rich.logging import RichHandler

    # CRITICAL: Console must use stderr=True to avoid breaking MCP protocol
    console = Console(stderr=True)

    # Configure rich logging to stderr only
    logging.basicConfig(
        level=logging.WARNING,  # Reduce verbosity for MCP
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=False, show_path=False)]
    )

    # Create custom logger
    logger = logging.getLogger("icards-mcp")
    logger.setLevel(logging.WARNING)  # Only warnings and errors

    # Disable noisy library loggers
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)

except ImportError:
    # Fallback to basic logging - ALWAYS to stderr
    console = None
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s:%(name)s:%(message)s",
        stream=sys.stderr  # CRITICAL: stderr only
    )
    logger = logging.getLogger(__name__)


async def validate_api_connection():
    """Validate API connection and token on startup."""
    try:
        base_url = (config.get("API_BASE_URL") or "http://localhost:3000").rstrip("/")
        timeout = config.get("API_TIMEOUT") or 30

        # Get auth token from environment
        import os

        auth_token = os.getenv("AUTH_TOKEN")

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            logger.error("❌ AUTH_TOKEN not configured!")
            if console:
                # Detectar si estamos en un entorno de producción/VPS
                is_production = os.getenv("SCOPE") == "prod" or not os.path.exists("/Users")  # Simple heuristic

                console.print("\n[bold red]🔑 AUTH_TOKEN Required:[/bold red]")
                console.print("The iCards MCP server requires authentication to access your flashcards.")
                console.print()

                if is_production:
                    console.print("[bold yellow]🚀 Production/VPS Environment:[/bold yellow]")
                    console.print("Set the AUTH_TOKEN environment variable:")
                    console.print("   [green]export AUTH_TOKEN='your_jwt_token_here'[/green]")
                    console.print("   [dim]Or configure it in your Docker/container environment[/dim]")
                    console.print()
                    console.print("[bold cyan]📋 To get your token:[/bold cyan]")
                    console.print("1. Login to your iCards API:")
                    console.print("   [cyan]curl -X POST https://your-api-domain.com/api/auth/login \\[/cyan]")
                    console.print("   [cyan]  -H 'Content-Type: application/json' \\[/cyan]")
                    console.print('   [cyan]  -d \'{"username": "your-username", "password": "your-password"}\'[/cyan]')
                    console.print("2. Copy the 'token' field from the JSON response")
                    console.print("3. Set AUTH_TOKEN=your_token_here")
                else:
                    console.print("[bold yellow]💻 Development Environment:[/bold yellow]")
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
                console.print("[bold red]❌ Cannot start without valid AUTH_TOKEN[/bold red]")
            else:
                logger.error("❌ AUTH_TOKEN environment variable is required but not set")
                logger.error("💡 Set AUTH_TOKEN=your_jwt_token_here in your environment")
            return False

        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # 1. Health check
            health_response = await client.get(f"{base_url}/api/health")
            health_response.raise_for_status()

            # 2. Token validation - try to get user decks
            decks_response = await client.get(f"{base_url}/api/decks")
            decks_response.raise_for_status()

        # Validation successful - only log to stderr if there's an issue
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
        # Initialize FastMCP server (silently)
        mcp = FastMCP("iCards 🎴")

        # Register all iCards tools (silently)
        register_icards_tools(mcp)

        # Check if SSE mode is requested
        sse_port = os.getenv("SSE_PORT")
        if sse_port:
            # SSE mode for HTTP proxy - start server first, validate later
            from fastmcp.server.http import create_sse_app

            # Create SSE app with proper paths
            app = create_sse_app(
                server=mcp,
                message_path="/messages",
                sse_path="/sse"
            )
            import uvicorn

            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=int(sse_port),
                log_level="error"  # Minimize logs
            )
            server = uvicorn.Server(config)

            # Start SSE server in background and validate API
            import asyncio
            async def validate_and_log():
                await asyncio.sleep(1)  # Wait a bit for server to start
                if not await validate_api_connection():
                    # Log error but don't exit - server is already running
                    logger.error("⚠️ API validation failed - server running but API unavailable")

            # Start validation in background
            asyncio.create_task(validate_and_log())

            # Start the server
            await server.serve()
        else:
            # Default stdio mode - validate first
            if not await validate_api_connection():
                # Only log errors to stderr
                logger.error("💥 API validation failed - MCP server will not start")
                sys.exit(1)

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
