from database import database, expiry
import time
import json 

with open("config.json") as f:
    config = json.load(f)

def execute_command(request, persist=False):
    if request == ["PING"]:
        return b"+PONG\r\n"
    elif request[0] == "SET":
        key = request[1]
        value = request[2]
        database[key] = value
        if persist:
          with open("appendonly.aof", "a") as f:
            f.write(" ".join(request) + "\n")
        return b"+OK\r\n"
    elif request[0] == "GET":
        key = request[1]
        if key in database:
            if key in expiry and time.time() > expiry[key]:
                del database[key]
                del expiry[key]
                return b"$-1\r\n"
            value = database[key]
            return f"${len(value)}\r\n{value}\r\n".encode()
        else:
            return b"$-1\r\n"
    elif request[0] == "DEL":
        key = request[1]
        if key in database:
            del database[key]
            if key in expiry:
                del expiry[key]
            if persist:
              with open("appendonly.aof", "a") as f:
                f.write(" ".join(request) + "\n")
            return b":1\r\n"
        return b":0\r\n"
    elif request[0] == "EXISTS":
        key = request[1]
        if key in database:
            if key in expiry and time.time() > expiry[key]:
                del database[key]
                del expiry[key]
                return b"$-1\r\n"
            return b":1\r\n"
        return b":0\r\n"
    elif request[0] == "EXPIRE":
        key = request[1]
        if key in database:
            if persist:
                expiry[key] = time.time() + int(request[2])
                request[2] = expiry[key]
                with open("appendonly.aof", "a") as f:
                    f.write(" ".join(request) + "\n")
            else:
                expiry[key] = float(request[2])
            return b":1\r\n"
        return b":0\r\n"
    elif request[0] == "TTL":
        key = request[1]
        if key in database:
            if key in expiry:
                ttl = int(expiry[key]-time.time())
                if ttl < 0:
                    del database[key]
                    del expiry[key]
                    return b":-2\r\n"
                return f":{ttl}\r\n".encode()
            return b":-1\r\n"
        return b":-2\r\n"
    else:
        return b"-ERROR: Unknown command\r\n"