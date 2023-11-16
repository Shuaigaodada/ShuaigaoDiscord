import os
import pathlib
from typing import Any

_root    = os.path.abspath(__file__)
_root    = os.path.dirname(_root)
_src     = os.path.join(_root, "src")
_server  = os.path.join(_src, "servers")

# class Server:
#     def __init__(self, id: str):
#         self.id = id
#         self.user: User = self._assign_user
    
#     def _assign_user(self, id: str):
#         self.user = User(id, self.id)

# class User:
#     def __init__(self, id: str, svid: str):
#         self.id = id
#         self.server_id = svid
#         self.path = os.path.join(_server, self.server_id, self.id)
    
#     def check(self, name: str) -> bool:
#         path = os.path.join(self.path, name)
#         return os.path.exists(path)

#     def create(self, name: str):
#         path = os.path.join(self.path, name)
#         os.makedirs(path, exist_ok=True)
#         return path
    
#     def lists(self, name: str):
#         return os.listdir(os.path.join(self.path, name))

#     def file(self, name: str):
#         return os.path.join(self.path, name)

#     @property
#     def playlist(self):
#         os.makedirs(self.path, exist_ok=True)
#         playlists = os.listdir(self.path)
#         return [file.split(".")[0] for file in playlists]

class _AssetsFile:
    def lists(self, suffix: bool = True):
        if self._auto:
            os.makedirs(self._path, exist_ok=True)
        return os.listdir(self._path) if suffix else [f.split(".")[0] for f in os.listdir(self._path)]
    
    def join(self, name):
        if self._auto:
            os.makedirs(self._path, exist_ok=True)
        return os.path.join(self._path, name)


class User(_AssetsFile):
    def __init__(self, id: str, _sid: str, _path: str, _auto: bool):
        self.id = id
        self._sid = _sid
        self._path = _path
        self._auto = _auto
    
    

class Server(_AssetsFile):
    def __init__(self, id: str, _path: str, _auto: bool):
        self.id = id
        self._path = _path
        self._auto = _auto

    def user(self, id: str):
        return User(id, self.id, os.path.join(self._path, id), self._auto)

    

class Assets:
    def __init__(self, path: str = _root, __auto: bool = True):
        self._cph = path
        self._auto = __auto
    
    def server(self, id: str):
        return Server(id, os.path.join(self._cph, "src", "servers", str(id)), self._auto)

    def __getattr__(self, attr: str):
        return Assets(os.path.join(self._cph, attr), self._auto)

    def path(self):
        return self._cph
    def file(self, name: str):
        return os.path.join(self._cph, name)


