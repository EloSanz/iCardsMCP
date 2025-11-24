# icards/server.py

from fastmcp import FastMCP
import os
import argparse
from urllib.parse import urlparse

# Load instructions
def load_instructions(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "No instructions available"

instructions = load_instructions("docs/InstructionsMCP/api_instructions.md")

mcp = FastMCP(
    name="iCards",
    instructions=instructions
)

# Tool de ejemplo
@mcp.tool()
def ping() -> str:
    return "pong"


def main():
    parser = argparse.ArgumentParser(description="iCards MCP Server")
    parser.add_argument(
        "url",
        nargs="?",
        default="http://localhost:3001/sse",
        help="URL where the MCP server is accessible"
    )

    args = parser.parse_args()

    # Parse the URL to extract host and port
    parsed = urlparse(args.url)
    os.environ["SSE_PORT"] = str(parsed.port or 3001)

    # Check if SSE mode is requested
    sse_port = os.environ.get("SSE_PORT")
    if sse_port:
        # SSE mode
        from fastmcp.server.http import create_sse_app
        import uvicorn

        app = create_sse_app(
            server=mcp,
            message_path="/messages",
            sse_path="/sse"
        )

        uvicorn_config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=int(sse_port),
            log_level="error"
        )
        server = uvicorn.Server(uvicorn_config)
        import asyncio
        asyncio.run(server.serve())
    else:
        # stdio server
        mcp.run_stdio()


if __name__ == "__main__":
    main()
