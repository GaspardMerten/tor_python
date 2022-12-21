import asyncio
import sys
from mitmproxy import options
from mitmproxy.net.http.http1 import assemble_request

from mitmproxy.tools import dump

from client import TorClient

client = TorClient(("localhost", 8001))
class RequestLogger:
    def request(self, flow):
        if "info.cern.ch" in flow.request.pretty_host:
            assemble = assemble_request(flow.request).decode("utf-8")
            resp = client.send_http_message(assemble)
            print(resp)
            print("REPLIED")
            flow.reply(resp)

async def start_proxy(host, port):
    opts = options.Options(listen_host=host, listen_port=port)

    master = dump.DumpMaster(
        opts,
        with_termlog=False,
        with_dumper=False,
    )
    master.addons.add(RequestLogger())

    await master.run()
    return master


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    asyncio.run(start_proxy(host, port))