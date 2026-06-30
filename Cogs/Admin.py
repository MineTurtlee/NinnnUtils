from discord.ext.commands import hybrid_group, Cog, Context
from discord import Member, VoiceChannel, Embed, Color
from discord.app_commands import allowed_installs, default_permissions, describe

async def setup(bot):
    await bot.add_cog(Admin(bot))

class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @hybrid_group(name="admin", description="Admin commands", invoke_without_command=True)
    async def a(self, ctx):
        pass

    @a.command(name="adm-voice-move", description="Move everyone in your current voice channel to another voice channel")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(move_members=True)
    @describe(
        channel="Target voice channel to move everyone into"
    )
    async def adm_voice_move(self, ctx: Context, channel: VoiceChannel):
        member = ctx.author
        if not isinstance(member, Member):
            member = ctx.guild.get_member(ctx.author.id)

        if not member or not member.voice or not member.voice.channel:
            await ctx.send("<:disapprove:1517452151012589662> You must be connected to a voice channel to use this command.", ephemeral=True)
            return

        source_channel = member.voice.channel
        if source_channel.id == channel.id:
            await ctx.send("<:approve:1517452125687513158> You are already in the target voice channel.", ephemeral=True)
            return

        moved_members = []
        failed_members = []
        for target_member in list(source_channel.members):
            try:
                await target_member.move_to(channel, reason=f"Voice move initiated by {ctx.author}")
                moved_members.append(target_member.display_name)
            except Exception as e:
                failed_members.append(f"{target_member.display_name}: {e}")

        embed = Embed(
            title="Voice Move Complete",
            description=f"Moved {len(moved_members)} user(s) from **{source_channel.name}** to **{channel.name}**.",
            color=Color.blurple()
        )
        if moved_members:
            embed.add_field(name="Moved", value="\n".join(moved_members[:25]), inline=False)
        if failed_members:
            embed.add_field(name="Failed", value="\n".join(failed_members[:25]), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)