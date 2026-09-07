import socket
import json 
import os
from commands import execute_command
from parser import handle_client
from database import database
from aof_parser import load_aof, rewrite_aof, should_rewrite_aof
import select


with open("config.json") as f:
    config = json.load(f)

#creating socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            sockets.append(client_connection)
            buffers[client_connection] = b""
        else:
            data = sock.recv(1024)
            if data == b"":
                sockets.remove(sock)
                del buffers[sock]
                sock.close()
            else:
                buffers[sock] += data
                buffers[sock] = handle_client(sock, buffers[sock])
                print(buffers[sock])
    if should_rewrite_aof():
        rewrite_aof()