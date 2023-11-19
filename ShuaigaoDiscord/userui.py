import interactions

play_status = "⏸ 播放"
# "▶︎ 播放"
play_order = "🔁 顺序播放"
def get_row1():
    return [
        interactions.Button(
            label="⏮︎ 上一首",
            style=interactions.ButtonStyle.SECONDARY
        ),
        interactions.Button(
            label=play_status,
            style=interactions.ButtonStyle.GREEN
            # ⏸||
        ),
        interactions.Button(
            label="⏭ 下一首",
            style=interactions.ButtonStyle.SECONDARY
        )
    ]
def get_row2():
    return [
        interactions.Button(
            label="- 音量🔉",
            style=interactions.ButtonStyle.SECONDARY
        ),
        interactions.Button(
            label=play_order,
            style=interactions.ButtonStyle.BLUE
        ),
        interactions.Button(
            label="+ 音量🔊",
            style=interactions.ButtonStyle.SECONDARY
        )
    ]

def get_action():
    action_row1 = interactions.ActionRow(*get_row1())
    action_row2 = interactions.ActionRow(*get_row2())
    return [action_row1, action_row2]