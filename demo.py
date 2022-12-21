"""
    A demo script for the tor network.

    It creates ten nodes and connects them to the network using one registry node.

    Then creates a client that connects to the network using the registry node to retrieve
    the list of nodes.

    Then the client builds a path of nodes and sends different messages to the auth server demonstrating
    the capabilities of this home-made tor network.
"""
import json
import threading
import time

from auth_server import AuthServerNode
from client import TorClient
from domain.http_message import extract_data_from_http_raw_response
from registry_node import RegistryNode
from server_node import ServerNode


def build_http_post_message_from_url(host, path, data, headers=None):
    if data:
        content_length = len(data)
    else:
        content_length = 0

    if not headers:
        headers = {}

    headers["Content-Length"] = content_length

    post_request_raw_message = f"""POST {path} HTTP/1.1\nHost: {host}\n"""

    for key, value in headers.items():
        post_request_raw_message += f"{key}: {value}\n"

    if data:
        post_request_raw_message += f"\n\n{data}"

    return post_request_raw_message


def build_http_get_message_from_url(domain: str, path: str, headers: dict[str, str] = None):
    request_raw_message = f"""GET {path} HTTP/1.1
Host: {domain}
"""
    if headers:
        for key, value in headers.items():
            request_raw_message += f"{key}: {value}"

    return request_raw_message


if __name__ == '__main__':
    registry_port = 8424
    auth_server_port = 7075

    server_nodes = [
        ServerNode(("localhost", 8080 + i), registry_address=("localhost", registry_port))
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


    registry = RegistryNode(("localhost", registry_port))
    auth_server = AuthServerNode(("localhost", auth_server_port))

    threads = [Thread(registry), Thread(auth_server)]
    time.sleep(2)
    threads += [Thread(server_node) for server_node in server_nodes]

    time.sleep(9)
    input("\nPress Enter to start demonstration...")

    print("Launching tor client...")
    tor_client = TorClient(registry.server_address)

    auth_server_host = ":".join(map(str, auth_server.server_address))

    print("Using auth server: " + auth_server_host)

    print("Sending unauthenticated request to server...")
    response = tor_client.send_http_message(build_http_get_message_from_url(auth_server_host, "/private"))
    raw_response = extract_data_from_http_raw_response(response)
    print("Server responds with status", raw_response.status_code, raw_response.status)

    print("Sending post request to auth server...")
    response = tor_client.send_http_message(build_http_post_message_from_url(auth_server_host, "/auth", json.dumps(
        {"username": "gaspard", "password": "mypassword"})))
    raw_response = extract_data_from_http_raw_response(response)
    json_response = json.loads(raw_response.body)
    print("Received token: ", json_response["token"])
    print("Now making authenticated request to server")
    response = tor_client.send_http_message(
        build_http_get_message_from_url(auth_server_host, "/private", headers={"Token": json_response["token"]}))
    raw_response = extract_data_from_http_raw_response(response)
    json_response = json.loads(raw_response.body)
    print("Server responds with status", raw_response.status_code, raw_response.status)
    print("Server responds secret message : ", json_response["data"])
    print("Are you ready to see the magic ?")
    input("Press Enter to continue...")
    time.sleep(1)
    print("Now demonstrating HTTPS request over our home-made tor network which is built over http.")
    time.sleep(1)
    print("Sounds crazy ?")
    time.sleep(1)
    print("Let's see...")

    time.sleep(1)

    response = tor_client.send_http_message(
        build_http_get_message_from_url("www.google.be:443", "/"))
    raw_response = extract_data_from_http_raw_response(response)

    print("Server responds with status", raw_response.status_code, raw_response.status)
    print("Server responds:", raw_response.body)

    print("\n\n")
    print("Try it yourself !")

    x = 0

    while x < 5:
        x += 1
        url = input("Enter url to request (R to refresh path):")

        if url == "R":
            tor_client.refresh()
            continue

        if not url:
            if input("Do you really want to stop ? [Y/n]") == "Y":
                break
            else:
                print("Ok, let's continue ! It so fun !")

        if "://" in url[10:]:
            print(
                "Do not include protocol in url ! For instance use www.google.be:443 instead of https://www.google.be")
            continue

        try:
            response = tor_client.send_http_message(
                build_http_get_message_from_url(url.split("/")[0],
                                                "/" + ("" if "/" not in url else url.split("/", 1)[1])))
            if response:
                print(response)
                raw_response = extract_data_from_http_raw_response(response)
                print("Server responds with status", raw_response.status_code, raw_response.status)
                print("Server responds:", raw_response.body)
            else:
                print("The server is not happy with your request")
        except Exception as _:
            print("Something went wrong !")
    print("Enough for today !")
    print(
        f"You can now try to launch proxy.py using 127.0.0.1 9000 127.0.0.1 {registry_port} (proxy address, proxy port, registry address, registry port)")
    print("Once that done, change your browser settings to use the proxy and try to access a website")
    input(
        "Waiting for you to press enter to stop the demonstration... It will stop all nodes making the proxy useless")
