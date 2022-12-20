from typing import Tuple

from models.node import TorNode


def encode_tor_message_for_final_node(message: str, public_key: bytes) -> str:
    return f"1\n{public_key}\n" + message


def encode_tor_message_for_intermediate_node(encrypted_message: str, next_node: TorNode) -> str:
    return f"0\n{next_node.ip}:{next_node.port}\n" + encrypted_message


def is_final_node(tor_message: str):
    return tor_message[0] == "1"


def decode_tor_message_for_final_node(tor_message: str) -> Tuple[str, str]:
    tor_message = tor_message[2:]
    first_line_end_index = tor_message.find("\n")
    sim_key = tor_message[1:first_line_end_index]
    http_message = tor_message[first_line_end_index + 1:]
    return sim_key, http_message


def decode_tor_message_for_intermediate_node(tor_message: str):
    tor_message = tor_message[2:]
    first_line_end_index = tor_message.find("\n")
    next_node = tor_message[:first_line_end_index]
    http_message = tor_message[first_line_end_index + 1:]
    return next_node, http_message
