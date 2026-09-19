import socket
import pickle
import struct
import select
from pubsub import subscriptions
from parser import handle_client
from aof_parser import rewrite_aof, should_rewrite_aof
from commands import execute_command
import database


PRIMARY_HOST = "127.0.0.1"
PRIMARY_PORT = 6379

ROLE = "replica"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(('0.0.0.0', 6380))

server_socket.listen()
server_socket.setblocking(False)

psync_request = (
    "*3\r\n"
    "$5\r\n"
    "PSYNC\r\n"
    "$1\r\n"
    "?\r\n"
    "$2\r\n"
    "-1\r\n"
)



# --------------------------------------------------
# TCP HELPERS
# --------------------------------------------------
primary_connection = None

if ROLE == "replica":
    primary_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    primary_socket.connect(
        (PRIMARY_HOST, PRIMARY_PORT)
    )
    primary_connection = primary_socket

sockets = [server_socket]

if primary_connection:
    sockets.append(primary_connection)
    primary_connection.sendall(
        psync_request.encode()
    )

def read_line(sock):
    """
    Read bytes until CRLF is received.
    Returns the line without \\r\\n.
    """

    data = b""

    while not data.endswith(b"\r\n"):
        chunk = sock.recv(1)

        if not chunk:
            raise ConnectionError(
                "Connection closed while reading line"
            )

        data += chunk

    return data[:-2].decode()


def read_exactly(sock, number_of_bytes):
    """
    Read exactly number_of_bytes from the socket.
    TCP recv() may return fewer bytes, so we keep reading.
    """

    data = b""

    while len(data) < number_of_bytes:
        chunk = sock.recv(
            number_of_bytes - len(data)
        )

        if not chunk:
            raise ConnectionError(
                "Connection closed during data transfer"
            )

        data += chunk

    return data


# --------------------------------------------------
# RESP PARSER
# --------------------------------------------------

def read_resp_command(sock):
    """
    Read one RESP array command from the socket.

    Example wire format:

    *2\\r\\n
    $3\\r\\n
    SET\\r\\n
    $3\\r\\n
    key\\r\\n

    Returns:

    ["SET", "key"]
    """

    # Read array header, e.g. *2
    array_header = read_line(sock)

    if not array_header.startswith("*"):
        raise ValueError(
            f"Expected RESP array, received: {array_header}"
        )

    argument_count = int(array_header[1:])

    request = []

    for _ in range(argument_count):
        # Read bulk string header, e.g. $3
        bulk_header = read_line(sock)

        if not bulk_header.startswith("$"):
            raise ValueError(
                f"Expected RESP bulk string, received: {bulk_header}"
            )

        bulk_length = int(bulk_header[1:])

        # Read exactly the bulk string bytes
        value_bytes = read_exactly(
            sock,
            bulk_length
        )

        # Read the trailing CRLF
        read_exactly(sock, 2)

        request.append(
            value_bytes.decode()
        )

    return request


# --------------------------------------------------
# CONNECT TO PRIMARY
# --------------------------------------------------


# --------------------------------------------------
# PSYNC HANDSHAKE
# --------------------------------------------------

# PSYNC ? -1 means:
#
# ?  -> I do not know the replication ID
# -1 -> I have no previous replication offset
#
# RESP representation:
#
# *3
# $5
# PSYNC
# $1
# ?
# $2
# -1

buffers = {}


while True:
    readable, _, _ = select.select(sockets, [], [])
    for sock in readable:
        if ROLE == "replica" and sock is primary_connection:
            response_text = read_line(primary_connection)
            print("Primary:", response_text)

            if response_text.startswith("+FULLRESYNC"):
                parts = response_text.split()

                if len(parts) != 3:
                    raise ValueError(
                        f"Invalid FULLRESYNC response: {response_text}"
                    )

                primary_replication_id = parts[1]
                primary_offset = int(parts[2])

                print(
                    "Replication ID:",
                    primary_replication_id
                )

                print(
                    "Primary offset:",
                    primary_offset
                )

                # Read the 4-byte snapshot length
                snapshot_length_bytes = read_exactly(
                    primary_connection,
                    4
                )

                snapshot_length = struct.unpack(
                    "!I",
                    snapshot_length_bytes
                )[0]

                print(
                    "Snapshot size:",
                    snapshot_length,
                    "bytes"
                )

                # Read the complete snapshot
                snapshot_bytes = read_exactly(
                    primary_connection,
                    snapshot_length
                )

                # Deserialize snapshot
                received_database = pickle.loads(
                    snapshot_bytes
                )

                # Replace local database contents
                database.database.clear()
                database.database.update(
                    received_database
                )

                print("Initial database received:")
                print(database.database)

                # Store replication state locally for now.
                # Later, we will persist these values to disk.
                replica_replication_id = primary_replication_id
                replica_replication_offset = primary_offset

                print(
                    "Replica is synchronized at offset:",
                    replica_replication_offset
                )


            elif response_text.startswith("+CONTINUE"):
                print(
                    "Partial synchronization accepted"
                )

            else:
                raise ConnectionError(
                    f"Unexpected primary response: {response_text}"
                )


            print("Waiting for replication commands...")

            request = read_resp_command(
                primary_connection
            )

            print(
                "Replication command:",
                request
            )

            execute_command(
                request,
                persist=False,
                client_connection=primary_connection,
                executing=False,
                from_replica=True
            )
        else:
            if sock is server_socket:
                client_connection, client_address = server_socket.accept()
                client_connection.setblocking(False)
                sockets.append(client_connection)
                buffers[client_connection] = b""
            else:
                data = sock.recv(1024)
                if data == b"":
                    sockets.remove(sock)
                    del buffers[sock]
                    for channel in subscriptions:
                        subscriptions[channel].discard(sock)
                    sock.close()
                else:
                    buffers[sock] += data
                    if buffers[sock].startswith(b"PROMOTE\r\n"):
                        ROLE = "primary"

                        if primary_connection:
                            sockets.remove(primary_connection)
                            primary_connection.close()
                            primary_connection = None

                        buffers[sock] = buffers[sock][len(b"PROMOTE\r\n"):]

                        print("[Replica] PROMOTED TO PRIMARY")

                        continue
                    while buffers[sock]:
                        new_buffer = handle_client(sock, buffers[sock])
                        if new_buffer == buffers[sock]:
                            break
                        buffers[sock] = new_buffer
                if should_rewrite_aof():
                    rewrite_aof()