import socket
import time

PRIMARY_HOST = "127.0.0.1"
PRIMARY_PORT = 6379

replica_socket = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM
)

replica_socket.connect((PRIMARY_HOST, PRIMARY_PORT))

replica_socket.connect((PRIMARY_HOST, PRIMARY_PORT))

# Send simplified handshake
handshake = (
    "*2\r\n"
    "$7\r\n"
    "REPLICA\r\n"
    "$5\r\n"
    "HELLO\r\n"
)

replica_socket.sendall(handshake.encode())

response = replica_socket.recv(1024)
print("Primary:", response.decode())

while True:
    data = replica_socket.recv(4096)

    if not data:
        print("Primary disconnected")
        break

    print("Received from primary:", data)