from typing import List, Tuple

from cryptography.fernet import Fernet

from domain.crypto import encrypt_message_using_public_key
from models.node import TorNode

__all__ = (
    "encode_tor_message_for_final_node",
    "decode_tor_message_for_intermediate_node",
    "encode_tor_message_for_intermediate_node",
    "decode_tor_message_for_final_node",
    "is_final_node",
    "create_onion_message",
    "peel_response"
)


def encode_tor_message_for_final_node(message: str) -> str:
    """
    Encode a message to be sent to the final node, 1 is the flag for the final node
    """
    return f"1\n" + message


def encode_tor_message_for_intermediate_node(
    encrypted_message: str, next_node: TorNode
) -> str:
    """
    Encode a message to be sent to the next node, 0 is the flag for the intermediate node
    After the 0, the next node address is written, then the encrypted message just after exactly one line break.
    """
    return f"0\n{next_node.ip}:{next_node.port}\n" + encrypted_message


def is_final_node(tor_message: str) -> bool:
    """
    Check if the message is for the final node or not
    """
    return tor_message[0] == "1"


def decode_tor_message_for_final_node(tor_message: str) -> str:
    """
    Decode a message for the final node
    """
    tor_message = tor_message[2:]
    return tor_message


def decode_tor_message_for_intermediate_node(tor_message: str) -> Tuple[str, str]:
    """
    Decode a message for the intermediate node.
    The message is split into 2 parts, the first part is the next node address, the
    second part is the encrypted message to be sent to the next node.
    """

    tor_message = tor_message[2:]
    first_line_end_index = tor_message.find("\n")
    next_node = tor_message[:first_line_end_index]
    http_message = tor_message[first_line_end_index + 1 :]

    return next_node, http_message


def peel_response(response, sym_keys) -> str:
    """
    Peels the response from the final node to get the original message.

    To achieve this, the response is decrypted using the symmetric keys in the reverse order.
    """
    for sym_key in sym_keys[::-1]:
        response = Fernet(sym_key).decrypt(response.encode("utf-8")).decode("utf-8")
    return response


def create_onion_message(
    path: List[TorNode], http_message: str
) -> tuple[list[bytes], str]:
    """
    Creates the onion message to send through the Tor network.

    To achieve this, the message is encrypted using the symmetric keys in the reverse order (path speaking, last to first).
    """
    tor_message = encode_tor_message_for_final_node(http_message)
    tor_message, first_sym_key = encrypt_message_using_public_key(
        tor_message, path[-1].public_key.encode("utf-8")
    )
    sym_keys = [first_sym_key]

    for node in path[::-1][1:]:
        tor_message = encode_tor_message_for_intermediate_node(
            tor_message, path[path.index(node) + 1]
        )
        tor_message, sym_key = encrypt_message_using_public_key(
            tor_message, node.public_key.encode("utf-8")
        )
        sym_keys.append(sym_key)

    return sym_keys, tor_message
