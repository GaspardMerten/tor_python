import re
import socketserver
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import requests
from cryptography.fernet import Fernet

from domain.cryptocontainer import CryptoContainer
from domain.tor_message import decode_tor_message_for_final_node, decode_tor_message_for_intermediate_node, \
    is_final_node


def send_http_request_from_raw_http_message(raw_http_message):
    regex = r"([A-Z]+)\s(\/.*)\sHTTP\/([1-2](?:.[0-2])?)\sHost:\s(.*)\s([\s\S]*)"

    match = re.match(regex, raw_http_message, re.MULTILINE)
    method = match.group(1)
    path = match.group(2)
    http_version = match.group(3)
    host = match.group(4)
    headers_and_body = match.group(5)

    protocol = "https"

    if http_version[0] == "1":
        protocol = "http"

    if "\r\n\r\n" in headers_and_body:
        raw_headers, body = headers_and_body.split("\r\n\r\n")
    else:
        raw_headers = headers_and_body
        body = None

    request_func = requests.get

    if method == "POST":
        request_func = requests.post
    elif method == "PUT":
        request_func = requests.put
    elif method == "DELETE":
        request_func = requests.delete

    headers = {}

    for header_line in raw_headers.splitlines():
        header_name, header_value = header_line.split(": ")
        headers[header_name] = header_value

    response = request_func(
        f"{protocol}://{host}{path}",
        headers=headers,
        data=body,
        timeout=10
    )

    return response_object_to_raw_http_message(response)


def response_object_to_raw_http_message(response):
    def format_headers(d):
        return '\n'.join(f'{k}: {v}' for k, v in d.items())

    return f"""{response.status_code} {response.reason} {response.url}\n{format_headers(response.headers)}\n\n{response.text}"""


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
        time.sleep(5)
        requests.post(f"http://{self.registry_address[0]}:{self.registry_address[1]}/add/{self.server_address[1]}")

    def get_request(self):
        return super().get_request()

    def handle_request(self) -> None:
        super().handle_request()

    def finish_request(self, request, client_address):
        self.http_handler(request, client_address, self, self.crypto)
