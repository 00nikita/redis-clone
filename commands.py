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
    elif request[0] == "LPUSH":
        key = request[1]
        value = request[2]
        if key not in database:
            database[key] = []
        database[key].insert(0, value)
        if persist:
            with open("appendonly.aof", "a") as f:
                f.write(" ".join(request) + "\n")
        return b":1\r\n"
    elif request[0] == "RPUSH":
        key = request[1]
        value = request[2]
        if key not in database:
            database[key] = []
        database[key].append(value)
        if persist:
            with open("appendonly.aof", "a") as f:
                f.write(" ".join(request) + "\n")
        return b":1\r\n"
    elif request[0] == "LRANGE":
        key = request[1]
        start = int(request[2])
        end = int(request[3])
        if key in database:
            if isinstance(database[key], list):
                if end == -1:
                    values = database[key][start:]
                else:
                    values = database[key][start:end+1]
                response = f"*{len(values)}\r\n"
                for value in values:
                    response += f"${len(value)}\r\n{value}\r\n"
                return response.encode()
            else:
                return b"-ERROR: Key is not a list\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "LLEN":
        key = request[1]
        if key in database:
            if isinstance(database[key], list):
                return f":{len(database[key])}\r\n".encode()
            else:
                return b"-ERROR: Key is not a list\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "LINDEX":
        key = request[1]
        if key in database:
            if isinstance(database[key], list):
                value = database[key][int(request[2])]
                return f"${len(value)}\r\n{value}\r\n".encode()
            else:
                return b"-ERROR: Key is not a list\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "LSET":
        key = request[1]
        index = int(request[2])
        value = request[3]
        if key in database:
            if isinstance(database[key], list):
                if 0 <= index < len(database[key]):
                    database[key][index] = value
                    if persist:
                        with open("appendonly.aof", "a") as f:
                            f.write(" ".join(request) + "\n")
                    return b"+OK\r\n"
                else:
                    return b"-ERROR: Index out of range\r\n"
            else:
                return b"-ERROR: Key is not a list\r\n"
        else:
            return b"*0\r\n"

    
    elif request[0] == "LPOP":
        key = request[1]
        if key in database:
            if isinstance(database[key], list):
                if database[key]:
                    value = database[key].pop(0)
                    if persist:
                        with open("appendonly.aof", "a") as f:
                            f.write("LPOP {} {}\n".format(key, value))
                    return f"${len(value)}\r\n{value}\r\n".encode()
                return b"$-1\r\n"
            else:
                return b"-ERROR: Key is not a list\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "RPOP":
        key = request[1]
        if key in database:
            if isinstance(database[key], list):
                if database[key]:
                    value = database[key].pop()
                    if persist:
                        with open("appendonly.aof", "a") as f:
                            f.write("RPOP {} {}\n".format(key, value))
                    return f"${len(value)}\r\n{value}\r\n".encode()
                return b"$-1\r\n"
            else:
                return b"-ERROR: Key is not a list\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "HSET":
        key = request[1]
        field = request[2]
        value = request[3]
        if key not in database:
            database[key] = {}
        database[key][field] = value
        if persist:
            with open("appendonly.aof", "a") as f:
                f.write("HSET {} {} {}\n".format(key, field, value))
        return b"+OK\r\n"
    elif request[0] == "HGET":
        key = request[1]
        field = request[2]
        if key in database:
            if field in database[key]:
                value = database[key][field]
                return f"${len(value)}\r\n{value}\r\n".encode()
            else:
                return b"$-1\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "HGETALL":
        key = request[1]
        if key in database:
            response = f"*{len(database[key])*2}\r\n"
            for field, value in database[key].items():
                response += f"${len(field)}\r\n{field}\r\n"
                response += f"${len(value)}\r\n{value}\r\n"
            return response.encode()
        else:
            return b"*0\r\n"
    elif request[0] == "HDEL":
        key = request[1]
        field = request[2]
        if key in database:
            if field in database[key]:
                del database[key][field]
                if persist:
                    with open("appendonly.aof", "a") as f:
                        f.write("HDEL {} {}\n".format(key, field))
                return b":1\r\n"
            else:
                return b":0\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "HEXISTS":
        key = request[1]
        field = request[2]
        if key in database:
            if field in database[key]:
                return b":1\r\n"
            else:
                return b":0\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "HLEN":
        key = request[1]
        if key in database:
            return f":{len(database[key])}\r\n".encode()
        else:
            return b"*0\r\n"
    elif request[0] == "SADD":
        key = request[1]
        members = request[2:]
        if key not in database:
            database[key] = set()
        database[key].update(members)
        if persist:
            with open("appendonly.aof", "a") as f:
                f.write(" ".join(request) + "\n")
            return b":1\r\n"
        return b":0\r\n"
    elif request[0] == "SMEMBERS":
        key = request[1]
        if key in database:
            members = database[key]
            response = f"*{len(members)}\r\n"
            for member in members:
                response += f"${len(member)}\r\n{member}\r\n"
            return response.encode()
        else:
            return b"*0\r\n"
    elif request[0] == "SREM":
        key = request[1]
        members = request[2:]
        if key in database:
            removed = 0
            for member in members:
                if member in database[key]:
                    database[key].remove(member)
                    removed += 1
            if persist:
                with open("appendonly.aof", "a") as f:
                    f.write(" ".join(request) + "\n")
            return f":{removed}\r\n".encode()
        return b":0\r\n"
    elif request[0] == "SISMEMBER":
        key = request[1]
        member = request[2]
        if key in database:
            if member in database[key]:
                return b":1\r\n"
            else:
                return b":0\r\n"
        else:
            return b"*0\r\n"
    elif request[0] == "SCARD":
        key = request[1]
        if key in database:
            return f":{len(database[key])}\r\n".encode()
        else:
            return b"*0\r\n"
    elif request[0] == "SPOP":
        key = request[1]
        if key in database:
            if database[key]:
                member = database[key].pop()
                if persist:
                    with open("appendonly.aof", "a") as f:
                        f.write(f"SREM {key} {member}\n")
                return f"${len(member)}\r\n{member}\r\n".encode()
            else:
                return b"$-1\r\n"
        else:
            return b"*0\r\n"
    else:
        return b"-ERROR: Unknown command\r\n"