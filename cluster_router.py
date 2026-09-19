import socket
from parser import parse_request
from cluster import get_node_for_key


HOST = "0.0.0.0"
PORT = 7000


server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server_socket.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Cluster router listening on {PORT}")

def forward_request(request, node):
    resp = f"*{len(request)}\r\n"

    for word in request:
        resp += f"${len(word)}\r\n{word}\r\n"

    with socket.create_connection(
        (node["host"], node["port"])
    ) as connection:

        connection.sendall(resp.encode())

        response = connection.recv(1024)

    return response


while True:
    client_connection, client_address = server_socket.accept()

    print(
        f"Client connected: {client_address}"
    )

    data = client_connection.recv(1024)

    request, remaining = parse_request(data)

    print("Parsed request:", request)

    if request[0] in ("GET", "SET", "DEL", "EXISTS"):

       key = request[1]

       node = get_node_for_key(key)

       response = forward_request(request, node)

       print("Node response:", response)

       client_connection.sendall(response)