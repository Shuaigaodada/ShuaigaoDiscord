# coding: utf-8
import os
import re
import json
import userui
import random
import engine
import assets
import command
import threading
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
    
@interactions.slash_command(name="play", description="搜索并播放选择的音乐")
@load_config("play")
async def play(ctx: SlashContext, query: str, max_resluts: int = 5):
    logger.info(f"start searching {query}, command auother: {ctx.author.username}")
    results: List[engine.VideoData] = await engine.Youtube.search(query, max_resluts)
    names: List[str] = [res.title for res in results]
    logger.info(f"results: {names}")
    select_menu = StringSelectMenu(
        *names,
        placeholder="选择想要播放的音乐",
        min_values=1,
        max_values=1,
        custom_id=command.select_music
    )
    if str(ctx.author.id) not in temp:
        temp[str(ctx.author.id)] = {}
    temp[str(ctx.author.id)]["play_result"] = results
    await ctx.send(content="请选择想要播放的音乐:", components=select_menu)

@interactions.slash_command(name="ping", description="测试与服务器的连接")
@load_config("ping")
async def ping(ctx: SlashContext, ip: str, frequency: int = 10):
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
        await ctx.send("无效的 IP 地址。")
        logger.error(f"invalid ip address: {ip}")
        return
    
    logger.info(f"start pinging {ip}")
    message = await ctx.send(f"正在向 {ip} 发送ping请求")
    process = subprocess.Popen(
        ["ping", "-c", str(frequency), ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # 循环读取输出
    out = ""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            out += output.strip() + "\n"

    rc = process.poll()
    out += "\nping已结束\nwebsocket 连接延迟: " + str(bot.latency) + "s"

    if len(out) >= 2000:
        out = out[:2000]

    await message.edit(out)
    logger.info(f"end pinged {ip}")
    return rc

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


async def playMusic(ctx: SlashContext, video: engine.VideoData):
    embed = interactions.Embed(
        title="正在播放: " + video.title,
        description="介绍: " + video.description,
        color=random.randint(0, 0xFFFFFF)
    )
    embed.set_image(video.image[-1]["url"])
    asset = assets.Assets()
    server = ctx.guild_id
    with open(asset.server(server).join("temp", "playing.json"), "r") as file:
        play_data = json.load(file)
    audio: AudioVolume = AudioVolume(play_data["music-path"])

    if not ctx.voice_state:
        if ctx.author.voice is None:
            voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, interactions.ChannelType.GUILD_VOICE)]
            channel_names = [interactions.StringSelectOption(label=channel.name, value=channel.name) for channel in voice_channels]
            choiceUI = StringSelectMenu(*channel_names, placeholder="选择机器人播放音乐的位置", custom_id=command.choose_playchannel)
            await ctx.send("请选择机器人播放音乐的位置:", components=choiceUI)
            # TODO when callback join user chice voice channel
        else:
            await ctx.author.voice.channel.connect()
    
    audio.pre_buffer(4.5)
    message = await ctx.send(embeds=embed, components=userui.get_action())
    
    await ctx.voice_state.play(audio)
    await ctx.voice_state.disconnect()

logger.info("starting bot server...")
bot.start()
logger.info("server is stop")
