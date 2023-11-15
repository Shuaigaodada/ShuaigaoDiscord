import os
import pathlib

root    = os.path.abspath(__file__)
root    = os.path.dirname(root)
src     = os.path.join(root, "src")
server  = os.path.join(src, "servers")

class Server:
    def __init__(self, id: str):
        self.id = id
        self.user: User = self._assign_user
    
    def _assign_user(self, id: str):
        self.user = User(id, self.id)

class User:
    def __init__(self, id: str, svid: str):
        self.id = id
        self.server_id = svid
        self.path = os.path.join(server, self.server_id, self.id)
    
    def check(self, name: str) -> bool:
        path = os.path.join(self.path, name)
        return os.path.exists(path)

    def create(self, name: str):
        path = os.path.join(self.path, name)
        os.makedirs(path, exist_ok=True)
        return path
    
    def lists(self, name: str):
        return os.listdir(os.path.join(self.path, name))

    @property
    def playlist(self):
        os.makedirs(self.path, exist_ok=True)
        playlists = os.listdir(self.path)
        return playlists


