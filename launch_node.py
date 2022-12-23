import sys

from clients.server_node import ServerNode

if __name__ == "__main__":
    server_node = ServerNode(
        (sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4]))
    )
    server_node.serve_forever()
