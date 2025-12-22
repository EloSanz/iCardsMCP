from fastmcp import FastMCP
from fastmcp.server.http import create_sse_app
from fastmcp.server.context import Context
import uvicorn
import os
import tempfile
import logging
import warnings
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from app.mcp.token_utils import (
    set_auth_token_for_connection,
    get_auth_token_for_connection,
    set_current_auth_token,
    get_auth_token
)

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

def decode_jwt_payload(token: str) -> dict | None:
    """Decode JWT payload without verification to inspect contents."""
    try:
        # Decode without verification to see payload
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        logging.error(f"❌ Error decoding JWT: {str(e)}")
        return None

def set_current_auth_token(token: str):
    """Set the auth token globally."""
    from app.services.base_service import current_auth_token
    import app.services.base_service as bs
    bs.current_auth_token = token
    logging.info(f"🔑 Token set globally ({len(token)} chars)")

# Import the context setter for use in tools
import app.services.base_service as base_service_module
base_service_module.set_current_auth_token = set_current_auth_token

class AuthTokenMiddleware(BaseHTTPMiddleware):
    """Middleware to extract Authorization header and store token per connection."""

    def __init__(self, app):
        super().__init__(app)
        self.connection_counter = 0
        self.logged_no_auth = False

    async def dispatch(self, request, call_next):
        # Only process requests that might have auth headers (not SSE endpoint)
        path = request.url.path

        # Skip auth processing for SSE endpoint and health checks
        if path in ["/sse", "/health", "/favicon.ico"]:
            return await call_next(request)

        # Generate unique connection ID for this request
        # Use client IP + user agent as connection identifier
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        connection_id = f"{client_ip}_{hash(user_agent) % 10000}"

        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            set_auth_token_for_connection(connection_id, token)
            set_current_auth_token(token)  # Set globally for immediate use
            # Add connection ID to request state for later use
            request.state.connection_id = connection_id
            logging.info(f"🔐 Auth token received for connection {connection_id} (token length: {len(token)})")
        elif auth_header:
            # If it's not Bearer format, but some other auth
            token = auth_header
            set_auth_token_for_connection(connection_id, token)
            set_current_auth_token(token)  # Set globally for immediate use
            request.state.connection_id = connection_id
            logging.info(f"🔐 Non-Bearer auth header received for connection {connection_id} (token length: {len(token)})")
        else:
            # No auth header - still assign connection ID for tracking
            request.state.connection_id = connection_id
            if not self.logged_no_auth:
                logging.warning(f"⚠️  No Authorization header in request for connection {connection_id}")
                self.logged_no_auth = True

        response = await call_next(request)
        return response

mcp = FastMCP(
    name="iCards",
    instructions=instructions
)

print("🚀 iCards MCP Server initialized successfully!")
print("📡 SSE endpoint will be available at: http://localhost:8081/sse")
print("🔧 Ready to handle MCP requests")
logging.info("iCards MCP Server startup completed")

# Import and register real iCards tools
try:
    from app.config.config import config
    from app.mcp.instructions import load_instructions
    from app.mcp.tools import register_icards_tools

    # Register the real iCards tools
    register_icards_tools(mcp)

    # Add login tool for authentication
    @mcp.tool(
        name="login",
        description="Login with username and password to get JWT token"
    )
    async def login(username: str, password: str) -> dict:
        """Login to get JWT token for authentication."""
        try:
            # For testing, accept admin/admin123
            if username == "admin" and password == "admin123":
                # Create a test JWT token (this is just for testing)
                import time
                import jwt

                payload = {
                    "userId": 1,
                    "username": username,
                    "iat": int(time.time()),
                    "exp": int(time.time()) + 86400  # 24 hours
                }

                # Use a test secret (in production this would be from env)
                test_secret = "test_secret_key_for_development_only"
                token = jwt.encode(payload, test_secret, algorithm="HS256")

                logging.info(f"✅ Login successful for user {username}")
                return {
                    "success": True,
                    "message": "Login successful",
                    "token": token,
                    "user_id": payload["userId"],
                    "expires_in": 86400
                }
            else:
                return {
                    "success": False,
                    "message": "Invalid credentials"
                }

        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            return {"error": "Internal server error", "message": str(e)}

    # Add debug tool for JWT token inspection
    @mcp.tool(
        name="debug_jwt_token",
        description="Debug JWT token to see userId and other claims"
    )
    async def debug_jwt_token(ctx: Context) -> dict:
        """Debug the current JWT token to inspect its contents."""
        try:
            # Try to get token from current connection context
            connection_id = getattr(ctx.request.state, 'connection_id', None) if hasattr(ctx, 'request') and hasattr(ctx.request, 'state') else None
            token = None

            if connection_id:
                token = get_auth_token_for_connection(connection_id)
                logging.info(f"🔍 Debug: Found token for connection {connection_id}")

            if not token:
                token = get_auth_token()  # Fallback to env
                logging.info("🔍 Debug: Using env token as fallback")

            if not token:
                return {"error": "No auth token found", "connection_id": connection_id}

            # Clean token (remove Bearer prefix if present)
            if token.startswith("Bearer "):
                token = token.replace("Bearer ", "")

            payload = decode_jwt_payload(token)
            if not payload:
                return {"error": "Could not decode JWT token"}

            return {
                "success": True,
                "token_length": len(token),
                "connection_id": connection_id,
                "token_source": "connection_context" if connection_id else "environment",
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
    logging.info("iCards MCP Server startup completed successfully :D")
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
    sse_port = os.getenv("SSE_PORT", "8081")

    if sse_port:
        # SSE mode
        app = create_sse_app(
            server=mcp,
            message_path="/messages",
            sse_path="/sse"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add auth token middleware to capture tokens from client headers
        app = AuthTokenMiddleware(app)

    # Check for auth token at startup (from env only - tokens come from MCP requests)
    auth_token = os.getenv("AUTH_TOKEN")
    if auth_token:
        logging.info(f"🔐 Auth token available from environment ({len(auth_token)} chars)")
    else:
        logging.info("ℹ️  No AUTH_TOKEN in environment - tokens will come from MCP client requests")

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
