from main import bot_error_cache
from discord.ext.commands import Context
from datetime import datetime

def add_bot_error_entry(guild_id: int | None, channel_id: int | None, user, source: str, error: Exception):
    global bot_error_cache

    if guild_id is None:
        return

    bot_error_cache.append({
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user": user,
        "command_name": source,
        "error_type": type(error).__name__,
        "error_message": str(error) or "No error message provided",
        "time": datetime.now(),
    })

    if len(bot_error_cache) > 100:
        bot_error_cache = bot_error_cache[-100:]

def add_bot_error(ctx: Context, error: Exception):
    global bot_error_cache

    if ctx.guild is None:
        return

    command_name = getattr(getattr(ctx, "command", None), "qualified_name", None)
    if not command_name:
        command_name = getattr(getattr(ctx, "command", None), "name", "unknown command")

    bot_error_cache.append({
        "guild_id": ctx.guild.id,
        "channel_id": ctx.channel.id,
        "user": ctx.author,
        "command_name": command_name,
        "error_type": type(error).__name__,
        "error_message": str(error) or "No error message provided",
        "time": datetime.now(),
    })

    if len(bot_error_cache) > 100:
        bot_error_cache = bot_error_cache[-100:]