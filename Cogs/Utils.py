from discord.ext.commands import Cog, Context, hybrid_command
from discord.app_commands import *
from discord import Member, Embed, Color, PartialEmoji

async def setup(bot):
    await bot.add_cog(Utils(bot))

class Utils(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="avatar", description="Get the profile picture of a user")
    @allowed_installs(guilds=True, users=False)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(user="The user to get the avatar from")
    async def avatar(self, ctx: Context, user: Member = None):
        user = user or interaction.user
        embed = Embed(title=f"{user.name}'s Avatar", color=Color.blue())
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @hybrid_command(name="banner", description="Get the profile banner of a user")
    @allowed_installs(guilds=True, users=False)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(user="The user to get the banner from")
    async def banner(self, ctx: Context, user: Member = None):
        user = user or ctx.author
        full_user = await self.bot.fetch_user(user.id)
        if full_user.banner:
            embed = Embed(title=f"{user.name}'s Banner", color=Color.blue())
            embed.set_image(url=full_user.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user.name} does not have a banner.", ephemeral=True)

    @hybrid_command(name="emoji", description="Get the image for a custom emoji")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(emoji="The custom emoji to get the image from")
    async def emoji(self, ctx: Context, emoji: str):
        if not emoji:
            return await ctx.send("<:disapprove:1517452151012589662> Please provide a valid custom emoji.", ephemeral=True)
        try:
            emoji_obj = PartialEmoji.from_str(emoji)
        except Exception:
            return await ctx.send("<:disapprove:1517452151012589662> Please provide a valid custom emoji.", ephemeral=True)
        if not emoji_obj.id:
            return await ctx.send("<:disapprove:1517452151012589662> Please provide a valid custom emoji.", ephemeral=True)
        embed = Embed(title=f"Emoji: {emoji_obj.name}", color=Color.blue())
        embed.set_image(url=emoji_obj.url)
        await ctx.send(embed=embed)
