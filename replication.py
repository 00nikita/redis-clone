import pickle
import struct

from database import database

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