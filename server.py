from fastmcp import FastMCP
from fastmcp.server.http import create_sse_app
import uvicorn
import os
import tempfile
import logging
import warnings

# Configure logging to reduce verbosity while keeping important info
logging.basicConfig(
    level=logging.INFO,  # Show info level and above
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Reduce httpx verbosity (very chatty)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Keep uvicorn connection logs but reduce access logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.INFO)

# Keep our app logs at info level for important events
logging.getLogger("app").setLevel(logging.INFO)

# Suppress specific deprecation warnings from websockets
warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings("ignore", message="websockets.server.WebSocketServerProtocol is deprecated")

# Suppress websockets deprecation warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

# Load instructions
def load_instructions(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "No instructions available"

instructions = load_instructions("docs/InstructionsMCP/api_instructions.md")

# Global variable to store auth token from HTTP headers
auth_token_file = os.path.join(tempfile.gettempdir(), "icards_auth_token.txt")

def get_auth_token():
    """Get auth token from env var or temp file."""
    # First try environment variable
    token = os.getenv("AUTH_TOKEN")
    if token:
        return token

    # Then try temp file (written by HTTP middleware)
    try:
        with open(auth_token_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

mcp = FastMCP(
    name="iCards",
    instructions=instructions
)

print("🚀 iCards MCP Server initialized successfully!")
print("📡 SSE endpoint will be available at: http://localhost:3001/sse")
print("🔧 Ready to handle MCP requests")
logging.info("iCards MCP Server startup completed")

# Import and register real iCards tools
try:
    from app.config.config import config
    from app.mcp.instructions import load_instructions
    from app.mcp.tools import register_icards_tools

    # Register the real iCards tools
    register_icards_tools(mcp)
    print("✅ iCards tools registered successfully")

except ImportError as e:
    print(f"⚠️ Could not load iCards tools: {e}")
    # Fallback: simple tools
    @mcp.tool()
    def ping() -> str:
        return "pong"

    @mcp.tool()
    def list_decks() -> str:
        return "Mock: deck1, deck2, deck3"


def main():
    # Check if SSE mode is requested (from env or command line)
    sse_port = os.getenv("SSE_PORT", "3001")

    if sse_port:
        # SSE mode
        app = create_sse_app(
            server=mcp,
            message_path="/messages",
            sse_path="/sse"
        )

    # Simple auth token extraction - do it once at startup from env
    auth_token = os.getenv("AUTH_TOKEN")
    if auth_token:
        try:
            with open(auth_token_file, 'w') as f:
                f.write(auth_token)
            logging.info(f"🔐 Auth token configured from environment ({len(auth_token)} chars)")
        except Exception as e:
            logging.error(f"❌ Error saving auth token: {e}")
    else:
        logging.warning("⚠️  No AUTH_TOKEN found in environment")

    # Don't use middleware for now - keep it simple

    # Log server startup
    logging.info(f"🚀 Starting iCards MCP Server on http://0.0.0.0:{sse_port}")
    logging.info(f"📡 SSE endpoint: http://0.0.0.0:{sse_port}/sse")
    logging.info(f"🛠️  MCP server ready to handle requests")

    # Run server with reduced logging
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(sse_port),
        log_level="warning",  # Reduce uvicorn logs
        access_log=False     # Disable access logs
    )


if __name__ == "__main__":
    main()
