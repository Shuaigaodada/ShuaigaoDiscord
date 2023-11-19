# coding: utf-8
import os
import re
import json
import time
import engine
import assets
import command
import subprocess
import interactions
import interactions.ext
from event import *
from loguru import logger
from typing import Dict, List
from decrypt import decrypt_token
from interactions import OptionType, slash_option
from interactions.api.events import MessageCreate
from interactions.api.voice.audio import AudioVolume
from interactions import Message, SlashContext, StringSelectMenu

logger.info("initializing server...")
TOKEN: str = decrypt_token()
bot = interactions.Client(token=TOKEN)
logined_user: Dict[str, Dict[Dict, List[str]]] = {}



def load_config(name):
    def decorator(function):
        path = os.path.abspath(__file__)
        path = os.path.dirname(path)
        path = os.path.join(path, "src", "configs", name + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not os.path.exists(path):
            logger.error(f"Config file not found: {path}")
            return function
        
        with open(path, "r") as fp:
            data = fp.read()

        if not data:
            logger.error("can't load data, data is null")
            return function
        
        configs = json.loads(data)
        func = function
        for config in configs["args"][::-1]:
            config["opt_type"] = getattr(OptionType, config["opt_type"])
            func = slash_option(**config)(func)
            
        if func is None:
            logger.error("can't load data, data is null")
            return function
        return func
    return decorator

@interactions.listen()
async def on_startup():
    logger.info("bot is ready!")
    logger.info(f"bot owner: {bot.owner}")
    logger.info("press `Ctrl + C` to stop bot.")
@interactions.listen("on_message_create")
async def on_message(event: MessageCreate):
    message: Message = event.message
    logger.info(f"message received: {message.content} from {message.author.username}")
    
from interactions.api.voice.audio import AudioVolume

@interactions.slash_command(name="play", description="搜索并播放选择的音乐")
@load_config("play")
async def play(ctx: SlashContext, query: str, max_resluts: int = 5, quality: str = "Best"):
    logger.info(f"start searching {query}, command auother: {ctx.author.username}")
    message = await ctx.send("正在搜索中......")
    results: List[engine.VideoData] = await engine.Youtube.search(query, max_resluts)
    logger.info(f"results: {results}")
    names: List[str] = [f"{res.title[:50]} - {res.uploader[:20] if res.uploader else 'Unknown Uploader'}" for res in results]
    select_menu = StringSelectMenu(
        *names,
        placeholder="选择想要播放的音乐",
        min_values=1,
        max_values=1,
        custom_id=command.select_music
    )
    if str(ctx.author.id) not in temp:
        temp[str(ctx.author.id)] = {}
    temp[str(ctx.author.id)]["play_result"] = {name: video_data for name, video_data in zip(names, results)}
    temp[str(ctx.author.id)]["play_message"] = message
    temp[str(ctx.author.id)]["play_quality"] = quality
    
    await message.edit(content="请选择想要播放的音乐:", components=select_menu)

@interactions.slash_command(name="ping", description="测试与服务器的连接")
async def ping(ctx: SlashContext):
    before: float = time.perf_counter()
    message: Message = await ctx.send(content="正在计算延迟中...")
    after: float = time.perf_counter()
    await message.edit(content=f"你与服务器的延迟为 `{round((after - before) * 1000, 2)}ms`")
    return
    

@interactions.slash_command(name="playlist", description="列出用户的所有播放列表")
async def playlist(ctx: SlashContext):
    server_id: str = str(ctx.guild_id)
    user_id: str = str(ctx.author.id)

    asset = assets.Assets()
    

    playlists = asset.server(server_id).user(user_id).lists(False)
    if not playlists:
        logger.info(f"didn't find any playlist from user '{ctx.author.username}'")
        

    options = [interactions.StringSelectOption(label=playlist, value=playlist) for playlist in playlists]
    add_playlist_option = interactions.StringSelectOption(label="+ 添加/导入播放列表", value=command.add_playlist)
    options.append(add_playlist_option)

    # 创建选择菜单
    select_menu = StringSelectMenu(
        *options,
        placeholder="选择一个播放列表",
        min_values=1,
        max_values=1,
        custom_id=command.select_list
    )

    # 发送消息并附加选择菜单
    await ctx.send("请选择一个播放列表:", components=select_menu)



logger.info("starting bot server...")
bot.start()
logger.info("server is stop")
