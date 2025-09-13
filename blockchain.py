import hashlib
import datetime

class Block:
    def __init__(self, index, timestamp, data, prev_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.prev_hash = prev_hash
        self.hash = self.hash_block()
    
    def hash_block(self):
        sha = hashlib.sha256()
        sha.update(f"{self.index}{self.timestamp}{self.data}{self.prev_hash}".encode())
        return sha.hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
    
    def create_genesis_block(self):
        return Block(0, str(datetime.datetime.now()), "Genesis Block", "0")
    
    def add_block(self, data):
        prev_block = self.chain[-1]
        new_block = Block(len(self.chain), str(datetime.datetime.now()), data, prev_block.hash)
        self.chain.append(new_block)