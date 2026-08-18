import socket
import json 
from commands import execute_command
from parser import handle_client
from database import database

database = {}

with open("config.json") as f:
    config = json.load(f)

#creating socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind socket
socket.bind((config['host'], config['port']))

#listen

socket.listen()

while True:
    client_connection, client_address = socket.accept()
    handle_client(client_connection, client_address, b"")
