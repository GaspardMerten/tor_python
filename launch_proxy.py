import asyncio
import sys

from clients.proxy import start_proxy

if __name__ == "__main__":
    host = sys.argv[1]
    port = int(sys.argv[2])
    asyncio.run(start_proxy(host, port, (sys.argv[3], int(sys.argv[4]))))
