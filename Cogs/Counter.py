from discord.ext.commands import *
from discord import *
from Shared.Counter import *

async def setup(bot):
    await bot.add_cog(Counter(bot))

class Counter(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_group(name="counter", description="Management of counters in a guild", invoke_without_command=True)
    async def c(self, ctx): pass

    @c.group(name="channel", description="Management of counters, innit!", invoke_without_command=True)
    async def c2(self, ctx): pass

    @c.group(name="number", description="Number", invoke_without_command=True)
    async def n(self, ctx): pass

    @c2.command(name="set", description="Enable counting in a channel and optionally reset on fail")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The text channel where counting will happen",
        reset_when_fail="If enabled, the current counter resets when someone fails"
    )
    @has_permissions(manage_guild=True)
    async def counter_channel_set(self, ctx: Context, channel: TextChannel, reset_when_fail: bool = False):
        set_counter_channel(str(ctx.guild.id), channel.id, reset_when_fail)
        status_text = "resets on fail" if reset_when_fail else "does not reset on fail"
        await ctx.send(f"<:approve:1517452125687513158> Counter enabled in {channel.mention} and {status_text}.", ephemeral=False)

    @c2.command(name="del", description="Disable counting in a channel")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The channel where counting should be disabled"
    )
    @has_permissions(manage_guild=True)
    async def counter_del(self, ctx: Context, channel: TextChannel):
        removed = remove_counter_channel(str(ctx.guild.id), channel.id)
        if removed:
            await ctx.send(f"<:approve:1517452125687513158> Counter disabled in {channel.mention}.", ephemeral=False)
        else:
            await ctx.send(f"<:warning:1517452174991556758> That channel does not have an active counter.", ephemeral=True)

    @n.command(name="set", description="Set the current count in a counter channel")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The counter channel to update",
        value="The new current count value"
    )
    @has_permissions(manage_guild=True)
    async def counter_number_set(self, ctx: Context, channel: TextChannel, value: int):
        success = set_counter_value(str(ctx.guild.id), channel.id, value)
        if success:
            await ctx.send(f"<:approve:1517452125687513158> Counter in {channel.mention} is now set to {value}.", ephemeral=False)
        else:
            await ctx.send(f"<:warning:1517452174991556758> That channel does not have an active counter.", ephemeral=True)
