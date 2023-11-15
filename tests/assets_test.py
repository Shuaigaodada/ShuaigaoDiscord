import sys
import asyncio
sys.path.append("./ShuaigaoDiscord")
import assets

server = assets.Server("123")
server.user("456")
playlists = server.user.playlist
print(playlists)

