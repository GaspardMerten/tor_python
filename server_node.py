import socketserver
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import requests
from cryptography.fernet import Fernet

from domain.cryptocontainer import CryptoContainer
from domain.http_message import send_http_request_from_raw_http_message
from domain.tor_message import decode_tor_message_for_final_node, decode_tor_message_for_intermediate_node, \
    is_final_node


# noinspection HttpUrlsUsage
class ServerNodeHTTPHandler(socketserver.ThreadingMixIn, BaseHTTPRequestHandler):
    """
        A tor node http handler that handles the http requests from the client and the intermediate nodes.
        It decrypts the message, sends it to the next node and encrypts the response.
        Or when it is an exit node, it sends the message to the server and encrypts the response and sends
        it to the previous node.

        The handler has multiple endpoints:

        - /key: returns the public key of the node
        - (POST) /: handles the http request from the client or the intermediate node

    """
    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer,
                 crypto: CryptoContainer):
        self.crypto = crypto
        super().__init__(request, client_address, server)

    def do_GET(self):
        # check if path is public key
        if self.path == "/key":
            self.send_response(200)
            self.send_header('Content-type', 'application/x-pem-file')
            self.end_headers()
            self.wfile.write(self.crypto.get_public_key_bytes())
        elif self.path == "":
            self.send_response(200)

    def do_POST(self):
        # Retrieve body in string
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode("utf-8")

        # Decrypt body
        decrypted_body, sym_key = self.crypto.decrypt(body)

        self.send_response(200)

        if is_final_node(decrypted_body):
            http_message = decode_tor_message_for_final_node(decrypted_body)
            # Send http message to server
            response = send_http_request_from_raw_http_message(http_message)
            # Encrypt response using extracted public key
        else:
            next_node, http_message = decode_tor_message_for_intermediate_node(decrypted_body)
            response = requests.post(f"http://{next_node}", http_message).text
        encrypted_response = Fernet(sym_key).encrypt(response.encode("utf-8"))
        self.send_header("Content-length", str(len(encrypted_response)))
        self.end_headers()
        self.wfile.write(encrypted_response)


class ServerNode(HTTPServer):
    def __init__(self, server_address: tuple[str, int], registry_address: tuple[str, int], private_key_path=None,
                 public_key_path=None):
        super().__init__(server_address, ServerNodeHTTPHandler)

        self.crypto = CryptoContainer(private_key_path, public_key_path)
        self.http_handler = ServerNodeHTTPHandler
        self.registry_address = registry_address

        # make a request asynchronously to the registry to register the node
        Thread(target=self.register_node).start()

    def register_node(self):
        time.sleep(1)
        requests.post(f"http://{self.registry_address[0]}:{self.registry_address[1]}/add/{self.server_address[1]}")

    def get_request(self):
        return super().get_request()

    def handle_request(self) -> None:
        super().handle_request()

    def finish_request(self, request, client_address):
        self.http_handler(request, client_address, self, self.crypto)
