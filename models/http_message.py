from dataclasses import dataclass

__all__ = ("RawHttpRequest", "RawHttpResponse")


@dataclass
class RawHttpRequest:
    host: str
    http_version: str
    path: str
    method: int
    headers: str
    body: str


@dataclass
class RawHttpResponse:
    status_code: int
    status: str
    url: str
    headers: str
    body: str
