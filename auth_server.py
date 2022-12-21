import json
import socketserver
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

from domain.cryptocontainer import CryptoContainer

# The number of times the server will try to retrieve the public key from a given node.
# The higher, the longer it will take to discover that a node is down.
MAX_NODE_PUBLIC_KEY_ATTEMPT = 5


# noinspection HttpUrlsUsage
class AuthServerHTTPHandler(socketserver.ThreadingMixIn, BaseHTTPRequestHandler):
    """
        A very simple HTTP server that only handles GET and POST requests. It exposes a
        /private and /auth endpoint.

        The /private endpoint requires a token to be passed
        to return the secret message (through the Token http header).
        If no token is passed, the server will return a 403 error.

        The /auth endpoint requires a username and password
        to return a token.

        This server is in no way a real authentication server, a framework like Django should
        be used to offer a real authentication server for instance using the django rest framework.
    """

    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer,
                 user_tokens: dict):
        self.user_tokens = user_tokens
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path[:8] == "/private":
            token = self.headers.get("Token", None)
            if token and token in self.user_tokens:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                self.wfile.write(
                    json.dumps({"data": f"Secret for your eyes only ;) Hello {self.user_tokens[token]}"}).encode(
                        "utf-8"))
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write("Unauthorized".encode("utf-8"))

    def do_POST(self):
        # adds a node to the list of node based on a request from that given node
        if self.path == "/auth":
            # get body from post request
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            body_json = json.loads(body)
            if body_json.get("username", None) == "gaspard" and body_json.get("password", None) == "mypassword":
                self.send_response(202)
                self.send_header('Content-type', 'application/json')

                token = str(uuid.uuid4())
                content = json.dumps(dict(token=token)).encode("utf-8")
                self.user_tokens[token] = "gaspard"

                self.send_header('Content-length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        self.send_response(404)
        self.end_headers()


class AuthServerNode(HTTPServer):
    """
        The node using the AuthServerHttpHandler as its http handler. Stores
        the user tokens for a session.
    """

    def __init__(self, server_address: tuple[str, int], private_key_path=None,
                 public_key_path=None):
        super().__init__(server_address, AuthServerHTTPHandler)

        self.crypto = CryptoContainer(private_key_path, public_key_path)
        self.http_handler = AuthServerHTTPHandler
        self.user_tokens = {}

    def get_request(self):
        return super().get_request()

    def handle_request(self) -> None:
        super().handle_request()

    def finish_request(self, request, client_address):
        self.http_handler(request, client_address, self, self.user_tokens)
