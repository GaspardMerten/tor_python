import random
import requests
from typing import List, Tuple

from cryptography.fernet import Fernet

from domain.cryptocontainer import encrypt_message_using_public_key
from domain.tor_message import encode_tor_message_for_final_node, \
    encode_tor_message_for_intermediate_node
from models.node import TorNode

cheat = {}


# noinspection HttpUrlsUsage
class TorClient:
    """
        This class is responsible for sending messages through the Tor network.
        It uses the registry to retrieve the list of nodes and then builds a path of nodes to send the message through.
        It also encrypts the message using the onion encryption method (layer by layer encryption).
    """

    def __init__(self, registry_address: Tuple[str, int]):
        self.path = None
        self.sym_key = None
        self.known_nodes = []
        self.registry_address = registry_address
        # Instantiates path and crypto
        self.refresh()

    def refresh(self, path_length=3):
        """
        Refreshes the path and the crypto key used to encrypt the message.

        :param path_length:  The length of the path to build. Should probably be 3 all the time (more than 3 is not
        recommended since it should not result in more security).
        """

        # retrieve nodes from registry
        nodes_data = requests.get(f"http://{self.registry_address[0]}:{self.registry_address[1]}", timeout=1).json()

        # extract nodes from nodes_data
        self.known_nodes = [TorNode(*address.split(":"), public_key) for address, public_key in nodes_data.items()]

        self.sym_key = Fernet.generate_key()
        self.path = self._generate_path(path_length=path_length)

    def _generate_path(self, path_length=4) -> List[TorNode]:
        return random.sample(self.known_nodes, k=path_length)

    def _build_message(self, http_message: str) -> Tuple[str, List[str]]:
        """
        Builds the message to send through the Tor network.
        """
        tor_message = encode_tor_message_for_final_node(
            http_message
        )
        print("h")

        tor_message, first_sym_key = encrypt_message_using_public_key(tor_message,
                                                                      self.path[-1].public_key.encode("utf-8"))
        print("hi")

        sym_keys = [first_sym_key]

        for node in self.path[::-1][1:]:
            tor_message = encode_tor_message_for_intermediate_node(tor_message, self.path[self.path.index(node) + 1])
            tor_message, sym_key = encrypt_message_using_public_key(tor_message, node.public_key.encode("utf-8"))
            sym_keys.append(sym_key)
        print("hio")

        return tor_message, sym_keys

    def send_http_message(self, message: str) -> str:
        """
            Sends a message through the Tor network.
        """
        print(message)
        tor_message, sym_keys = self._build_message(message)
        print(tor_message)
        request = requests.post(f"http://{self.path[0].ip}:{self.path[0].port}", tor_message, timeout=5)
        response = request.text

        for sym_key in sym_keys[::-1]:
            response = Fernet(sym_key).decrypt(response.encode("utf-8")).decode("utf-8")
        print(response)
        return response
