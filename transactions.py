transactions = {}

def start_transaction(client_connection):
    transactions[client_connection] = []

def queue_command(client_connection, request):
    transactions[client_connection].append(request)

def get_queued_commands(client_connection):
    return transactions.get(client_connection)

def clear_transaction(client_connection):
    transactions.pop(client_connection, None)

def is_in_transaction(client_connection):
    return client_connection in transactions
