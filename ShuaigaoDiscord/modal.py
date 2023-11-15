import interactions

__all__ = ["PlaylistModal"]

PlaylistModal = interactions.Modal(
    interactions.ShortText(
        label="列表名称", 
        custom_id="playlist_name",
        placeholder="输入播放列表的名称",
        required=True,
        max_length=50
        ),
    interactions.ParagraphText(
        label="导入URL",
        custom_id="playlist_url",
        placeholder="输入播放列表的URL",
        required=False,
        max_length=200
    ),
    title="创建播放列表"
)

