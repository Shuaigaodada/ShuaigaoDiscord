import interactions
import command

PlaylistModal = interactions.Modal(
    interactions.ShortText(
        label="列表名称", 
        custom_id=command.list_name,
        placeholder="输入播放列表的名称",
        required=True,
        max_length=50
        ),
    interactions.ParagraphText(
        label="导入URL",
        custom_id=command.list_url,
        placeholder="输入播放列表的URL",
        required=False,
        max_length=200
    ),
    title="创建播放列表"
)

CheckVIPModal = interactions.Modal(
    interactions.ShortText(
        label="账号:",
        custom_id=command.vip_username,
        placeholder="输入您的账号",
        required=True,
        max_length=100
    ),
    interactions.ShortText(
        label="密码:",
        custom_id=command.vip_password,
        placeholder="请输入您的密码",
        required=True,
        max_length=100
    ),
    title="登入(未开放注册名额)"
)

