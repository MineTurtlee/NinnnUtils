from discord.ext.commands import Cog, hybrid_command, Context
from discord.app_commands import allowed_contexts, allowed_installs
import os

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
