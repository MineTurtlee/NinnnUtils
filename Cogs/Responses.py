import discord; from discord.ext.commands import *; from discord import app_commands
from Shared.Fun import *

async def setup(bot): await bot.add_cog(Responses(bot))

class Responses(Cog): 
    def __init__(self, bot): self.bot = bot

    @hybrid_group(name="responses", description="Autorespond config", invoke_without_command=True)
    async def r(self, ctx): pass

    @r.command(name="add", description="Add a trigger word and random responses for this server")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        word="The word that triggers the bot",
        reply1="Mandatory first response",
        reply2="Optional second response",
        reply3="Optional third response",
        reply4="Optional fourth response"
    )
    @has_permissions(manage_guild=True)
    async def auto_reply(self, ctx: Context, word: str, reply1: str, reply2: str = None, reply3: str = None, reply4: str = None):
        guild_id = str(ctx.guild.id)
        trigger_word = word.lower()
        replies = [r for r in [reply1, reply2, reply3, reply4] if r is not None]
        fun_data = load_fun_data()
        if guild_id not in fun_data:
            fun_data[guild_id] = {}
        fun_data[guild_id][trigger_word] = replies
        save_fun_data(fun_data)
        embed = discord.Embed(
            title="<:spark:1517583248421552305> Fun Reply Added!",
            description=f"Whenever someone says **{word}** in this server, I will randomly reply with one of these:",
            color=discord.Color.purple()
        )
        for i, r in enumerate(replies, 1):
            embed.add_field(name=f"Reply {i}", value=r, inline=False)
        await ctx.send(embed=embed)


    @r.command(name="clear", description="Remove a trigger word from this server's fun system")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(word="The trigger word you want to delete")
    @has_permissions(manage_guild=True)
    async def auto_reply_clear(interaction: discord.Interaction, word: str):
        guild_id = str(interaction.guild.id)
        trigger_word = word.lower()
        fun_data = load_fun_data()
        if guild_id in fun_data and trigger_word in fun_data[guild_id]:
            del fun_data[guild_id][trigger_word]
            if not fun_data[guild_id]:
                del fun_data[guild_id]
            save_fun_data(fun_data)
            embed = discord.Embed(
                title="<:trash:1517497581058527404> Trigger Cleared",
                description=f"Successfully removed the word **{word}** from this server's auto-reply system.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"<:disapprove:1517452151012589662> '{word}' isn't registered as a fun reply trigger in this server.", ephemeral=True)

    