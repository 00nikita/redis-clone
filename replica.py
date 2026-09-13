import socket
import time
from commands import execute_command
import database
import pickle
import struct

PRIMARY_HOST = "127.0.0.1"
PRIMARY_PORT = 6379

replica_socket = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM
)

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

# Read exactly 4 bytes containing the snapshot length.
snapshot_length_bytes = b""

while len(snapshot_length_bytes) < 4:
    chunk = replica_socket.recv(4 - len(snapshot_length_bytes))

    if not chunk:
        raise ConnectionError("Primary disconnected during snapshot header")

    snapshot_length_bytes += chunk

snapshot_length = struct.unpack("!I", snapshot_length_bytes)[0]

print("Snapshot size:", snapshot_length, "bytes")

snapshot_bytes = b""

while len(snapshot_bytes) < snapshot_length:
    chunk = replica_socket.recv(
        min(4096, snapshot_length - len(snapshot_bytes))
    )

    if not chunk:
        raise ConnectionError("Primary disconnected during snapshot transfer")

    snapshot_bytes += chunk


received_database = pickle.loads(snapshot_bytes)

database.clear()
database

print("Initial database received:")
print(database)

while True:
    data = replica_socket.recv(4096)
    if not data:
        print("Primary disconnected")
        break
    request = []
    tot_words, remaining_part = data.split(b"\r\n", 1)
    count = int(tot_words.decode().split("*",1)[1])
    flag = 0
    complete = True
    while count > 0:
        if b"\r\n" in remaining_part:
            if flag == 0:
                flag = 1
                remaining_part = remaining_part.split(b"\r\n", 1)[1]
                continue
            request_line = remaining_part.split(b"\r\n", 1)[0].decode()
            request.append(request_line)
            remaining_part = remaining_part.split(b"\r\n", 1)[1]
            flag = 0
            count -= 1
    execute_command(request, persist=False, client_connection=replica_socket, executing=False, from_replica=True)

