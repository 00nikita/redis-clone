from commands import execute_command
import os
from database import database

def load_aof():
    try:
        with open("appendonly.aof", "r") as f:
            for line in f:
                line = line.strip().split()
                execute_command(line, persist=False)
    except FileNotFoundError:
        return
    
def rewrite_aof():
    with open("appendonly.aof.tmp", "w") as f:
        for key, value in database.items():
            f.write(f"SET {key} {value}\n")
    os.replace("appendonly.aof.tmp", "appendonly.aof")