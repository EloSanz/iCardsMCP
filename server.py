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
    from app.services.base_service import auth_token_ctx
    auth_token_ctx.set(token)
    logging.info(f"🔑 Token set globally ({len(token)} chars)")

# Import the context setter for use in tools
import app.services.base_service as base_service_module
base_service_module.set_current_auth_token = set_current_auth_token

class AuthTokenMiddleware:
    """
    ASGI Middleware to extract Authorization header and store token per connection.
    Implemented as pure ASGI to avoid BaseHTTPMiddleware streaming issues.
    """

    def __init__(self, app):
        self.app = app
        self.logged_no_auth = False

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        # Skip auth processing for specific paths
        path = scope.get("path", "")
        if path in ["/health", "/favicon.ico", "/sse"]:
            await self.app(scope, receive, send)
            return

        # Extract headers
        headers = dict(scope.get("headers", []))
        
        # Generate unique connection ID
        client = scope.get("client", ["unknown", 0])
        client_ip = client[0] if client else "unknown"
        
        # Get User-Agent from headers (bytes key)
        user_agent = headers.get(b"user-agent", b"unknown").decode("utf-8", errors="ignore")
        
        connection_id = f"{client_ip}_{hash(user_agent) % 10000}"
        
        # Get Auth header
        auth_header_bytes = headers.get(b"authorization")
        auth_header = auth_header_bytes.decode("utf-8", errors="ignore") if auth_header_bytes else None

        token = None
        if auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
            else:
                token = auth_header
                
            if token:
                set_auth_token_for_connection(connection_id, token)
                set_current_auth_token(token)
                # Store in scope state equivalent if possible, but for FastMCP/Starlette 
                # we primarily rely on our thread-local/contextvar storage for the tools
                logging.debug(f"🔐 Auth token received for connection {connection_id} (token length: {len(token)})")
        
        else:
            # Try to recover from existing context
            existing_token = get_auth_token_for_connection(connection_id)
            if existing_token:
                set_current_auth_token(existing_token)
                logging.debug(f"🔄 Restored auth token for connection {connection_id} from cache")
            elif not self.logged_no_auth:
                logging.debug(f"⚠️  No Authorization header for connection {connection_id}")
                # Don't set flag here to avoid missing logs for new connections, 
                # but keep at debug to reduce noise
        
        # Inject connection_id into state if possible (Starlette specific)
        # Since we are raw ASGI, we can modify scope['state'] if it exists, but typically 
        # Starlette initializes it. We'll rely on our ContextVars.
        
        await self.app(scope, receive, send)

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
    async def login(username: str, password: str, ctx: Context) -> dict:
        """Login to get JWT token for authentication."""
        try:
            import httpx
            from app.config.config import config
            
            base_url = config.get("API_BASE_URL")
            login_url = f"{base_url}/api/auth/login"
            
            logging.info(f"🔐 Attempting login for user {username} at {login_url}")
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        login_url,
                        json={"username": username, "password": password},
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        token = None
                        
                        # Extract token from response data
                        # Structure might be {success: true, data: {token: ...}} or direct
                        if "data" in data and isinstance(data["data"], dict) and "token" in data["data"]:
                            token = data["data"]["token"]
                            user_id = data["data"].get("userId") or data["data"].get("id")
                        elif "token" in data:
                            token = data["token"]
                            user_id = data.get("userId") or data.get("id")
                            
                        if token:
                            # Store token in connection context
                            # Get connection_id from context
                            connection_id = getattr(ctx.request.state, 'connection_id', None) if hasattr(ctx, 'request') and hasattr(ctx.request, 'state') else None
                            
                            if connection_id:
                                # Update connection-specific token
                                set_auth_token_for_connection(connection_id, token)
                                logging.info(f"✅ Login successful for {username}. Token stored for connection {connection_id}")
                                
                                # Also update global context just in case (though connection-specific is preferred)
                                set_current_auth_token(token)
                                
                                return {
                                    "success": True,
                                    "message": "Login successful",
                                    "user_id": user_id,
                                    "token_preview": f"{token[:10]}..."
                                }
                            else:
                                logging.warning(f"⚠️ Login successful but no connection_id found in context")
                                return {
                                    "success": False, 
                                    "message": "Login successful but context missing connection_id"
                                }
                        else:
                            logging.error(f"❌ Login response missing token: {data}")
                            return {"success": False, "message": "Invalid server response (no token)"}
                            
                    elif response.status_code == 401:
                        return {"success": False, "message": "Invalid credentials"}
                    else:
                        return {"success": False, "message": f"Server error: {response.status_code}"}
                        
                except httpx.RequestError as e:
                    logging.error(f"❌ Network error during login: {str(e)}")
                    return {"success": False, "message": f"Network error: {str(e)}"}
                    
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

    # Auth token check removed: We now rely purely on per-request tokens (via headers)
    # This ensures thread safety and supports multiple users via mcp-proxy
    logging.info("ℹ️  Authentication: Waiting for client tokens (Authorization: Bearer ...)")

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
