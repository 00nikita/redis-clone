import socket
import json 

with open("config.json") as f:
    config = json.load(f)

def handle_client(client_connection, client_address):
    buffer = b""
    request = []
    while b"\r\n" not in buffer:
        buffer += client_connection.recv(1024)
    tot_words, remaining_part = buffer.split(b"\r\n", 1)
    count = 2*int(tot_words.decode().split("$",1)[1])
    flag = 0
    while count > 0:
        if b"\r\n" in remaining_part:
            if flag == 0:
                flag = 1 
                continue 
            request_line = remaining_part.split(b"\r\n", 1)[0].decode()
            request.append(request_line)
            remaining_part = remaining_part.split(b"\r\n", 1)[1]
            count -= 1
        else:
            remaining_part += client_connection.recv(1024)

    return request

#creating socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind socket
socket.bind((config['host'], config['port']))

#listen

socket.listen()

client_connection, client_address = socket.accept()

handle_client(client_connection, client_address)
