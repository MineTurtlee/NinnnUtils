from discord.ext.commands import Cog, hybrid_command, Context
from discord.app_commands import allowed_contexts, allowed_installs
from discord import Color, Embed, __version__
import os
from dotenv import load_dotenv

async def setup(bot):
    await bot.add_cog(Bot(bot))

class Bot(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @hybrid_command(name="version", description="Display the bot's version")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ver(self, ctx: Context):
        VERSION = os.getenv('BOT_VERSION')
        VERSION_ALTERNATE = os.getenv('BOT_VERSION_ALTERNATE')
        ACTIVITY_TEXT = os.getenv('ACTIVITY')
        await ctx.send(f"<:gear:1517576939097952496> Current version: {VERSION} | Alternate: {VERSION_ALTERNATE} | {ACTIVITY_TEXT}")

    @hybrid_command(name="ping", description="Check the bot's latency to Discord")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"<:gear:1517576939097952496> Pong! Latency is **{latency}ms**")

    @hybrid_command(name="stats", description="Show bot statistics and status")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def stats(self, ctx: Context):
        load_dotenv(override=True)
        VERSION = os.getenv('BOT_VERSION')
        VERSION_ALTERNATE = os.getenv('BOT_VERSION_ALTERNATE')
        ACTIVITY_TEXT = os.getenv('ACTIVITY')
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_guilds = len(self.bot.guilds)
        embed = Embed(
            title="<:gear:1517576939097952496> Bot Statistics",
            color=Color.gold(),
            description="Current status and technical details of the bot."
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url)
        embed.add_field(name="<:internet:1518376144246804672> Servers", value=str(total_guilds), inline=True)
        embed.add_field(name="<:graph:1517584522877866065> Total Users", value=str(total_members), inline=True)
        embed.add_field(name="<:hourglass:1517574046252924938> Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="<:python:1518376147413635154> Library", value=f"discord.py {__version__}", inline=True)
        embed.add_field(name="<:gear:1517576939097952496> Version", value=f"ver{VERSION} | alt{VERSION_ALTERNATE} | {ACTIVITY_TEXT}", inline=True)
        guild_shard_id = ctx.guild.shard_id if ctx.guild else 0
        total_shards = len(ctx.bot.shards) or 1
        shard_info = f"Shard id: {guild_shard_id} | total: {total_shards}"
        embed.add_field(name="<:shard:1518376149741338744> Shard Info", value=shard_info, inline=True)
        embed.add_field(name="<:nUtils:1518376146008539146> Bot owner", value="-ImNinnn- (imninnn.)", inline=True)
        await ctx.send(embed=embed)

