import random
import threading
from typing import List

import requests
from cryptography.fernet import Fernet

from domain.cryptocontainer import decrypt_message_using_sha256, encrypt_message_using_public_key
from domain.tor_message import decode_tor_message_for_final_node, decode_tor_message_for_intermediate_node, \
    encode_tor_message_for_final_node, \
    encode_tor_message_for_intermediate_node, is_final_node
from models.node import TorNode
from server_node import ServerNode

cheat = {}


# noinspection HttpUrlsUsage
class TorClient:
    def __init__(self, known_nodes: List[TorNode]):
        self.path = None
        self.sym_key = None
        self.known_nodes = known_nodes
        # Instantiates path and crypto
        self.refresh()

    def refresh(self, path_length=4):
        self.sym_key = Fernet.generate_key()
        self.path = self._generate_path(path_length=path_length)

    def _generate_path(self, path_length=4) -> List[TorNode]:
        return random.sample(self.known_nodes, k=path_length)

    def _send_message_to_node(self, http_message: str) -> str:
        tor_message = encode_tor_message_for_final_node(
            http_message,
            self.sym_key
        )

        tor_message = encrypt_message_using_public_key(tor_message, self.path[-1].public_key.encode("utf-8"))

        for node in self.path[::-1][1:]:
            tor_message = encode_tor_message_for_intermediate_node(tor_message, self.path[self.path.index(node)+1])
            tor_message = encrypt_message_using_public_key(tor_message, node.public_key.encode("utf-8"))

        return tor_message

    def send_http_message(self, message: str) -> str:
        response = self._send_message_to_node(message)
        request = requests.post(f"http://{self.path[0].ip}:{self.path[0].port}", response)

        return Fernet(self.sym_key).decrypt(request.text).decode()


