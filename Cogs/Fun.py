from discord.ext.commands import Cog, Context, hybrid_command
from discord.app_commands import allowed_contexts, allowed_installs, describe
from random import randint, choice

async def setup(bot):
    await bot.add_cog(Fun(bot))

class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="roll", description="Roll a 6-sided die")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def roll(self, ctx: Context):
        result = randint(1, 6)
        await ctx.send(f"🎲 You rolled a **{result}**!")

    @hybrid_command(name="random", description="Pick a random number between two values")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(min_value="The lowest number", max_value="The highest number")
    async def random_cmd(self, ctx: Context, min_value: int, max_value: int):
        low, high = min(min_value, max_value), max(min_value, max_value)
        result = randint(low, high)
        await ctx.send(f"<:list:1517497572770451567> Your random number between **{low}** and **{high}** is: **{result}**")

    @hybrid_command(name="say", description="Make the bot say something")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def say(self, ctx: Context, message: str):
        await ctx.send(message)
