import socket
import json 
import os
from commands import execute_command
from parser import handle_client
from database import database
from aof_parser import load_aof, rewrite_aof, should_rewrite_aof
import select
from pubsub import subscriptions


with open("config.json") as f:
    config = json.load(f)

#creating socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

socket.setblocking(False)

#bind socket
socket.bind((config['host'], config['port']))

#listen

socket.listen()

load_aof()

sockets = [socket]

buffers = {}

while True:
    readable, _, _ = select.select(sockets, [], [])
    for sock in readable:
        if sock is socket:
            client_connection, client_address = socket.accept()
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
                while buffers[sock]:
                    new_buffer = handle_client(sock, buffers[sock])
                    if new_buffer == buffers[sock]:
                        break
                    buffers[sock] = new_buffer
    if should_rewrite_aof():
        rewrite_aof()