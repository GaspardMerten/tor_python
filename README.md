# TOR Over HTTP

TOR is a protocol that allows you to browse the internet anonymously.
This is done by routing your traffic through a random path of three nodes (entry - intermediate - exit node).

This implementation of the protocol is different because instead of
relying on TCP, it uses HTTP. This means that any request going
through TOR looks exactly like a normal HTTP request. This is
especially useful when you want to use TOR in a network that blocks
TCP connections.

This project is a proof of concept and is not meant to be used in production.
But it does offer a good starting point to build a new implementation of TOR.
An implementation that would be more focus on modern web technologies.

## How it works

There are three important components in this project:
- The client
- The node server
- The registry server

The flow is the following.

A registry server is created by a trusted entity. This server is
responsible for keeping track of all the nodes that are currently
available.

Then, whenever a node is created, it registers itself to the registry.
The registry server will then keep track of the node and will send
it to the client when it is requested.

After the TOR network is setted up, the client will send a request
to the registry server. The registry server will then respond with a
list of nodes that are currently available. The client will then
create a path of three nodes and will send the request to the first
node in the path. The first node will then send the request to the
second node and so on. The last node in the path will then send the
response back to the client.

Of course, the message sent by the client is encrypted using a combination of each node's public key and symmetric key
to encrypt long messages. So the only way to decrypt the message is to have the private key of each node in the path.

To get a better understanding of how the protocol works, you can
check the documentation in the source code.

## How to use

You can start a registry node with

```bash
python registry_node.py ip port
```

You can start a tor node with

```bash
python server_node.py ip port registry_ip registry_port
```

You can start an auth server with

```bash
python auth_server.py ip port
```

You can start the proxy with

```bash
  python proxy.py ip port registry_ip registry_port
```

If you get an issue with firefox not trusting the proxy.
See: https://stackoverflow.com/questions/62261786/how-to-allow-firefox-to-connect-to-webpage-through-mitmproxy

## How to run the demo

If you just want to verify that the project works, you can run the
demo.py file.

You can run the demo just by launching the demo.py file.
Then just follow the instructions.

## LIMITATIONS

HTTP2 is not supported. This is because the protocol is not supported by
the requests library. HTTPX is a good alternative and should probably be used
in the future.

