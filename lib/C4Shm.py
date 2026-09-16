import os
import json

def getC4Shm(shm,shmsz):
    shm.seek(0)
    raw_data = shm.read(shmsz)
    clean_data=raw_data.split(b'\x00')[0]
    if not clean_data:
        return {}
    try:
        return json.loads(clean_data.decode('utf-8'))
    except json.JSONDecodeError:
        return {}

def setC4Shm(shm,shmsz, data_dict):
    json_bytes=json.dumps(data_dict).encode('utf-8')
    json_len=len(json_bytes)
    if json_len >= shmsz:
        raise MemoryError(f"Shared Memory Overflow! JSON needs {json_len} Bytes, max {shmsz} allowed.")
    
    shm.seek(0)
    shm.write(b'\x00' * shmsz)
    shm.seek(0)
    shm.write(json_bytes)
