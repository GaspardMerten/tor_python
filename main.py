import threading

from client import TorClient
from models.node import TorNode
from server_node import ServerNode

if __name__ == '__main__':
    server_nodes = [
        ServerNode(("localhost", 8080 + i))
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

    threads = [Thread(server_node) for server_node in server_nodes]

    input("Press Enter to continue...")

    tor_client = TorClient(list(map(lambda server_node: TorNode(
        server_node.server_address[0],
        server_node.server_address[1],
        server_node.crypto.get_public_key_bytes().decode("utf-8"),
    ), server_nodes)))

    def build_http_get_message_from_url():
        return f"GET / HTTP/1.1\nHost: httpforever.com:80\n\n"

    print(tor_client.send_http_message(
        build_http_get_message_from_url()
    ))
