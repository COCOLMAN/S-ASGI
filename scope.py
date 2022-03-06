from typing import Optional, Iterable, TypedDict


class ASGIInfo(TypedDict):
    version: str
    spec_version: str


class Scope(TypedDict):
    type: str
    asgi: ASGIInfo
    http_version: str
    method: str
    scheme: str
    path: str
    raw_path: Optional[bytes]
    query_string: bytes
    root_path: str
    headers:  Iterable[tuple[bytes, bytes]]
    client: Optional[Iterable[tuple[str, int]]]
    server: Optional[Iterable[tuple[str, int]]]

