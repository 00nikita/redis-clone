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