from discord.ext.commands import Cog, Context, hybrid_command
from discord.app_commands import allowed_installs
from discord import Embed, Color
from Shared.User import *

async def setup(bot):
    await bot.add_cog(Guilds(bot))

class Guilds(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @hybrid_command(name="serverinfo", description="Display detailed information about this server")
    @allowed_installs(guilds=True, users=False)
    async def serverinfo(self, ctx: Context):
        guild = ctx.guild
        created_at = guild.created_at.strftime("%m/%d/%Y %H:%M")
        joined_at = ctx.author.joined_at.strftime("%m/%d/%Y %H:%M") if ctx.author.joined_at else "Unknown"
        total_count = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_count - bot_count

        embed = Embed(title=f"Information for {guild.name}", color=Color.blue())
        embed.add_field(name="<:chalice:1517579767573123092> Server Owner", value=f"{format_user_reference(guild.owner)}", inline=True)
        embed.add_field(name="<:timer:1517996239583576194> Created At", value=created_at, inline=True)
        embed.add_field(name="<:plus:1518348756570079262> Joined At (user)", value=joined_at, inline=True)
        vanity = guild.vanity_url_code if guild.vanity_url_code else "-"
        embed.add_field(name="<:minus:1518348754111959150> Vanity Link", value=vanity, inline=True)
        embed.add_field(name="<:internet:1518376144246804672> Preferred Locale", value=f"{guild.preferred_locale}", inline=True)
        embed.add_field(name="<:shield:1518340640801427566> Verification Level", value=str(guild.verification_level).capitalize(), inline=True)
        boost_info = f"{guild.premium_subscription_count} (Level {guild.premium_tier})"
        embed.add_field(name="<:spark:1517583248421552305> Server Boosts", value=boost_info, inline=True)
        embed.add_field(name="<:drawer:1517497564189036574> Channels", value=f"{len(guild.channels)}", inline=True)
        embed.add_field(name="<:multi:1518348755261460661> Roles", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name="\n<:graph:1517584522877866065> Members", value=" ", inline=False)
        embed.add_field(name="<:approuve:1517452125687513158> Real Accounts", value=str(human_count), inline=True)
        embed.add_field(name="<:dissaprouve:1517452151012589662> Bots", value=str(bot_count), inline=True)
        embed.add_field(name="<:warning:1517452174991556758> Total", value=str(total_count), inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)
