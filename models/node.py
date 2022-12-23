from dataclasses import dataclass

__all__ = ("TorNode",)

@dataclass
class TorNode:
    ip: str
    port: int
    public_key: str

    def __hash__(self):
        return hash((self.ip, self.port))
