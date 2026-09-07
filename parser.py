from commands import execute_command 

def handle_client(client_connection, buffer):
    request = []
    if buffer == b"":
        return b""
    tot_words, remaining_part = buffer.split(b"\r\n", 1)
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
        else:
            complete = False
            break
    if not complete:
        return buffer
    buffer = remaining_part
    response = execute_command(request, persist=True, client_connection=client_connection)
    client_connection.sendall(response)
    return buffer