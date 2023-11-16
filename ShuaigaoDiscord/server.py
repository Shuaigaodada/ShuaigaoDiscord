# coding: utf-8
import os
import re
import json
import modal
import engine
import assets
import command
import subprocess
import interactions
import interactions.ext
from typing import Dict, List
from loguru import logger
from decrypt import decrypt_token
from interactions import OptionType, slash_option
from interactions import Message, SlashContext, StringSelectMenu, ModalContext
from interactions.api.events import MessageCreate

logger.info("initializing server...")
TOKEN: str = decrypt_token()
bot = interactions.Client(token=TOKEN)
logined_user: Dict[str, Dict[Dict, List[str]]] = {}

temp: Dict[str, Dict] = dict()

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

@interactions.component_callback(command.select_list)
async def on_playlist_select(ctx: interactions.ComponentContext):
    server_id: str = str(ctx.guild_id)
    user_id: str = str(ctx.author.id)

    server = assets.Assets().server(server_id)
    # 处理用户的选择
    selected = ctx.values[0]
    if selected == command.add_playlist:
        await ctx.send_modal(modal=modal.PlaylistModal)

        modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal.PlaylistModal)
        await modal_ctx.send("创建播放列表完成", ephemeral=True)

        name = modal_ctx.responses[command.list_name]
        url  = modal_ctx.responses[command.list_url]
        message: Message = await ctx.send(content="正在导入播放列表...")

        if url:
            await engine.Youtube.playlist.Import(url, server.user(user_id).join(name + ".json"))
            download_Button = interactions.Button(
                style=interactions.ButtonStyle.GREEN,
                label="下载列表!",
                custom_id=command.download_list
            )
            temp[command.download_list] = url
            await message.edit(content="播放列表导入完成!重新调用 `/playlist` 来播放音乐\n", components=download_Button)
    else:
        musics: List[str] = server.user(user_id).lists(selected)
        
@interactions.component_callback(command.download_list)
async def on_download_list(ctx: interactions.ComponentContext):
    await ctx.send_modal(modal=modal.CheckVIPModal)
    modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal.CheckVIPModal)

    username = modal_ctx.responses[command.vip_username]
    password = modal_ctx.responses[command.vip_password]
    await modal_ctx.send("登入成功!", ephemeral=True)

    asset = assets.Assets()
    with open(asset.src.file("VIP.json"), "r") as file:
        db = json.load(file)
    if username in db:
        if password == db[username]:
            message: Message = await ctx.send(content="正在准备下载中...")
            await engine.Youtube.playlist.download(message, temp[command.download_list], asset.server(ctx.guild_id).join("temp"))
            temp.pop(command.download_list)
        else:
            await modal_ctx.send("账号或密码错误。", ephemeral=True)
    else:
        await modal_ctx.send("账号或密码错误。", ephemeral=True)


logger.info("starting bot server...")
bot.start()
logger.info("server is stop")
