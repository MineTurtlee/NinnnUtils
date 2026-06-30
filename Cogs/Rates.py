from discord.ext.commands import Cog, Context, hybrid_command
from discord.app_commands import *
from discord import Interaction, Message, Embed, Color
import random
from Shared.Love import *

async def setup(bot):
    await bot.add_cog(Rates())

class Rates(Cog):
    @context_menu(name="Rizz Meter")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def rizz_menu(interaction: Interaction, message: Message):
        percentage = random.randint(0, 100)
        original_text = message.content if message.content else "*[Media or Embed]*"
        await interaction.response.send_message(f"> This message has **{percentage}%** Rizz.\n-# **{message.author.display_name}:** {original_text}")


    @context_menu(name="Cringe Meter")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def cringe_menu(interaction: Interaction, message: Message):
        percentage = random.randint(0, 100)
        original_text = message.content if message.content else "*[Media or Embed]*"
        await interaction.response.send_message(f"> This message is **{percentage}%** Cringe.\n-# **{message.author.display_name}:** {original_text}")


    @context_menu(name="Stupid Meter")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def stupid_menu(interaction: Interaction, message: Message):
        percentage = random.randint(0, 100)
        original_text = message.content if message.content else "*[Media or Embed]*"
        await interaction.response.send_message(f"> This message is **{percentage}%** Stupid.\n-# **{message.author.display_name}:** {original_text}")


    @context_menu(name="Lie Meter")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lie_menu(interaction: Interaction, message: Message):
        percentage = random.randint(0, 100)
        original_text = message.content if message.content else "*[Media or Embed]*"
        await interaction.response.send_message(f"> This message is **{percentage}%** a Lie.\n-# **{message.author.display_name}:** {original_text}")


    @hybrid_command(name="love", description="Check the compatibility between two things or users")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(item1="The first person or thing", item2="The second person or thing")
    async def love(interaction: Interaction, item1: str, item2: str):
        love_data = load_love_data()
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        if guild_id not in love_data:
            love_data[guild_id] = {}
        pair = sorted([item1.lower().strip(), item2.lower().strip()])
        match_key = f"{pair[0]}&{pair[1]}"
        if match_key in love_data[guild_id]:
            score = love_data[guild_id][match_key]
        else:
            score = random.randint(1, 100)
            love_data[guild_id][match_key] = score
            save_love_data(love_data)
        filled = max(0, int(score / 10))
        bar = "<:Square_Red:1517679897068306522>" * filled + "<:Square_Black:1517679889615032540>" * (10 - filled)
        embed = Embed(title="Love Compatibility <:heart:1517577673763979344>", color=Color.red())
        embed.add_field(name="Match", value=f"{item1} & {item2}", inline=False)
        embed.add_field(name="Compatibility", value=f"**{score}%**\n{bar}", inline=False)
        await interaction.response.send_message(embed=embed)
