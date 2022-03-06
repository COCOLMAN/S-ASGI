import asyncio
from urllib.parse import urlparse
from http import HTTPStatus
from scope import Scope


def get_content_length(scope):
    for [key, value] in scope["headers"]:
        if key == b"content-length":
            return int(value)

    return 0


def build_http_headers(scope, event):
    http_version = scope["http_version"]
    status = HTTPStatus(event["status"])
    status_line = f"HTTP/{http_version} {status.value} {status.phrase}\r\n"

    headers = [status_line.encode()]
    for header_line in event.get("headers", []):
        headers.append(b": ".join(header_line))
        headers.append(b"\r\n")
    headers.append(b"\r\n")

    return headers


class ScopeParser:
    async def scope_headers(self, reader):
        headers = []

        while True:
            header_line = await reader.readuntil(b"\r\n")
            header = header_line.rstrip()
            if not header:
                break
            key, value = header.split(b": ", 1)
            headers.append([key.lower(), value])

        return headers

    async def parse(self, reader) -> Scope:
        request_line = await reader.readuntil(b'\r\n')
        method, url, protocol_version = request_line.decode().strip().split()
        url = urlparse(url)
        protocol, version = protocol_version.split("/")
        headers = await self.scope_headers(reader)

        return Scope(
            type="http",
            asgi={
                "version": "2.3",
            },
            http_version=version,
            method= method,
            scheme= "http",
            path= url.path,
            query_string=url.query.encode(),
            headers=headers,
        )



class ASGIServer:
    scope: Scope

    def __init__(self, app, host, port):
        self.app = app
        self.host: str = host
        self.port: int = port
        self.scope_parser = ScopeParser()


    async def __call__(self):
        server = await asyncio.start_server(self.handler, self.host, self.port)
        async with server:
            await server.serve_forever()

    async def receive(self):
        content_length = get_content_length(self.scope)
        return {
            "type": "http.request",
            "body": await self.reader.read(content_length),
            "more_body": False,
        }

    async def send(self, event):
        if event["type"] == "http.response.start":
            self.response_headers = build_http_headers(self.scope, event)
        elif event["type"] == "http.response.body":
            if self.response_headers:
                self.writer.writelines(self.response_headers)
                self.response_headers = []

            self.writer.write(event["body"])
            await self.writer.drain()

            if event.get("more_body", False) is False:
                self.writer.close()
                await self.writer.wait_closed()


    async def handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader; self.writer = writer
        self.response_headers = []
        self.scope = await self.scope_parser.parse(self.reader)

        await self.app(self.scope, self.receive, self.send)


def run(app, host, port):
    server = ASGIServer(app, host, port)
    asyncio.run(server(), debug=True)


