from discord.ext.commands import hybrid_group, Cog, Context, HybridGroup, has_permissions
from discord import Member, VoiceChannel, Embed, Color, Forbidden, PermissionOverwrite, HTTPException
from discord.app_commands import allowed_installs, default_permissions, describe
from typing import Optional
from datetime import datetime, timedelta
from Shared.User import *
from Shared.Errors import *

async def setup(bot):
    await bot.add_cog(Admin(bot))

class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @hybrid_group(name="admin", description="Admin commands", invoke_without_command=True)
    async def a(self, ctx):
        pass

    @a.group(name="voice", description="Admin voice commands", invoke_without_command=True)
    async def v(self, ctx):
        pass

    @a.group(name="purge", description="Purge commands")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(manage_messages=True)
    @has_permissions(manage_messages=True)
    @describe(
        amount="Number of messages to delete",
        user="Optional: Only delete messages from this specific user"
    )
    async def p(self, ctx: Context, amount: int, user: Optional[Member] = None):
        if amount <= 0:
            await ctx.send("<:disapprove:1517452151012589662> Please specify a number greater than 0.", ephemeral=True)
            return
        if amount > 100:
            await ctx.send("<:warning:1517452174991556758> For safety, you can only purge up to 100 messages at a time.", ephemeral=True)
            return

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=False)

        def is_user(m):
            return m.author == user if user else True

        try:
            deleted = await ctx.channel.purge(limit=amount, check=is_user, before=datetime.now().timestamp())
            user_str = f" from {format_user_reference(user)}" if user else ""
            await ctx.send(f"<:explosive:1517578642723573880> Successfully deleted **{len(deleted)}** messages{user_str}.", ephemeral=False)
        except Exception as e:
            await ctx.send(f"<:disapprove:1517452151012589662> Failed to purge messages. Error: {e}", ephemeral=True)


    @v.command(name="move", description="Move everyone in your current voice channel to another voice channel")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(move_members=True)
    @has_permissions(move_members=True)
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

    @a.command(name="rename", description="Rename a user or reset their nickname")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(manage_nicknames=True)
    @has_permissions(manage_nicknames=True)
    @describe(
        user="The member you want to rename",
        name="The new nickname (leave empty to reset to original name)"
    )
    async def rename(self, ctx: Context, user: Member, name: str = None):
        if ctx.guild.me.top_role <= user.top_role:
            await ctx.send("<:disapprove:1517452151012589662> I cannot rename this user. Their role is higher than or equal to mine!", ephemeral=True)
            return
        try:
            old_name = user.display_name
            await user.edit(nick=name)
            if name:
                await ctx.send(f"<:approve:1517452125687513158> Changed **{old_name}**'s nickname to **{name}**.")
            else:
                await ctx.send(f"<:approve:1517452125687513158> Reset **{old_name}**'s nickname to their original username.")
        except Forbidden:
            await ctx.send("<:disapprove:1517452151012589662> I don't have the 'Manage Nicknames' permission or the user is the Server Owner.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"<:disapprove:1517452151012589662> An error occurred: {e}", ephemeral=True)

    @p.command(name="nuke", description="Fully clear a channel")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(manage_channels=True)
    @has_permissions(manage_channels=True)
    async def nuke(self, ctx: Context, archive: bool = False):
        try:
            channel = await ctx.guild.fetch_channel(ctx.channel)
        except Forbidden:
            await ctx.send("<:disapprove:1517452151012589662> I cannot 'see' this channel. Please check my permissions in this specific channel's settings.", ephemeral=True)
            return

        GIF_URL = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2x1ZW82ZGdlZzV1MTFzNGF6ajJzZ3Bmc3I2MDlxaXp0cWpkcTY4YyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/fXhYwggfsp3yHBsdlr/giphy.gif"

        await ctx.send("<:explosive:1517578642723573880> Target locked. Nuking...", ephemeral=False)
        new_channel = await channel.clone(reason=f"Nuke by {ctx.author}")
        await new_channel.edit(position=channel.position)

        embed = Embed(
            title="<:nuke:1517497573986926732> Channel Nuked",
            description=f"This is {format_user_reference(ctx.author)}'s fault, THEY DID THIS",
            color=Color.red()
        )
        embed.set_image(url=GIF_URL)
        try:
            await new_channel.send(embed=embed)
        except Forbidden as error:
            add_bot_error_entry(ctx.guild.id, new_channel.id, ctx.author, "nuke result message", error)

        try:
            if archive:
                everyone_role = ctx.guild.default_role
                await channel.edit(
                    name=f"{channel.name}-archived",
                    overwrites={everyone_role: PermissionOverwrite(view_channel=False)},
                    reason="Channel Archived via Nuke"
                )
            else:
                await channel.delete(reason="Nuked")
        except Forbidden:
            try:
                await new_channel.send("<:warning:1517452174991556758> **Warning:** I couldn't delete or hide the old channel. Check if my role is high enough!")
            except Forbidden as error:
                add_bot_error_entry(ctx.guild.id, new_channel.id, ctx.author, "nuke cleanup warning", error)
        except Exception as e:
            print(f"Error during nuke cleanup: {e}")

    @a.command(name="timeout", description="Timeout a member for a specific duration")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(moderate_members=True)
    @has_permissions(moderate_members=True)
    @describe(
        member="The member to timeout",
        days="Number of days",
        hours="Number of hours",
        minutes="Number of minutes",
        seconds="Number of seconds",
        reason="Why is this user being timed out?"
    )
    async def timeout(self, ctx: Context, member: Member, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0, reason: str = "No reason provided"):
        duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        if duration.total_seconds() <= 0:
            await ctx.send("<:disapprove:1517452151012589662> You must specify a duration greater than 0!", ephemeral=True)
            return
        if duration.total_seconds() > 2419200:
            await ctx.send("<:disapprove:1517452151012589662> Timeout cannot exceed 28 days.", ephemeral=True)
            return

        if ctx.author != member and member.top_role >= ctx.author.top_role:
            await ctx.send("<:disapprove:1517452151012589662> You cannot timeout someone with an equal or higher role than yours.", ephemeral=True)
            return

        time_str = f"{days}d {hours}h {minutes}m {seconds}s"
        if not member.bot:
            try:
                dm_embed = Embed(
                    title="<:hourglass:1517574046252924938> You have been timed out",
                    description=f"**Server:** {ctx.guild.name}\n**Duration:** {time_str}\n**Reason:** {reason}",
                    color=Color.orange()
                )
                await member.send(embed=dm_embed)
            except (Forbidden, HTTPException):
                pass

        try:
            await member.timeout(duration, reason=reason)
            confirm_embed = Embed(
                title="<:approve:1517452125687513158> User Timed Out",
                description=f"**{format_user_reference(member)}** has been timed out for {time_str}.",
                color=Color.green()
            )
            confirm_embed.add_field(name="Reason", value=reason)
            await ctx.send(embed=confirm_embed)
        except Forbidden:
            await ctx.send("<:disapprove:1517452151012589662> I don't have permission to timeout this user (Hierarchy issue).", ephemeral=True)
        except Exception as e:
            await ctx.send(f"<:disapprove:1517452151012589662> An error occurred: {e}", ephemeral=True)

