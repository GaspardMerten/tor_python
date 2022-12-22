import asyncio
import sys

from mitmproxy import http, options
from mitmproxy.net.http.http1 import assemble_request
from mitmproxy.tools import dump

from client import TorClient
from domain.http_message import extract_data_from_http_raw_response

client = None


class RequestLogger:
    def __init__(self, tor_client):
        self.tor_client = tor_client

    def request(self, flow):
        try:
            assemble = assemble_request(flow.request).decode("utf-8")

            resp = self.tor_client.send_http_message(assemble)
            raw_http = extract_data_from_http_raw_response(resp)
            headers = {}

            for header_line in raw_http.headers.splitlines():
                if ": " in header_line:
                    header_name, header_value = header_line.split(": ")
                    headers[header_name] = header_value

            flow.response = http.Response.make(
                raw_http.status_code,  # (optional) status code
                raw_http.body.encode("utf-8"),  # (optional) content
                headers,  # (optional) headers
            )
        except Exception as s:
            print("NOT WORKING")
            flow.response = http.Response.make(
                404,  # (optional) status code
            )
        else:
            print("RESPONDED")


async def start_proxy(host, port, tor_registry_address):
    tor_client = TorClient(tor_registry_address)

    opts = options.Options(listen_host=host, listen_port=port)

    master = dump.DumpMaster(
        opts,
        with_termlog=False,
        with_dumper=False,
    )
    master.addons.add(RequestLogger(tor_client))

    await master.run()
    return master


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    asyncio.run(start_proxy(host, port, (sys.argv[3], int(sys.argv[4]))))
