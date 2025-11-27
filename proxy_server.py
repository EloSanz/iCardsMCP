#!/usr/bin/env python3
"""
Simple proxy server using http.server to forward localhost:3000 requests to remote server.
"""
import http.server
import socketserver
import urllib.request
import urllib.parse
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Remote server URL
REMOTE_URL = "http://72.61.45.36:3000"

class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP proxy handler."""

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_PUT(self):
        self._proxy_request("PUT")

    def do_DELETE(self):
        self._proxy_request("DELETE")

    def _proxy_request(self, method):
        """Proxy the request to the remote server."""
        try:
            # Build remote URL
            path = self.path
            remote_url = REMOTE_URL + path

            logger.info(f"🚀 Proxying {method} {self.path} -> {remote_url}")

            # Get request body for POST/PUT
            content_length = int(self.headers.get('Content-Length', 0))
            body = None
            if content_length > 0:
                body = self.rfile.read(content_length)

            # Create request
            req = urllib.request.Request(remote_url, data=body, method=method)

            # Copy headers (except host)
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ['host', 'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade']:
                    req.add_header(header_name, header_value)

            # Make the request
            with urllib.request.urlopen(req) as response:
                # Send response back to client
                self.send_response(response.status)
                for header_name, header_value in response.headers.items():
                    self.send_header(header_name, header_value)
                self.end_headers()

                # Send response body
                self.wfile.write(response.read())

        except Exception as e:
            logger.error(f"❌ Proxy error: {str(e)}")
            self.send_error(500, f"Proxy error: {str(e)}")

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(format % args)

def run_proxy():
    """Run the proxy server."""
    PORT = 3000
    with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
        print(f"🚀 Starting proxy server on http://localhost:{PORT}")
        print(f"📡 Forwarding requests to {REMOTE_URL}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_proxy()
