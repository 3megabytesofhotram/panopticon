import socket
from typing import Optional

class SingleInstanceException(Exception):
    pass

class SingleInstance:
    def __init__(self, port: int = 47588):
        self.lock_socket: Optional[socket.socket] = None
        self.port = port

    def __enter__(self):
        try:
            self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.lock_socket.bind(('localhost', self.port))
            return self
        except socket.error:
            raise SingleInstanceException("Another instance is already running")

    def __exit__(self):
        if self.lock_socket:
            self.lock_socket.close()