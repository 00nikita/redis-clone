from commands import execute_command

def load_aof():
    try:
        with open("appendonly.aof", "r") as f:
            for line in f:
                line = line.strip().split()
                execute_command(line, persist=False)
    except FileNotFoundError:
        return