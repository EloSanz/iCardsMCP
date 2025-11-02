#!/usr/bin/env python3
"""
Simple test MCP server to verify Claude connection
"""

import sys
import os
import json

# Simple MCP server implementation
def send_message(message):
    """Send a message to stdout as JSON-RPC"""
    json_message = json.dumps(message)
    sys.stdout.write(f"Content-Length: {len(json_message)}\r\n\r\n{json_message}")
    sys.stdout.flush()

def read_message():
    """Read a message from stdin"""
    # Read Content-Length header
    line = sys.stdin.readline().strip()
    if not line.startswith("Content-Length: "):
        return None

    length = int(line.split(": ")[1])

    # Read empty line
    sys.stdin.readline()

    # Read JSON content
    content = sys.stdin.read(length)
    return json.loads(content)

def main():
    # Send initialize response
    send_message({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "Test iCards",
                "version": "1.0.0"
            }
        }
    })

    # Main message loop
    while True:
        try:
            message = read_message()
            if message is None:
                break

            if message.get("method") == "tools/list":
                # Respond to tools/list request
                send_message({
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": {
                        "tools": [
                            {
                                "name": "hello_world",
                                "description": "A simple hello world tool",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Name to greet",
                                            "default": "World"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                })
            elif message.get("method") == "tools/call":
                # Handle tool call
                tool_name = message["params"]["name"]
                args = message["params"].get("arguments", {})

                if tool_name == "hello_world":
                    name = args.get("name", "World")
                    result = f"Hello, {name}! This is a test MCP server."

                    send_message({
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result
                                }
                            ]
                        }
                    })
                else:
                    send_message({
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "error": {
                            "code": -32601,
                            "message": f"Method '{tool_name}' not found"
                        }
                    })

        except Exception as e:
            # Send error response
            send_message({
                "jsonrpc": "2.0",
                "id": message.get("id", 1) if 'message' in locals() else 1,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            })

if __name__ == "__main__":
    main()