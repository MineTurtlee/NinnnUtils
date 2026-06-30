from discord.ext.commands import Cog, hybrid_group, Context, has_permissions
from discord import app_commands, TextChannel
from main import locked_channels, admin_log_channels, all_paused_guilds, server_pauses
from Shared.Lock import *

async def setup(bot):
    await bot.add_cog(Locks(bot))

class Locks(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_group(name="locks", description="Channel locking", invoke_without_command=True)
    @has_permissions(manage_guild=True)
    async def l(self, ctx): pass

    @l.group(name="admin", description="Admin management", invoke_without_command=True)
    @has_permissions(manage_guild=True)
    async def a(self, ctx): pass

    @l.command(name="add", description="Lock this channel - messages will be logged and deleted.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def lock_command(self, ctx: Context):
        locked_channels[ctx.channel.id] = True
        save_lock_config(locked_channels, admin_log_channels)
        await ctx.send(f"<:locked:1517574877257924809> Channel locked.")

    @l.command(name="remove", description="Unlock this channel.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def unlock_command(self, ctx: Context):
        if ctx.channel.id in locked_channels:
            locked_channels.pop(ctx.channel.id)
            save_lock_config(locked_channels, admin_log_channels)
            await ctx.send("<:unlocked:1517574880034558102> Channel unlocked.")
        else:
            await ctx.send("<:warning:1517452174991556758> This channel is not currently locked.", ephemeral=True)


    @a.command(name="start", description="Enable admin logging in this channel.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def adminadd_command(self, ctx: Context):
        admin_log_channels[ctx.channel.id] = True
        save_lock_config(locked_channels, admin_log_channels)
        await ctx.send("<:list:1517497572770451567> Logging enabled in this channel.")


    @a.command(name="stop", description="Stop admin logging in this channel.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def adminstop_command(self, ctx: Context):
        if ctx.channel.id in admin_log_channels:
            admin_log_channels.pop(ctx.channel.id)
            save_lock_config(locked_channels, admin_log_channels)
            await ctx.send("<:prohibited:1517497579582132436> **Logging stopped.**")
        else:
            await ctx.send("<:warning:1517452174991556758> This channel has no active logging.", ephemeral=True)


    @l.command(name="pause", description="Pause message deletion for this channel or all locked channels.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def pause_command(self, ctx: Context, channel: TextChannel = None):
        guild_id = ctx.guild.id
        if channel is None:
            all_paused_guilds.add(guild_id)
            await ctx.send("<:pause:1517497575219920986> Message deletion paused for all locked channels in this server.")
            return
        if guild_id not in server_pauses:
            server_pauses[guild_id] = set()
        server_pauses[guild_id].add(channel.id)
        await ctx.send(f"<:pause:1517497575219920986> Message deletion paused for {channel.mention}.")


    @l.command(name="resume", description="Resume message deletion for this channel or all locked channels.")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def resume_command(self, ctx: Context, channel: TextChannel = None):
        guild_id = ctx.guild.id
        if channel is None:
            all_paused_guilds.discard(guild_id)
            await ctx.send("<:play:1517497576855965716> Message deletion resumed for all locked channels in this server.")
            return
        if guild_id not in server_pauses:
            server_pauses[guild_id] = set()
        server_pauses[guild_id].discard(channel.id)
        await ctx.send(f"<:play:1517497576855965716> Message deletion resumed for {channel.mention}.")

