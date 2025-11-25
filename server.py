from fastmcp import FastMCP
from fastmcp.server.http import create_sse_app
import uvicorn
import os
import tempfile
import logging
import warnings
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

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

def save_auth_token(token: str):
    """Save auth token to temp file."""
    try:
        with open(auth_token_file, 'w') as f:
            f.write(token)
        logging.info("✅ Auth token saved to temp file")
    except Exception as e:
        logging.error(f"❌ Error saving auth token: {e}")

def decode_jwt_payload(token: str) -> dict | None:
    """Decode JWT payload without verification to inspect contents."""
    try:
        # Decode without verification to see payload
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        logging.error(f"❌ Error decoding JWT: {str(e)}")
        return None

def get_auth_token():
    """Get auth token from env var or temp file."""
    # First try environment variable
    token = os.getenv("AUTH_TOKEN")
    if token:
        return token

    # Then try temp file (written by HTTP middleware)
    try:
        with open(auth_token_file, 'r') as f:
            token = f.read().strip()
            if token:
                logging.info(f"🔄 Using auth token from temp file ({len(token)} chars)")
                return token
    except FileNotFoundError:
        pass

    return None

class AuthTokenMiddleware(BaseHTTPMiddleware):
    """Middleware to extract Authorization header and save token."""

    def __init__(self, app):
        super().__init__(app)
        self.auth_token_logged = False

    async def dispatch(self, request, call_next):
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            save_auth_token(token)
            if not self.auth_token_logged:
                logging.info(f"🔍 Auth token received from client ({len(token)} chars)")
                self.auth_token_logged = True
        elif auth_header:
            # If it's not Bearer format, but some other auth
            token = auth_header
            save_auth_token(token)
            if not self.auth_token_logged:
                logging.info(f"🔍 Non-Bearer auth header received ({len(token)} chars)")
                self.auth_token_logged = True
        else:
            if not self.auth_token_logged:
                logging.warning("⚠️  No Authorization header in request")
                self.auth_token_logged = True

        response = await call_next(request)
        return response

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

    # Add debug tool for JWT token inspection
    @mcp.tool(
        name="debug_jwt_token",
        description="Debug JWT token to see userId and other claims"
    )
    async def debug_jwt_token() -> dict:
        """Debug the current JWT token to inspect its contents."""
        try:
            token = get_auth_token()
            if not token:
                return {"error": "No auth token found"}

            # Clean token (remove Bearer prefix if present)
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")

            payload = decode_jwt_payload(token)
            if not payload:
                return {"error": "Could not decode JWT token"}

            return {
                "success": True,
                "token_length": len(token),
                "payload": payload,
                "user_id": payload.get("userId"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "message": "This userId might not exist in the current database"
            }

        except Exception as e:
            logging.error(f"Error debugging JWT token: {str(e)}")
            return {"error": "Internal server error", "message": str(e)}

    print("✅ iCards tools registered successfully")
    logging.info("iCards MCP Server startup completed successfully")
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

        # Add auth token middleware to capture tokens from client headers
        app = AuthTokenMiddleware(app)

    # Check for auth token at startup (from env or existing temp file)
    auth_token = get_auth_token()
    if auth_token:
        logging.info(f"🔐 Auth token available ({len(auth_token)} chars)")
    else:
        logging.warning("⚠️  No AUTH_TOKEN found in environment or temp file")

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
