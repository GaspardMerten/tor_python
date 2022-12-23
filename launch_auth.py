import sys

from clients.auth_server import AuthServerNode

if __name__ == "__main__":
    auth_node = AuthServerNode((sys.argv[1], int(sys.argv[2])))
    auth_node.serve_forever()
