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
from app.mcp.instructions import load_instructions
from app.mcp.tools import register_icards_tools

# Load environment variables from .env (but don't override existing ones from Claude config)
try:
    env_file = ".env"
    if os.path.exists(env_file):
        # override=False means: only set if not already set (Claude config has priority)
        load_dotenv(env_file, override=False)
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
        level=logging.INFO,  # Show INFO level for debugging
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=False, show_path=False)]
    )

    # Create custom logger
    logger = logging.getLogger("icards-mcp")
    logger.setLevel(logging.INFO)  # Show info messages

    # Disable noisy library loggers but keep app loggers
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("mcp.server.transport_security").setLevel(logging.ERROR)  # Silence Content-Type warnings
    logging.getLogger("app").setLevel(logging.INFO)  # Enable app logs

except ImportError:
    # Fallback to basic logging - ALWAYS to stderr
    console = None
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
        stream=sys.stderr  # CRITICAL: stderr only
    )
    logger = logging.getLogger(__name__)
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("mcp.server.transport_security").setLevel(logging.ERROR)


async def validate_api_connection():
    """Validate API connection and token on startup."""
    try:
        # Get configuration directly from environment variables (same as main())
        base_url = os.getenv("API_BASE_URL", "http://localhost:3000").rstrip("/")
        timeout = int(os.getenv("API_TIMEOUT", "30"))
        auth_token = os.getenv("AUTH_TOKEN")

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            logger.error("❌ AUTH_TOKEN not configured!")
            if console:
                console.print("\n[bold red]🔑 AUTH_TOKEN Required:[/bold red]")
                console.print("The iCards MCP server requires authentication to access your flashcards.")
                console.print()
                console.print("[bold yellow]🚀 Production Environment:[/bold yellow]")
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

        # Validation successful - log success
        if console:
            console.print("[bold green]✓ API connection validated successfully[/bold green]")
            console.print(f"[dim]  Connected to: {base_url}[/dim]\n")
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
        # Log startup info with environment variables
        api_base_url = os.getenv("API_BASE_URL", "")
        auth_token = os.getenv("AUTH_TOKEN", "")

        if console:
            console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
            console.print("[bold green]🎴 iCards MCP Server[/bold green]")
            console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
            console.print(f"[cyan]🔗 API Base URL:[/cyan]   [blue]{api_base_url or 'Not configured'}[/blue]")
            console.print(f"[cyan]🔑 Auth Token:[/cyan]     [green]{'✓ Configured' if auth_token else '✗ Missing'}[/green]")
            console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")
        
        # Load instructions from config (uses external shared instructions file)
        instructions_path = config.get("MCP_ICARDS_INSTRUCTIONS_PATH")
        instructions = load_instructions(instructions_path)
        
        if console:
            if instructions:
                console.print(f"[green]📖 Instructions loaded: {len(instructions)} chars[/green]")
            else:
                console.print(f"[yellow]⚠️  No instructions loaded from {instructions_path}[/yellow]")
        
        # Initialize FastMCP server with instructions
        mcp = FastMCP("iCards 🎴", instructions=instructions)
        
        # IMPORTANT: Expose instructions as a resource so Claude can access them
        @mcp.resource("instructions://assistant-rules")
        def get_assistant_instructions() -> str:
            """
            Critical instructions for the AI assistant.
            These rules MUST be followed in ALL interactions.
            """
            logger.info("📖 Claude is reading the instructions resource!")
            return instructions
        
        # ALSO: Create a prompt to remind the assistant to read instructions
        @mcp.prompt()
        def read_assistant_instructions():
            """
            Prompt to ensure the AI assistant reads and follows the server instructions.
            Use this before starting interactions to ensure proper behavior.
            """
            return """
Please read the complete instructions from the resource 'instructions://assistant-rules'.

These instructions contain:
- Critical behavior rules you MUST follow
- API documentation and capabilities
- Response formatting guidelines
- Communication style expectations

Make sure to follow ALL the rules specified in those instructions for every interaction.
"""
        
        # Register all iCards tools (silently)
        register_icards_tools(mcp)
        
        if console:
            console.print("[bold green]✅ All iCards tools registered successfully[/bold green]\n")

        # Check if SSE mode is requested, default to SSE mode for local development
        sse_port = os.getenv("SSE_PORT", "3001")  # Default to SSE mode
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

            uvicorn_config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=int(sse_port),
                log_level="info",  # Show all HTTP requests
                access_log=True    # Enable access logging
            )
            server = uvicorn.Server(uvicorn_config)

            # Start SSE server in background and validate API
            import asyncio
            async def validate_and_log():
                await asyncio.sleep(1)  # Wait a bit for server to start
                if not await validate_api_connection():
                    # Log error but don't exit - server is already running
                    logger.error("⚠️ API validation failed - server running but API unavailable")

            # Start validation in background
            asyncio.create_task(validate_and_log())

            # Log SSE server start
            if console:
                console.print("[bold cyan]🌐 Starting SSE Server[/bold cyan]")
                console.print(f"[green]   • Server:[/green]   http://0.0.0.0:{sse_port}")
                console.print(f"[green]   • SSE:[/green]      http://0.0.0.0:{sse_port}/sse")
                console.print(f"[green]   • Messages:[/green] http://0.0.0.0:{sse_port}/messages")
                console.print("[yellow]   • Logs:[/yellow]    You'll see HTTP requests below\n")
            
            # Start the server
            await server.serve()
        else:
            # Default stdio mode - skip API validation since MCP client handles connection
            # The MCP client (Cursor/Claude) will handle API communication through tools
            if console:
                console.print("[bold cyan]🔌 Starting STDIO transport[/bold cyan]")
                console.print("[dim]   Waiting for client connection...[/dim]\n")

            await mcp.run_async()
            
            if console:
                console.print("\n[yellow]👋 Client disconnected[/yellow]")

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
