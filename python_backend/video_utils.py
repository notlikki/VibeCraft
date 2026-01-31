import hashlib

def chained_hash(frame: bytes, prev_hash: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(frame)
    h.update(prev_hash)
    return h.digest()

def content_hash(data: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(data)
    return h.digest()