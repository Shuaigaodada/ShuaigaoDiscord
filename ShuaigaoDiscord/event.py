import json
import modal
import random
import assets
import userui
import engine
import asyncio
import command
import datetime
import interactions
from loguru import logger
from typing import Dict, List, Any
from interactions.api.voice.audio import AudioVolume
from interactions import Message, ModalContext, SlashContext, \
                        StringSelectMenu, StringSelectOption, \
                        ComponentContext

temp: Dict[str, Dict] = dict()

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
            if user_id not in temp:
                temp[user_id] = {}
            temp[user_id]["playlist_select_url"] = url
            await message.edit(content="播放列表导入完成!重新调用 `/playlist` 来播放音乐\n", components=download_Button)
    else:
        musics: List[str] = server.user(user_id).lists(selected)
        
@interactions.component_callback(command.download_list)
async def on_download_list(ctx: interactions.ComponentContext):
    user_id: str = str(ctx.author.id)
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
            await engine.Youtube.playlist.download(message, temp[user_id]["playlist_select_url"], asset.server(ctx.guild_id).join("temp"))
            temp[user_id].pop("playlist_select_url")
        else:
            await modal_ctx.send("账号或密码错误。", ephemeral=True)
    else:
        await modal_ctx.send("账号或密码错误。", ephemeral=True)

@interactions.component_callback(command.select_music)
async def on_select_music_done(ctx: interactions.ComponentContext):
    # TODO: download results, write playing.json data, set description and images.
    message: Message = await ctx.send(content="正在下载中，请稍候....")
    user_id: str = str(ctx.author.id)
    server_id: str = str(ctx.guild_id)
    results: Dict[engine.VideoData] = temp[user_id]["play_result"]
    # free temp
    temp[user_id].pop("play_result")
    # because user only can choose one, so get first value
    selected: str = ctx.values[0]
    # max value is 10, so use simple algorithm
    video: engine.VideoData = None
    for name, video_data in results.items():
        if name == selected:
            video = video_data
            break
    
    # unknow reason can't find video, tell user email 2983536011@qq.com, and log error
    if video is None:
        await ctx.send(content="发生错误, 请联系2983536011@qq.com")
        logger.error(f"video results: {results}")
        return
    
    # download video, return path
    path: str = await engine.Youtube.download(video, str(ctx.guild_id))
    await message.edit(content="正在获取信息中，请稍候...")
    await video.fill_info()
    # start write playing.json info
    asset = assets.Assets()
    end_time: str = str(datetime.timedelta(seconds=video.duration))
    end_time = end_time.split(":")[1] + ":" + end_time.split(":")[2]
    config: Dict[str, Any] = {
        "music-path": path,
        "duration": end_time,
    }
    with open(asset.server(server_id).join("temp", "playing.json"), "w") as file:
        json.dump(config, file)
    await play_menu(ctx, message, video)
        
async def play_menu(ctx: SlashContext, message: Message, video: engine.VideoData, disconnect: bool = True,length: int = 20):
    server_id: str = str(ctx.guild_id)
    asset = assets.Assets()
    config_path: str = asset.server(server_id).join("temp", "playing.json")
    with open(config_path, "r") as file:
        config = json.load(file)
        
    # here just init, so don't need use variable
    content: str = "剩余时间: 00:00/" + config["duration"] + " |" + "•" + "━" * (length - 1) + "|\n"
    content += "介绍: " + video.description
    
    color: int = random.randint(0, 0xFFFFFF)
    embed = interactions.Embed(
        title="正在播放: " + video.title,
        description=content,
        color=color
    )
    embed.set_image(video.image[-1]["url"])
    
    # check and join voice channel
    if not ctx.voice_state:
        if ctx.author.voice is None:
            voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, interactions.ChannelType.GUILD_VOICE)]
            channel_names = [interactions.StringSelectOption(label=channel.name, value=channel.name) for channel in voice_channels]
            choiceUI = StringSelectMenu(*channel_names, placeholder="选择机器人播放音乐的位置", custom_id=command.choose_playchannel)
            await ctx.send("请选择机器人播放音乐的位置:", components=choiceUI)
            # TODO when callback join user chice voice channel
        else:
            await ctx.author.voice.channel.connect()
    
    audio = AudioVolume(config["music-path"])
    audio.pre_buffer(3.5)
    await message.edit(embeds=embed, components=userui.get_action())
    temp[ctx.author.id]["play_menu_message"] = message
    
    asyncio.get_event_loop().create_task(update_menu_progress(message, length, config, video, color))
    await ctx.voice_state.play()
    if disconnect:
        await ctx.voice_state.disconnect()
    
    
async def update_menu_progress(message: Message, length: int, config: Dict[str, Any], video: engine.VideoData, color: int):
    # TODO update menu progress
    min, sec = config["duration"].split(":")
    total_sec = int(min) * 60 + int(sec)
    for cursec in range(1, total_sec + 1):
        asyncio.sleep(1)
        progress: int = int((curtime / total_sec) * length)
        progress_bar: str = "|" + ("━" * (progress - 1) + "•" + "━" * (length - 1 - progress)) + "|"
        
        curtime: str = str(datetime.timedelta(seconds=cursec))
        curtime = curtime.split(":")[1] + ":" + curtime.split(":")[2]
        
        content: str = f"剩余时间: {curtime}/" + config["duration"] + " " + progress_bar + "\n"
        content += "介绍: " + video.description
        
        embed = interactions.Embed(
            title="正在播放: " + video.title,
            description=content,
            color=color
        )
        embed.set_image(video.image[-1]["url"])
        
        await message.edit(embeds=embed, components=userui.get_action())
        
        
@interactions.component_callback(command.choose_playchannel)
async def on_choose_playchannel(ctx: ComponentContext):
    choose_channel: str = ctx.values[0]
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, interactions.ChannelType.GUILD_VOICE)]
    channel = None
    for voice_channel in voice_channels:
        if voice_channel.name == choose_channel:
            channel = voice_channel
            break
    await channel.connect()
    

