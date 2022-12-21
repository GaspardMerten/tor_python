import json
import re
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List

import requests
from cryptography.fernet import Fernet

from domain.cryptocontainer import CryptoContainer
from domain.tor_message import decode_tor_message_for_final_node, decode_tor_message_for_intermediate_node, \
    is_final_node
from models.node import TorNode

MAX_NODE_PUBLIC_KEY_ATTEMPT = 2


# noinspection HttpUrlsUsage
class RegistryNodeHTTPHandler(socketserver.ThreadingMixIn, BaseHTTPRequestHandler):
    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer,
                 nodes: List[TorNode]):
        self.nodes = nodes
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            nodes_data = {}

            for node in self.nodes:
                nodes_data[f"{node.ip}:{node.port}"] = node.public_key

            self.wfile.write(json.dumps(nodes_data).encode("utf-8"))
        elif self.path[:8] == "/remove/":
            # extract ip and port from request
            ip = self.client_address[0]
            port = int(self.path[8:])

            # remove node from list
            self.nodes = [node for node in self.nodes if node.ip != ip and node.port != port]
            self.send_response(200)
            self.end_headers()
        elif self.path[:6] == "/check/":
            # extract ip and port from request path
            ip, port = self.path[6:].split(":")
            node_public_key = self._retrieve_public_key_from_node(ip, port)

            if not node_public_key:
                # remove node from nodes
                self.nodes = [node for node in self.nodes if node.ip != ip and node.port != port]
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # adds a node to the list of node based on a request from that given node
        if self.path[:5] == "/add/":
            # extract ip and port from request
            ip = self.client_address[0]
            port = int(self.path[5:])
            # retrieve public key from node
            public_key = self._retrieve_public_key_from_node(ip, port)

            if public_key:
                # add node to list
                self.nodes.append(TorNode(ip, port, public_key))
                self.send_response(200)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _retrieve_public_key_from_node(self, ip, port, n=0):
        try:
            print(f"Retrieving n == {n} public key from {ip}:{port}")
            public_key = requests.get(f"http://{ip}:{port}/key", timeout=2).text
        except requests.exceptions.ConnectionError:
            if n < MAX_NODE_PUBLIC_KEY_ATTEMPT:
                self._retrieve_public_key_from_node(ip, port, n + 1)
            public_key = None
        return public_key


class RegistryNode(HTTPServer):
    def __init__(self, server_address: tuple[str, int], private_key_path=None,
                 public_key_path=None):
        super().__init__(server_address, RegistryNodeHTTPHandler)

        self.crypto = CryptoContainer(private_key_path, public_key_path)
        self.http_handler = RegistryNodeHTTPHandler
        self.nodes: List[TorNode] = []

    def get_request(self):
        return super().get_request()

    def handle_request(self) -> None:
        super().handle_request()

    def finish_request(self, request, client_address):
        self.http_handler(request, client_address, self, self.nodes)
