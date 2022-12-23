import sys

from clients.registry_node import RegistryNode

if __name__ == "__main__":
    registry_node = RegistryNode((sys.argv[1], int(sys.argv[2])))
    registry_node.serve_forever()
