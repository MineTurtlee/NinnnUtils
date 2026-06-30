import json, os
from main import BOARD_FILE
from discord import NotFound, Forbidden, Embed, utils, Color
from Shared.Errors import *

def load_board_data():
    if not os.path.exists(BOARD_FILE):
        return {}
    with open(BOARD_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_board_data(data):
    with open(BOARD_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def update_board(bot, payload, emoji_str, remove_mode=False):
    guild_id = str(payload.guild_id)
    board_data = load_board_data()

    if guild_id not in board_data or emoji_str not in board_data[guild_id]:
        return

    config = board_data[guild_id][emoji_str]
    if "tracked_messages" not in config:
        config["tracked_messages"] = {}

    orig_msg_id = str(payload.message_id)

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return
    try:
        message = await channel.fetch_message(payload.message_id)
    except NotFound:
        return

    reaction = utils.get(message.reactions, emoji=payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji)
    current_count = reaction.count if reaction else 0

    board_channel = bot.get_channel(config["channel_id"])
    if not board_channel:
        return

    embed = Embed(
        description=f"{message.content}" if message.content else None,
        color=Color.gold(),
    )
    embed.set_author(name=f"| {message.author.display_name}", icon_url=message.author.display_avatar.url)
    if message.attachments:
        attachment = message.attachments[0]
        if attachment.content_type and attachment.content_type.startswith("image/"):
            embed.set_image(url=attachment.url)
    formatted_time = message.created_at.strftime("%b %d, %Y - %I:%M %p")
    embed.set_footer(text=f"| {formatted_time}")

    content_text = f"{emoji_str} {current_count} in {message.jump_url}"

    if orig_msg_id in config["tracked_messages"]:
        board_msg_id = int(config["tracked_messages"][orig_msg_id])
        try:
            board_message = await board_channel.fetch_message(board_msg_id)
            if current_count >= config["required_count"]:
                try:
                    await board_message.edit(content=content_text, embed=embed)
                except Forbidden as error:
                    add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board edit", error)
            else:
                try:
                    await board_message.delete()
                except Forbidden as error:
                    add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board delete", error)
                del config["tracked_messages"][orig_msg_id]
                save_board_data(board_data)
        except Forbidden as error:
            add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board fetch", error)
        except NotFound:
            del config["tracked_messages"][orig_msg_id]
            save_board_data(board_data)

    elif current_count >= config["required_count"] and not remove_mode:
        try:
            new_board_msg = await board_channel.send(content=content_text, embed=embed)
        except Forbidden as error:
            add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board post", error)
            return
        config["tracked_messages"][orig_msg_id] = str(new_board_msg.id)
        save_board_data(board_data)