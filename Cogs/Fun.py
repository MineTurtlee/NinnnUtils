from discord.ext.commands import Cog, Context, hybrid_command
from discord.app_commands import allowed_contexts, allowed_installs, describe
from random import randint, choice
import asyncio

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

    @hybrid_command(name="slot-classic", description="Spin the slot machine!")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def slot(self, ctx: Context):
        emojis = ['🍒', '🍎', '🍇', '💎', '<:bell:1517497562184024275>', '🍋']
        msg = await ctx.send("🎰 **Spinning...**")
        for _ in range(3):
            e1, e2, e3 = (choice(emojis) for _ in range(3))
            await msg.edit(content=f"🎰 | {e1} | {e2} | {e3} |")
            await asyncio.sleep(0.5)
        final_e1, final_e2, final_e3 = (choice(emojis) for _ in range(3))
        if final_e1 == final_e2 == final_e3:
            result_msg = f"🎰 **JACKPOT!** You won!\n\n| {final_e1} | {final_e2} | {final_e3} |"
        else:
            result_msg = f"🎰 Slot Machine:\n\n| {final_e1} | {final_e2} | {final_e3} |\n\nBetter luck next time!"
        await ctx.send(content=result_msg)


    @hybrid_command(name="coinflip-classic", description="Flips a coin and shows Heads or Tails")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def coinflip(self, ctx: Context):
        result = choice(["Heads", "Tails"])
        await ctx.send(f"<:coin:1518351100783231138> The coin landed on: **{result}**!")

    