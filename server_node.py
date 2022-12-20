import socket
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from cryptography.fernet import Fernet

from domain.cryptocontainer import CryptoContainer
from domain.tor_message import decode_tor_message_for_final_node, decode_tor_message_for_intermediate_node, \
    is_final_node


def send_http_request_from_raw_http_message(raw_http_message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # retrieve ip and port from raw http message
        host, port = raw_http_message.split('Host: ')[1].split('\r\n')[0].split(':')

        # connect to server
        sock.connect((host, int(port)))

        # send http request
        sock.sendall(raw_http_message.encode('utf-8'))

        response = ""

        while True:
            response += sock.recv(4096).decode('utf-8')
            if response.endswith('\r\n\r\n'):
                break
    finally:
        sock.close()

    return response


# noinspection HttpUrlsUsage
class ServerNodeHTTPHandler(socketserver.ThreadingMixIn, BaseHTTPRequestHandler):
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
        decrypted_body = self.crypto.decrypt(body)

        self.send_response(200)

        if is_final_node(decrypted_body):
            sym_key, http_message = decode_tor_message_for_final_node(decrypted_body)
            # Send http message to server
            response = send_http_request_from_raw_http_message(http_message)
            # Encrypt response using extracted public key
            encrypted_response = Fernet(sym_key).encrypt(response.encode("utf-8"))
            self.send_header("Content-length", str(len(encrypted_response)))
            self.end_headers()

            self.wfile.write(encrypted_response)
        else:
            next_node, http_message = decode_tor_message_for_intermediate_node(decrypted_body)
            next_node_response = requests.post(f"http://{next_node}", http_message)

            self.send_header("Content-length", str(len(next_node_response.content)))
            self.end_headers()
            self.wfile.write(next_node_response.content)


class ServerNode(HTTPServer):
    def __init__(self, server_address: tuple[str, int], private_key_path=None, public_key_path=None):
        super().__init__(server_address, ServerNodeHTTPHandler)

        self.crypto = CryptoContainer(private_key_path, public_key_path)
        self.http_handler = ServerNodeHTTPHandler

    def get_request(self):
        return super().get_request()

    def handle_request(self) -> None:
        super().handle_request()

    def finish_request(self, request, client_address):
        self.http_handler(request, client_address, self, self.crypto)
