from discord.ext.commands import Cog, Context, hybrid_group, has_permissions
from discord import app_commands, TextChannel, Forbidden
from Shared.Guild import *
from Shared.Cards import *
from Shared.Errors import *

async def setup(bot):
    await bot.add_cog(Welcomer(bot))

class Welcomer(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @hybrid_group(name="welcome", description="Welcome images", invoke_without_command=True)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def w(self, ctx): pass

    @hybrid_group(name="goodbye", description="Goodbyee", invoke_without_command=True)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def b(self, ctx): pass

    @w.command(name="add", description="Set the channel for welcome images")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def welcome_add(self, ctx: Context, channel: TextChannel):
        guild_config, data = get_guild_config(str(ctx.guild.id))
        guild_config["welcome_channel_id"] = channel.id
        save_guild_data(data)
        await ctx.send(f"<:approve:1517452125687513158> Welcome images will now be sent to {channel.mention}")


    @w.command(name="del", description="Disable welcome images for this server", aliases=["delete", "d"])
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def welcome_del(self, ctx: Context):
        guild_config, data = get_guild_config(str(ctx.guild.id))
        guild_config["welcome_channel_id"] = None
        save_guild_data(data)
        await ctx.send("<:approve:1517452125687513158> Welcome images have been disabled.")


    @b.command(name="add", description="Set the channel for goodbye images")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def goodbye_add(self, ctx: Context, channel: TextChannel):
        guild_config, data = get_guild_config(str(ctx.guild.id))
        guild_config["goodbye_channel_id"] = channel.id
        save_guild_data(data)
        await ctx.send(f"<:approve:1517452125687513158> Goodbye images will now be sent to {channel.mention}")


    @b.command(name="del", description="Disable goodbye images for this server")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def goodbye_del(self, ctx: Context):
        guild_config, data = get_guild_config(str(ctx.guild.id))
        guild_config["goodbye_channel_id"] = None
        save_guild_data(data)
        await ctx.send("<:approve:1517452125687513158> Goodbye images have been disabled.")

    @Cog.listener()
    async def on_member_join(member):
        guild_config, _ = get_guild_config(str(member.guild.id))
        channel_id = guild_config.get("welcome_channel_id")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                try:
                    welcome_file = await create_welcome_card(member)
                    await channel.send(f"Welcome {format_user_reference(member)}!", file=welcome_file)
                except Forbidden as error:
                    add_bot_error_entry(member.guild.id, channel.id, member, "welcome banner", error)
                except Exception as e:
                    print(f"Error creating welcome card: {e}")


    @Cog.listener()
    async def on_member_remove(member):
        guild_config, _ = get_guild_config(str(member.guild.id))
        channel_id = guild_config.get("goodbye_channel_id")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                try:
                    goodbye_file = await create_goodbye_card(member)
                    await channel.send(f"Goodbye {member.display_name}. We'll miss you!", file=goodbye_file)
                except Forbidden as error:
                    add_bot_error_entry(member.guild.id, channel.id, member, "goodbye banner", error)
                except Exception as e:
                    print(f"Error creating goodbye card: {e}")