import socket 
import time 

PRIMARY_HOST = "127.0.0.1"
PRIMARY_PORT = 6379

CHECK_INTERVAL = 2
FAILURE_THRESHOLD = 3

failure_count = 0
primary_state = "UP"

def check_primary():
    try:
        with socket.create_connection((PRIMARY_HOST, PRIMARY_PORT), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False 

print(f"[Sentinel] Monitoring Primary at {PRIMARY_HOST}:{PRIMARY_PORT}")

while True:
    time.sleep(CHECK_INTERVAL)
    state = check_primary()
    if state:
        failure_count = 0
        if primary_state == "DOWN":
            primary_state = "UP"
            print("PRIMARY RECOVERED - PRIMARY IS UP")
    else:
        failure_count += 1
        if primary_state == "DOWN":
            continue
        if failure_count >= FAILURE_THRESHOLD:
            primary_state = "DOWN"
            print("PRIMARY IS DOWN")

