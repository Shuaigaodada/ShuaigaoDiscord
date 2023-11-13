import os
from os.path import *
from cryptography.fernet import Fernet

dirpath = dirname(abspath(__file__))
class src:
    @staticmethod
    def create(path: str):
        path = join(dirpath, "src", *path.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
    

def decrypt_token():
    with open(src.create("keys/secret.key"), "rb") as key_file:
        key = key_file.read()

    fernet = Fernet(key)

    with open(src.create("tokens/bot.token"), "rb") as token_file:
        encrypted = token_file.read()
    return fernet.decrypt(encrypted).decode()

