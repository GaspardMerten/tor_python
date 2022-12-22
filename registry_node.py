import json
import socketserver
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List

import requests

from domain.cryptocontainer import CryptoContainer
from models.node import TorNode

MAX_NODE_PUBLIC_KEY_ATTEMPT = 2


# noinspection HttpUrlsUsage
class RegistryNodeHTTPHandler(socketserver.ThreadingMixIn, BaseHTTPRequestHandler):
    """
    A simple http handler that acts as a node registry for the tor network. It is quite
    primitive as it is not able to sink itself wit other registires (making the network
    centralized, but it is a good start).

    It has four endpoints:

        - GET /: returns a json object containing the ip and port of all the nodes in the
        network and their public key.

        - POST /add/<port>: adds a node to the list of nodes based on a request from that given node
        (only the node can be specified in the request, the ip used will be the one used to send the request).
        The idea behind this is to prevent one ip from registering multiple nodes without even having to change ip.

        - GET /remove/<port>: removes a node from the list of nodes based on a request from that given node

        - GET /check/<ip>:<port>: checks if a node is still alive and removes it from the list of nodes if it is not.
        If it is not, it will also remove the node from the list of nodes. This method can be called by anyone
        contrary to the previous two.
    """

    def __init__(
        self,
        request: bytes,
        client_address: tuple[str, int],
        server: socketserver.BaseServer,
        nodes: List[TorNode],
    ):
        self.nodes = nodes
        super().__init__(request, client_address, server)

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
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
            self.nodes = [
                node for node in self.nodes if node.ip != ip and node.port != port
            ]
            self.send_response(200)
            self.end_headers()
        elif self.path[:6] == "/check/":
            # extract ip and port from request path
            ip, port = self.path[6:].split(":")
            node_public_key = self._retrieve_public_key_from_node(ip, port)

            if not node_public_key:
                # remove node from nodes
                self.nodes = [
                    node for node in self.nodes if node.ip != ip and node.port != port
                ]
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
            public_key = requests.get(f"http://{ip}:{port}/key", timeout=2).text
        except requests.exceptions.ConnectionError:
            if n < MAX_NODE_PUBLIC_KEY_ATTEMPT:
                self._retrieve_public_key_from_node(ip, port, n + 1)
            public_key = None
        return public_key


class RegistryNode(HTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        private_key_path=None,
        public_key_path=None,
    ):
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


if __name__ == "__main__":
    registry_node = RegistryNode((sys.argv[1], int(sys.argv[2])))
    registry_node.serve_forever()
