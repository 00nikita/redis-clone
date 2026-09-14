import pickle
import struct
import uuid
from database import database
from collections import deque

replicas = set()

replication_id = uuid.uuid4().hex
replication_offset = 0

BACKLOG_SIZE = 1024*1024 

replication_backlog = deque()
backlog_size = 0
backlog_start_offset = 1

def get_backlog_data(requested_offset):
    if not replication_backlog:
        return None

    # The requested offset must still exist in the backlog
    if requested_offset < backlog_start_offset - 1:
        return None

    result = bytearray()

    for command_start_offset, command_bytes in replication_backlog:
        command_end_offset = (
            command_start_offset + len(command_bytes) - 1
        )

        # Include commands that contain bytes after requested_offset
        if command_end_offset > requested_offset:
            result.extend(command_bytes)

    return bytes(result)

def add_to_backlog(command_bytes, command_start_offset):
    global backlog_size
    global backlog_start_offset

    replication_backlog.append((command_start_offset, command_bytes))
    backlog_size += len(command_bytes)

    if len(replication_backlog) == 1:
        backlog_start_offset = command_start_offset

    while backlog_size > BACKLOG_SIZE:
        old_offset, old_command = replication_backlog.popleft()
        backlog_size -= len(old_command)

        if replication_backlog:
            backlog_start_offset = replication_backlog[0][0]
        else:
            backlog_start_offset = command_start_offset + len(command_bytes)

def get_replication_id():
    return replication_id

def get_replication_offset():
    return replication_offset

def increase_replication_offset(amount):
    global replication_offset
    replication_offset += amount

def replicate_command(request):
    resp = f"*{len(request)}\r\n"

    for word in request:
        resp += f"${len(word)}\r\n{word}\r\n"

    command_bytes = resp.encode()

        # Offset before adding this command
    command_start_offset = replication_offset + 1

    # Store command in backlog
    add_to_backlog(command_bytes, command_start_offset)

    increase_replication_offset(len(command_bytes))

    for replica in list(replicas):
        try:
            replica.sendall(command_bytes)
        except (BrokenPipeError, ConnectionResetError):
            replicas.remove(replica)
            replica.close()

def get_backlog_info():
    return {
        "backlog_size": backlog_size,
        "backlog_start_offset": backlog_start_offset,
        "replication_offset": replication_offset,
        "commands_stored": len(replication_backlog),
    }

def create_snapshot():
    """
    Create a snapshot of the current database state
    """
    return pickle.dumps(database)

def send_snapshot(client_connection):
    """
    Send:
        4-byte snapshot length
        followed by the snapshot bytes
    """

    snapshot = create_snapshot()
    # Send the 4-byte length followed by the snapshot bytes
    client_connection.sendall(struct.pack("!I", len(snapshot)))
    client_connection.sendall(snapshot)