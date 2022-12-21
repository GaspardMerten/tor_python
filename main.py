import threading
import time

from client import TorClient
from models.node import TorNode
from registry_node import RegistryNode
from server_node import ServerNode

if __name__ == '__main__':
    server_nodes = [
        ServerNode(("localhost", 8080 + i), registry_address=("localhost", 8001))
        for i in range(10)
    ]


    class Thread(threading.Thread):
        def __init__(self, server_node):
            threading.Thread.__init__(self)
            self.server_node = server_node
            self.daemon = True
            self.start()

        def run(self):
            self.server_node.serve_forever()


    registry = RegistryNode(("localhost", 8001))
    threads = [Thread(server_node) for server_node in server_nodes] + [Thread(registry)]

    input("Press Enter to continue...")

    tor_client = TorClient(registry.server_address)


    def build_http_get_message_from_url():
        return f"""GET / HTTP/2.0
Host: cdn.storage.giveactions.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate
Referer: https://www.google.com/
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Pragma: no-cache
Cache-Control: no-cache"""


    input()