from discord.ext.tasks import loop
from discord import Member, Embed, Color
from discord.ext.commands import Cog, hybrid_command, Context
from discord.app_commands import allowed_installs
from random import randint
from main import reaction_xp_cooldowns
from Shared.Leveling import *
from Shared.User import *

async def setup(bot):
    await bot.add_cog(Leveling(bot))

COLOR_EMOJIS = {
    "white": "<:Square_White:1517679898414813427>", "black": "<:Square_Black:1517679889615032540>", "red": "<:Square_Red:1517679897068306522>", "blue": "<:Square_Blue:1517679890932043897>", 
    "green": "<:Square_Green:1517679893234716843>", "yellow": "<:Square_Yellow:1517679899769311302>", "purple": "<:Square_Purple:1517679895738581062>", "orange": "<:Square_Orange:1517679894526562405>", "brown": "<:Square_Brown:1517679892039204955>"
}

class Leveling(Cog):
    def __init__(self, bot):
        self.bot = bot

    @loop(minutes=2.0)
    async def voice_xp_tracker(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for voice_channel in guild.voice_channels:
                real_members = [m for m in voice_channel.members if not m.bot and not m.voice.self_deaf and not m.voice.deaf]
                if len(real_members) >= 1:
                    for member in real_members:
                        await add_xp(self.bot, member, guild, randint(5, 10))

    @hybrid_command(name="level", description="View your current server tier standing level rank card")
    @allowed_installs(guilds=True, users=False)
    async def view_level(self, ctx: Context, user: Member = None):
        target = user or ctx.author
        levels = load_levels()
        g_id, u_id = str(ctx.guild.id), str(target.id)
        
        user_data = levels.get(g_id, {}).get("users", {}).get(u_id, {"xp": 0, "level": 0, "color": "white"})
        
        current_xp = user_data["xp"]
        current_lvl = user_data["level"]
        chosen_color = get_user_color(u_id) or user_data.get("color", "white") or "white"
        
        xp_needed = get_xp_needed(current_lvl)
        
        ratio = current_xp / xp_needed if xp_needed > 0 else 0
        filled_blocks = min(max(int(ratio * 10), 0), 10)
        empty_blocks = 10 - filled_blocks
        
        filled_emoji = COLOR_EMOJIS.get(chosen_color, "<:Square_White:1517679898414813427>")
        empty_emoji = COLOR_EMOJIS.get("black", "<:Square_Black:1517679889615032540>")
        
        progress_bar = (filled_emoji * filled_blocks) + (empty_emoji * empty_blocks)
        
        embed = Embed(
            title=f"<:chalice:1517579767573123092> Rank Profile - {target.display_name}",
            color=Color.dark_gray()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Current Tier", value=f"<:spark:1517583248421552305> **Level {current_lvl}**", inline=True)
        embed.add_field(name="Experience Nodes", value=f"<:Vial:1517681553377857628> `{current_xp:,}` / `{xp_needed:,}` XP", inline=True)
        embed.add_field(name="Progress Metrics", value=progress_bar, inline=False)
        
        await ctx.send(embed=embed)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        reactor = guild.get_member(payload.user_id)
        if reactor and not reactor.bot:
            cooldown_key = (payload.guild_id, payload.user_id)
            now = datetime.now()
            last_xp = reaction_xp_cooldowns.get(cooldown_key)
            if not last_xp or (now - last_xp).total_seconds() >= 15:
                reaction_xp_cooldowns[cooldown_key] = now
                await add_xp(self.bot, reactor, guild, randint(1, 3), announce_channel=guild.get_channel(payload.channel_id))
            try:
                channel = guild.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                if message.author and not message.author.bot and message.author.id != payload.user_id:
                    await add_xp(self.bot, message.author, guild, randint(3, 5), announce_channel=channel)
            except Forbidden as error:
                add_bot_error_entry(payload.guild_id, payload.channel_id, None, "reaction xp source fetch", error)
            except Exception:
                pass