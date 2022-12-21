import asyncio
import sys
from mitmproxy import options
from mitmproxy.net.http.http1 import assemble_request

from mitmproxy.tools import dump

from client import TorClient

client = None


class RequestLogger:
    def __init__(self, tor_client):
        self.tor_client = tor_client

    def request(self, flow):
        if "info.cern.ch" in flow.request.pretty_host:
            assemble = assemble_request(flow.request).decode("utf-8")
            resp = self.tor_client.send_http_message(assemble)
            print(resp)
            print("REPLIED")
            flow.reply(resp)


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
