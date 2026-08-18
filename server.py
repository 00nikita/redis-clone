import socket
import json 

database = {}

with open("config.json") as f:
    config = json.load(f)

def execute_command(request):
    if request == ["PING"]:
        return b"+PONG\r\n"
    elif request[0] == "SET":
        key = request[1]
        value = request[2]
        database[key] = value
        return b"+OK\r\n"
    elif request[0] == "GET":
        key = request[1]
        if key in database:
            value = database[key]
            return f"${len(value)}\r\n{value}\r\n".encode()
        else:
            return b"$-1\r\n"
    elif request[0] == "DEL":
        key = request[1]
        if key in database:
            del database[key]
            return b":1\r\n"
        return b":0\r\n"
    elif request[0] == "EXISTS":
        key = request[1]
        if key in database:
            return b":1\r\n"
        return b":0\r\n"
    else:
        return b"-ERROR: Unknown command\r\n"
            
        

def handle_client(client_connection, client_address, buffer):
    while True:
        request = []
        while b"\r\n" not in buffer:
            buffer += client_connection.recv(1024)
        if buffer == b"":
            break
        tot_words, remaining_part = buffer.split(b"\r\n", 1)
        count = int(tot_words.decode().split("*",1)[1])
        flag = 0
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
            else:
                remaining_part += client_connection.recv(1024)
        buffer = remaining_part
        response = execute_command(request)
        client_connection.sendall(response)

#creating socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind socket
socket.bind((config['host'], config['port']))

#listen

socket.listen()

client_connection, client_address = socket.accept()

handle_client(client_connection, client_address, b"")
