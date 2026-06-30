from discord.ext.commands import Cog, Context, hybrid_group, has_permissions, hybrid_command
from main import edited_cache
from discord.app_commands import *
from Shared.Guild import *
from Shared.Cache import *
from Shared.User import *
from Shared.Errors import *
from Views.Deleted import DeletedMediaView
from discord import *

async def setup(bot):
    await bot.add_cog(Ghosts(bot))

class Ghosts(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @hybrid_group(name="ghost", description="Ghost pings detection", invoke_without_command=True)
    async def gd(self, ctx):
        pass

    @gd.command(name="pings", description="ghost ping notifications management", invoke_without_command=True)
    async def p(self, ctx):
        pass

    @gd.command(name="history", description="History management (e.g. deleted/edited)", invoke_without_command=True)
    async def h(self, ctx):
        pass

    @p.command(name="toggle", description="Toggle ghost ping notifications detection for this guild.")
    @allowed_installs(guilds=True, users=False)
    @default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def ghost_toggle(self, ctx: Context):
        guild_id = str(ctx.guild.id)
        guild_config, data = get_guild_config(guild_id)
        
        current_state = guild_config.get("ghost_ping_enabled", False)
        new_state = not current_state
        guild_config["ghost_ping_enabled"] = new_state
        
        save_guild_data(data)
        
        status_text = "<:approve:1517452125687513158> **Enabled**" if new_state else "<:disapprove:1517452151012589662> **Disabled**"
        embed = Embed(
            title="<:ghost:1517497569939558470> Ghost Ping Notifications",
            description=f"Ghost ping notifications are now {status_text}",
            color=Color.green() if new_state else Color.red()
        )
        embed.set_footer(text="When enabled, the bot will notify users if someone pings them and then deletes the message (ghost ping).")
        await ctx.send(embed=embed, ephemeral=False)
        print(f"<:ghost:1517497569939558470> Ghost ping notifications {'enabled' if new_state else 'disabled'} in {ctx.guild.name}")


    @h.command(name="toggle", description="Enable or disable /edited and /deleted history in this guild")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def history_toggle(self, ctx: Context):
        guild_id = str(ctx.guild.id)
        guild_config, data = get_guild_config(guild_id)

        current_state = guild_config.get("edit_delete_history_enabled", True)
        new_state = not current_state
        guild_config["edit_delete_history_enabled"] = new_state
        save_guild_data(data)

        status_text = "<:approve:1517452125687513158> **Enabled**" if new_state else "<:disapprove:1517452151012589662> **Disabled**"
        embed = Embed(
            title="<:drawer:1517497564189036574> Edit/Delete History",
            description=f"Edited and deleted message history is now {status_text} for this server.",
            color=Color.green() if new_state else Color.red()
        )
        embed.set_footer(text="When disabled, /edited and /deleted commands will not show history and deleted/edited events will not be saved.")
        await ctx.send(embed=embed, ephemeral=False)
        print(f"<:drawer:1517497564189036574> Edit/Delete history {'enabled' if new_state else 'disabled'} in {ctx.guild.name}")

    @hybrid_command(name="deleted", description="View recently deleted messages and media")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def deleted(self, interaction: Interaction, user: Member = None):
        clean_cache()
        guild_config, _ = get_guild_config(str(interaction.guild.id))
        if not guild_config.get("edit_delete_history_enabled", True):
            await interaction.response.send_message("<:disapprove:1517452151012589662> Deleted message history is disabled for this server.")
            return
        channel_msgs = [m for m in deleted_cache if m['channel'] == interaction.channel_id]
        if user:
            channel_msgs = [m for m in channel_msgs if m['author'].id == user.id]
        if not channel_msgs:
            await interaction.response.send_message("No deleted messages found in this channel recently.")
            return

        description_lines = []
        media_only_messages = []

        for m in channel_msgs:
            media_indicator = "<:image:1517497571470348539> " if m['media'] else ""
            if m['media']:
                media_only_messages.append(m)
            content_text = m['content'] if m['content'] else "*[Media or Embed]*"
            description_lines.append(f"{media_indicator}**{m['author'].display_name}**: {content_text}\n-# Sent at {m['created_at']}")

        full_description = "\n\n".join(description_lines)
        main_embed = Embed(
            title="<:trash:1517497581058527404> Recent deleted messages:",
            description=full_description,
            color=Color.red()
        )

        if media_only_messages:
            media_only_messages.sort(key=lambda x: x['time'], reverse=True)
            view = DeletedMediaView(media_only_messages, interaction.user)
            view.main_text_layout = "Recent deleted messages:"
            view.main_embed_layout = main_embed
            await interaction.response.send_message(embed=main_embed, view=view)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message(embed=main_embed)

    @hybrid_command(name="edited", description="Show recently edited messages in this channel")
    @app_commands.describe(user="Optional: Only show edited messages from a specific user")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def edited_command(self, ctx: Context, user: Member = None):
        clean_cache()
        guild_config, _ = get_guild_config(str(ctx.guild.id))
        if not guild_config.get("edit_delete_history_enabled", True):
            await ctx.send("<:disapprove:1517452151012589662> Edited message history is disabled for this server.")
            return

        channel_edited = [m for m in edited_cache if m['channel'] == ctx.channel.id]

        if user:
            channel_edited = [m for m in channel_edited if m['author_id'] == user.id]

        if not channel_edited:
            await ctx.send("No messages have been edited in this channel recently.")
            return

        text_layout = ""
        for msg in channel_edited[:7]:
            text_layout += f"**{msg['author'].display_name}**: ~~{msg['old_content']}~~ ➔ {msg['new_content']}\n-# Edited at {msg['edited_at']} | [Jump to Message]({msg['jump_url']})\n\n"

        title_text = "<:edit:1517497568421085256> Recently Edited Messages"

        embed_layout = Embed(
            title=title_text,
            description=text_layout,
            color=Color.orange()
        )

        await ctx.send(embed=embed_layout)

    @hybrid_command(name="errors", description="Show recent bot errors in this server")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def errors(self, ctx: Context):
        clean_cache()

        guild_errors = [entry for entry in bot_error_cache if entry.get("guild_id") == ctx.guild.id]
        if not guild_errors:
            await ctx.send("No bot errors have been recorded for this server recently.")
            return

        recent_errors = list(reversed(guild_errors[-7:]))
        description_lines = []

        for entry in recent_errors:
            channel_id = entry.get("channel_id")
            if channel_id:
                channel_text = f"<#{channel_id}>"
            else:
                channel_text = "Unknown channel"

            user_obj = entry.get("user")
            user_text = getattr(user_obj, "display_name", getattr(user_obj, "name", "Unknown user"))
            error_message = entry.get("error_message", "No error message provided")
            if len(error_message) > 180:
                error_message = error_message[:177] + "..."

            description_lines.append(
                f"**{entry.get('command_name', 'unknown command')}** in {channel_text} by {user_text}\n"
                f"-# {entry.get('error_type', 'Error')}: {error_message}\n"
                f"-# At {entry['time'].strftime('%I:%M %p')}"
            )

        embed = Embed(
            title="<:warning:1517452174991556758> Recent Bot Errors",
            description="\n\n".join(description_lines),
            color=Color.red()
        )
        embed.set_footer(text=f"Showing latest {len(recent_errors)} of {len(guild_errors)} error(s).")
        await ctx.send(embed=embed)

    @hybrid_command(name="forget", description="Clear your messages from the bot's memory")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def forget(self, ctx: Context):
        clean_cache()
        global message_cache, deleted_cache, edited_cache
        
        message_cache = [m for m in message_cache if m['author'].id != ctx.author.id]
        deleted_cache = [m for m in deleted_cache if m['author'].id != ctx.author.id]
        edited_cache = [m for m in edited_cache if m['author'].id != ctx.author.id]
        
        await ctx.send("I've wiped your messages, edits, and media from my memory!", ephemeral=True)

    @hybrid_command(name="adm-forget", description="Clear edited and deleted history of a chosen user")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.default_permissions(manage_messages=True)
    @has_permissions(manage_messages=True)
    async def adm_forget(self, ctx: Context, user: Member):
        clean_cache()
        global message_cache, deleted_cache, edited_cache
        message_cache = [m for m in message_cache if m['author'].id != user.id]
        deleted_cache = [m for m in deleted_cache if m['author'].id != user.id]
        edited_cache = [m for m in edited_cache if m['author'].id != user.id]
        await ctx.send(
            f"Cleared deleted and edited history for {user.display_name}."
        )

    @Cog.listener()
    async def on_message_delete(self, message):
        global message_cache, deleted_cache
        clean_cache()

        for msg in message_cache:
            if msg['id'] == message.id:
                deleted_msg = msg.copy()
                deleted_msg['deleted_at'] = datetime.now().strftime("%I:%M %p")

                history_enabled = True
                ghost_enabled = False
                if message.guild:
                    guild_config, _ = get_guild_config(str(message.guild.id))
                    history_enabled = guild_config.get("edit_delete_history_enabled", True)
                    ghost_enabled = guild_config.get("ghost_ping_enabled", False)

                if history_enabled:
                    deleted_cache.append(deleted_msg)
                if message.guild and not ghost_enabled:
                    break

                if msg['mentions'] and not msg['author'].bot:
                    pinged_users = [user for user in msg['mentions'] if user.id != msg['author'].id]
                    
                    if pinged_users:
                        settings = load_user_settings()
                        mentions_str = " ".join([format_user_reference(user, settings) for user in pinged_users])
                        author_str = format_user_reference(msg['author'], settings)
                        
                        embed = Embed(
                            title="<:ghost:1517497569939558470> Ghost Ping Detected!",
                            description=f"{mentions_str}, you were pinged by {author_str} but the message was deleted.",
                            color=Color.red()
                        )
                        if msg['content']:
                            embed.add_field(name="<:list:1517497572770451567> Deleted Content:", value=msg['content'], inline=False)
                        
                        embed.set_footer(text=f"Sent at {msg['created_at']}")
                        
                        channel = self.bot.get_channel(msg['channel'])
                        if channel:
                            try:
                                await channel.send(embed=embed)
                            except Forbidden as error:
                                add_bot_error_entry(message.guild.id if message.guild else None, msg['channel'], msg['author'], "ghost ping notification", error)
                break


    @Cog.listener()
    async def on_message_edit(before, after):
        if before.author.bot:
            return

        if before.content == after.content:
            return

        global message_cache, edited_cache
        clean_cache()

        history_enabled = True
        if before.guild:
            guild_config, _ = get_guild_config(str(before.guild.id))
            history_enabled = guild_config.get("edit_delete_history_enabled", True)

        for msg in message_cache:
            if msg['id'] == before.id:
                if history_enabled:
                    edited_msg = msg.copy()
                    
                    edited_msg['author_id'] = before.author.id
                    edited_msg['old_content'] = before.content if before.content else "*(Empty original content)*"
                    edited_msg['new_content'] = after.content if after.content else "*(Empty edited content)*"
                    edited_msg['jump_url'] = after.jump_url
                    edited_msg['edited_at'] = datetime.now().strftime("%I:%M %p")
                    
                    edited_cache.append(edited_msg)
                
                msg['content'] = after.content
                break