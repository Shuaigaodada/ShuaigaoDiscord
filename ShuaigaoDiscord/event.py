import json
import modal
import assets
import engine
import command
import interactions
from typing import Dict, List
from interactions import Message, ModalContext

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
            temp[user_id] = url
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
            await engine.Youtube.playlist.download(message, temp[user_id], asset.server(ctx.guild_id).join("temp"))
            temp.pop(user_id)
        else:
            await modal_ctx.send("账号或密码错误。", ephemeral=True)
    else:
        await modal_ctx.send("账号或密码错误。", ephemeral=True)

