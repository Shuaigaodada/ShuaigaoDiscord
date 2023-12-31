import os
from os.path import *
from cryptography.fernet import Fernet

dirpath = dirname(abspath(__file__))
# 因为改动了位置因此更改dirpath，如果dirpath在ShuaigaoDiscord内则注释下面一行
dirpath = join(dirname(dirpath), "ShuaigaoDiscord")
class src:
    @staticmethod
    def create(path: str):
        path = join(dirpath, "src", *path.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

key = Fernet.generate_key()
with open(src.create("keys/secret.key"), "wb") as keyfp:
    keyfp.write(key)

fernet = Fernet(key)

token = "NONE" # Enter token here
if token == "NONE":
    raise Exception("You didn't set token")

encrypted = fernet.encrypt(token.encode())

with open(src.create("tokens/bot.token"), "wb") as token_file:
    token_file.write(encrypted)

