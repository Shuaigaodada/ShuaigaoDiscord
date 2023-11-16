import sys
import asyncio
sys.path.append("./ShuaigaoDiscord")
import engine

class ctxTest:
    async def send(*args, **kwargs):
        print(args[0], end="\r", flush=True)
        class TMessage:
            async def edit(*args, **kwargs):
                print(args[0], end="\r", flush=True)
        return TMessage()

async def main():
    # files = await engine.Youtube.playlist.download(ctxTest(), "https://www.youtube.com/playlist?list=PLTZI-S6ZpPkFTzE-X2JOec-56IWGDSPoj", "081932", "3218952")
    # print(files)
    # print(len(files))
    await engine.Youtube.playlist.Import("https://www.youtube.com/playlist?list=PLTZI-S6ZpPkFTzE-X2JOec-56IWGDSPoj", 
                                         "/home/laogao/Project/ShuaigaoDiscord/ShuaigaoDiscord/src/servers/12345/laogao/JayChou.json")

asyncio.run(main())
