import command
import interactions

play_status = ("⏸ 播放", command.stop_play) # "▶ 播放", command.continue_play
# "▶︎ 播放"
play_order = "🔁 顺序播放"

def change_status(label: str, cid: str):
    global play_status
    play_status = (label, cid)


def get_row1():
    return [
        # interactions.Button(
        #     label="⏮︎ 上一首",
        #     style=interactions.ButtonStyle.SECONDARY
        # ),
        interactions.Button(
            label=play_status[0],
            style=interactions.ButtonStyle.GREEN,
            custom_id=play_status[1]
        )
        # interactions.Button(
        #     label="⏭ 下一首",
        #     style=interactions.ButtonStyle.SECONDARY
        # )
    ]
def get_row2():
    return [
        # interactions.Button(
        #     label="- 音量🔉",
        #     style=interactions.ButtonStyle.SECONDARY
        # ),
        # interactions.Button(
        #     label=play_order,
        #     style=interactions.ButtonStyle.BLUE
        # ),
        # interactions.Button(
        #     label="+ 音量🔊",
        #     style=interactions.ButtonStyle.SECONDARY
        # )
    ]

def get_action():
    action_row1 = interactions.ActionRow(*get_row1())
    # action_row2 = interactions.ActionRow(*get_row2())
    # return [action_row1, action_row2]
    return [action_row1]

