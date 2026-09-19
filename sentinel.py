import socket 
import time 

PRIMARY_HOST = "127.0.0.1"
PRIMARY_PORT = 6379

REPLICAS = [
    ("127.0.0.1", 6380)
]

CHECK_INTERVAL = 2
FAILURE_THRESHOLD = 3

failure_count = 0
primary_state = "UP"

def promote_replica(host, port):
    try:
        with socket.create_connection(
            (host, port),
            timeout=1
        ) as connection:

            connection.sendall(
                b"PROMOTE\r\n"
            )

        print(
            f"[Sentinel] Promoted replica {host}:{port}"
        )

        return True

    except (socket.timeout, ConnectionRefusedError) as error:
        print(
            f"[Sentinel] Failed to promote {host}:{port}: {error}"
        )

        return False

def check_connection(host, port):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False 

print(f"[Sentinel] Monitoring Primary at {PRIMARY_HOST}:{PRIMARY_PORT}")

while True:
    time.sleep(CHECK_INTERVAL)
    state = check_connection(PRIMARY_HOST, PRIMARY_PORT)
    if state:
        failure_count = 0
    else:
        failure_count += 1
        if primary_state == "DOWN":
            continue
        if failure_count >= FAILURE_THRESHOLD:
            primary_state = "DOWN"
            print("PRIMARY IS DOWN")
            for replica in REPLICAS:
                host, port = replica

                if check_connection(host, port):
                    print(
                        f"[Sentinel] Replica {host}:{port} is available"
                    )

                    if promote_replica(host, port):
                        print(
                            f"[Sentinel] Failover complete: "
                            f"{host}:{port} is now primary"
                        )

                        break
