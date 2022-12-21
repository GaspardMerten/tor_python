from typing import Tuple

from models.node import TorNode


def encode_tor_message_for_final_node(message: str) -> str:
    return f"1\n" + message


def encode_tor_message_for_intermediate_node(encrypted_message: str, next_node: TorNode) -> str:
    return f"0\n{next_node.ip}:{next_node.port}\n" + encrypted_message


def is_final_node(tor_message: str):
    return tor_message[0] == "1"


def decode_tor_message_for_final_node(tor_message: str) -> str:
    tor_message = tor_message[2:]
    return tor_message


def decode_tor_message_for_intermediate_node(tor_message: str):
    tor_message = tor_message[2:]
    first_line_end_index = tor_message.find("\n")
    next_node = tor_message[:first_line_end_index]
    http_message = tor_message[first_line_end_index + 1:]
    return next_node, http_message
