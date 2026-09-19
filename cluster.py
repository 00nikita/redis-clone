TOTAL_SLOTS = 16384

NODES = [
    {
        "host": "127.0.0.1",
        "port": 6379,
        "start_slot": 0,
        "end_slot": 5461
    },
    {
        "host": "127.0.0.1",
        "port": 6380,
        "start_slot": 5462,
        "end_slot": 10922
    },
    {
        "host": "127.0.0.1",
        "port": 6381,
        "start_slot": 10923,
        "end_slot": 16383
    }
]


def crc16(data):
    crc = 0

    for byte in data:
        crc ^= byte << 8

        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1

            crc &= 0xFFFF

    return crc


def get_slot(key):
    return crc16(key.encode()) % TOTAL_SLOTS


def get_node_for_slot(slot):
    for node in NODES:
        if node["start_slot"] <= slot <= node["end_slot"]:
            return node

    return None


def get_node_for_key(key):
    slot = get_slot(key)
    return get_node_for_slot(slot)