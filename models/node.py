from dataclasses import dataclass


@dataclass
class TorNode:
    ip: str
    port: int
    public_key: str

    def __hash__(self):
        return hash((self.ip, self.port))
