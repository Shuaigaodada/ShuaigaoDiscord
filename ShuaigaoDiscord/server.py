# coding: utf-8
import os
import re
import json
import subprocess
import interactions
import interactions.ext
from typing import Dict, List
from loguru import logger
from decrypt import decrypt_token
from interactions import OptionType, slash_option

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
async def on_message(event: interactions.events.MessageCreate):
    message: interactions.Message = event.message
    logger.info(f"message received: {message.content} from {message.author.username}")
    

@interactions.slash_command(name="ping", description="测试与服务器的连接")
@load_config("ping")
async def ping(ctx: interactions.SlashContext, ip: str, frequency: int = 10):
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



logger.info("starting bot server...")
bot.start()
logger.info("server is stop")
