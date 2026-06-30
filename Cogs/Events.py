from discord.ext.commands import Cog
from discord.ext import commands
from main import NinnnUtils, locked_channels, admin_log_channels, all_paused_guilds, server_pauses, reaction_xp_cooldowns
from datetime import datetime
from discord import Forbidden, Embed, NotFound, Color, utils, Interaction
from discord import app_commands
import traceback
from Shared.Lock import *
from Shared.Blacklist import *
from Shared.Leveling import *
from Shared.Fun import *
from random import choice, randint
from Shared.Boards import *
from Shared.Counter import *
from Shared.Cache import *
from Shared.Errors import *
from Shared.Cards import *
from dotenv import load_dotenv
from os import getenv

async def setup(bot):
    await bot.add_cog(Events(bot))

class Events(Cog):
    def __init__(self, bot: NinnnUtils):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        shard_info = (
            f"{len(self.bot.shards)} shard(s), IDs {list(self.bot.shards.keys())}"
            if self.bot.shards
            else "single process (no sharding)"
        )
        print(f"Logged in as {self.bot.user} (ID: {self.bot.user.id}) - {shard_info}")
        print(f"Serving {len(self.bot.guilds)} guild(s)")
        self.bot.loop.create_task(blacklist_startup_cleanup(self.bot))


    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild and message.channel.id in locked_channels:
            guild_id = message.guild.id

            for log_id in admin_log_channels:
                log_channel = self.bot.get_channel(log_id)
                if log_channel and log_channel.guild.id == guild_id:
                    try:
                        await log_channel.send(f"**[LOCKED]** `{message.author}`: {message.content}")
                    except Forbidden as error:
                        add_bot_error_entry(guild_id, log_id, message.author, "locked channel admin log", error)
                    except Exception:
                        pass

            current_pauses = server_pauses.get(guild_id, set())
            if guild_id in all_paused_guilds or message.channel.id in current_pauses:
                return

            dots = "•" * min(max(len(message.content), 1), 200)
            try:
                await message.delete()
                await message.channel.send(f"<:locked:1517574877257924809> {dots}")
            except Forbidden as error:
                add_bot_error_entry(guild_id, message.channel.id, message.author, "locked channel notice", error)
            except Exception:
                pass
            return

        global message_cache
        clean_cache()

        media_url = message.attachments[0].url if message.attachments else None
        message_cache.append({
            'id': message.id,
            'channel': message.channel.id,
            'author': message.author,
            'content': message.content,
            'media': media_url,
            'mentions': message.mentions,
            'time': datetime.now(),
            'created_at': datetime.now().strftime("%I:%M %p")
        })

        if message.guild:
            guild_id = str(message.guild.id)
            fun_data = load_fun_data()
            if guild_id in fun_data:
                guild_replies = fun_data[guild_id]
                message_words = message.content.lower().split()
                for trigger in guild_replies:
                    if trigger in message_words:
                        response = choice(guild_replies[trigger])
                        try:
                            await message.reply(response)
                        except Forbidden as error:
                            add_bot_error_entry(message.guild.id, message.channel.id, message.author, f"auto-reply: {trigger}", error)
                        except Exception as error:
                            add_bot_error_entry(message.guild.id, message.channel.id, message.author, f"auto-reply: {trigger}", error)
                        break

            if await handle_counter_message(message):
                return

            await add_xp(self.bot, message.author, message.guild, randint(5, 10), announce_channel=message.channel)

        await self.bot.process_commands(message)


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


    @Cog.listener()
    async def on_member_join(member):
        guild_config, _ = get_guild_config(str(member.guild.id))
        channel_id = guild_config.get("welcome_channel_id")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                try:
                    welcome_file = await create_welcome_card(member)
                    await channel.send(f"Welcome {format_user_reference(member)}!", file=welcome_file)
                except Forbidden as error:
                    add_bot_error_entry(member.guild.id, channel.id, member, "welcome banner", error)
                except Exception as e:
                    print(f"Error creating welcome card: {e}")


    @Cog.listener()
    async def on_member_remove(member):
        guild_config, _ = get_guild_config(str(member.guild.id))
        channel_id = guild_config.get("goodbye_channel_id")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                try:
                    goodbye_file = await create_goodbye_card(member)
                    await channel.send(f"Goodbye {member.display_name}. We'll miss you!", file=goodbye_file)
                except Forbidden as error:
                    add_bot_error_entry(member.guild.id, channel.id, member, "goodbye banner", error)
                except Exception as e:
                    print(f"Error creating goodbye card: {e}")


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

        guild_id = str(payload.guild_id)
        board_data = load_board_data()

        if guild_id not in board_data:
            return

        emoji_str = str(payload.emoji)
        if emoji_str not in board_data[guild_id]:
            return

        config = board_data[guild_id][emoji_str]
        if "tracked_messages" not in config:
            config["tracked_messages"] = {}

        message_id_str = str(payload.message_id)

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except Forbidden as error:
            add_bot_error_entry(payload.guild_id, channel.id, None, "reaction board source fetch", error)
            return
        except NotFound:
            return

        reaction = utils.get(message.reactions, emoji=payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji)
        current_count = reaction.count if reaction else 0

        board_channel = self.bot.get_channel(config["channel_id"])
        if not board_channel:
            return

        embed = Embed(
            description=f"{message.content}" if message.content else None,
            color=Color.gold(),
        )
        embed.set_author(name=f"{message.author.display_name}", icon_url=message.author.display_avatar.url)
        if message.attachments:
            attachment = message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)
        formatted_time = datetime.now().strftime("%b %d, %Y - %I:%M %p")
        embed.set_footer(text=f"{formatted_time}")

        content_text = f"{emoji_str} {current_count} in {message.jump_url}"

        if message_id_str in config["tracked_messages"]:
            board_msg_id = int(config["tracked_messages"][message_id_str])
            try:
                board_message = await board_channel.fetch_message(board_msg_id)
                try:
                    await board_message.edit(content=content_text, embed=embed)
                except Forbidden as error:
                    add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board edit", error)
            except NotFound:
                del config["tracked_messages"][message_id_str]
                save_board_data(board_data)
        elif current_count >= config["required_count"]:
            try:
                new_board_msg = await board_channel.send(content=content_text, embed=embed)
            except Forbidden as error:
                add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board post", error)
                return
            config["tracked_messages"][message_id_str] = str(new_board_msg.id)
            save_board_data(board_data)


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id:
            return

        guild_id = str(payload.guild_id)
        board_data = load_board_data()

        if guild_id not in board_data:
            return

        emoji_str = str(payload.emoji)
        if emoji_str not in board_data[guild_id]:
            return

        config = board_data[guild_id][emoji_str]
        if "tracked_messages" not in config:
            return

        message_id_str = str(payload.message_id)
        if message_id_str not in config["tracked_messages"]:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except NotFound:
            return

        reaction = utils.get(message.reactions, emoji=payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji)
        current_count = reaction.count if reaction else 0

        board_channel = self.bot.get_channel(config["channel_id"])
        if not board_channel:
            return

        board_msg_id = int(config["tracked_messages"][message_id_str])
        try:
            board_message = await board_channel.fetch_message(board_msg_id)
            if current_count >= config["required_count"]:
                content_text = f"{emoji_str} {current_count} in {message.jump_url}"
                embed = Embed(description=f"{message.content}" if message.content else None, color=Color.gold())
                embed.set_author(name=f"{message.author.display_name}", icon_url=message.author.display_avatar.url)
                if message.attachments and message.attachments[0].content_type.startswith("image/"):
                    embed.set_image(url=message.attachments[0].url)
                embed.set_footer(text=f"{datetime.now().strftime('%b %d, %Y - %I:%M %p')}")
                await board_message.edit(content=content_text, embed=embed)
            else:
                await board_message.delete()
                del config["tracked_messages"][message_id_str]
                save_board_data(board_data)
        except Forbidden as error:
            add_bot_error_entry(payload.guild_id, config["channel_id"], None, "reaction board fetch", error)
        except NotFound:
            del config["tracked_messages"][message_id_str]
            save_board_data(board_data)

    # Blacklist here !!
    @Cog.listener()
    async def on_guild_join(self, guild):
        load_dotenv(override=True)
        raw_blacklist = getenv('SERVER_BLACKLIST', '')
        BLACKLISTED_GUILDS = [int(sid.strip()) for sid in raw_blacklist.split(',') if sid.strip().isdigit()]
        if guild.id in BLACKLISTED_GUILDS:
            print(f"<:prohibited:1517497579582132436> Joined blacklisted guild: {guild.name} ({guild.id}). Leaving immediately...")
            await guild.leave()
    
    # Events will be here, Cog.listener()

    @Cog.listener()
    async def on_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        original_error = getattr(error, "original", error)
        bot_missing_permissions_error = getattr(app_commands, "BotMissingPermissions", None)

        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = error.retry_after
            if retry_after >= 60:
                minutes = int(retry_after // 60)
                seconds = int(retry_after % 60)
                if seconds > 0:
                    message_text = f"<:hourglass:1517574046252924938> This command is on cooldown. Please wait **{minutes}m {seconds}s** before trying again."
                else:
                    message_text = f"<:hourglass:1517574046252924938> This command is on cooldown. Please wait **{minutes}m** before trying again."
            else:
                retry_after = round(retry_after, 1)
                message_text = f"<:hourglass:1517574046252924938> This command is on cooldown. Please wait **{retry_after}s** before trying again."
            if interaction.response.is_done():
                await interaction.followup.send(message_text, ephemeral=True)
            else:
                await interaction.response.send_message(message_text, ephemeral=True)
        elif isinstance(error, app_commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await interaction.response.send_message(f"<:disapprove:1517452151012589662> You lack the required permissions to run this: `{perms}`", ephemeral=True)
        elif bot_missing_permissions_error is not None and isinstance(error, bot_missing_permissions_error):
            perms = ", ".join(error.missing_permissions)
            message_text = f"<:disapprove:1517452151012589662> I am missing the required permissions to run this: `{perms}`"
            if interaction.response.is_done():
                await interaction.followup.send(message_text, ephemeral=True)
            else:
                await interaction.response.send_message(message_text, ephemeral=True)
        elif isinstance(original_error, Forbidden):
            message_text = "<:disapprove:1517452151012589662> I am missing the permissions required to complete that action."
            if interaction.response.is_done():
                await interaction.followup.send(message_text, ephemeral=True)
            else:
                await interaction.response.send_message(message_text, ephemeral=True)
        else:
            add_bot_error(interaction, original_error)
            command_name = getattr(getattr(interaction, "command", None), "qualified_name", None) or getattr(getattr(interaction, "command", None), "name", "unknown command")
            print(f"Ignored exception in command tree [{command_name}]: {type(original_error).__name__}: {original_error}")
            print("".join(traceback.format_exception(type(original_error), original_error, original_error.__traceback__)))
            if not interaction.response.is_done():
                await interaction.response.send_message("<:disapprove:1517452151012589662> An unexpected error occurred while executing this command.", ephemeral=True)

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        original_error = getattr(error, "original", error)
        bot_missing_permissions_error = getattr(commands, "BotMissingPermissions", None)

        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            if retry_after >= 60:
                minutes = int(retry_after // 60)
                seconds = int(retry_after % 60)
                if seconds > 0:
                    message_text = f"<:hourglass:1517574046252924938> This command is on cooldown. Please wait **{minutes}m {seconds}s** before trying again."
                else:
                    message_text = f"<:hourglass:1517574046252924938> This command is on cooldown. Please wait **{minutes}m** before trying again."
            else:
                retry_after = round(retry_after, 1)
                message_text = f"<:hourglass:1517574046252924938> This command is on cooldown. Please wait **{retry_after}s** before trying again."
            await ctx.reply(message_text, mention_author=False)
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.reply(f"<:disapprove:1517452151012589662> You lack the required permissions to run this: `{perms}`", mention_author=False)
        elif bot_missing_permissions_error is not None and isinstance(error, bot_missing_permissions_error):
            perms = ", ".join(error.missing_permissions)
            message_text = f"<:disapprove:1517452151012589662> I am missing the required permissions to run this: `{perms}`"
            await ctx.reply(message_text, mention_author=False)
        elif isinstance(original_error, Forbidden):
            message_text = "<:disapprove:1517452151012589662> I am missing the permissions required to complete that action."
            await ctx.reply(message_text, mention_author=False)
        else:
            add_bot_error(ctx, original_error)
            command_name = getattr(getattr(ctx, "command", None), "qualified_name", None) or getattr(getattr(ctx, "command", None), "name", "unknown command")
            print(f"Ignored exception in Hybrid command [{command_name}]: {type(original_error).__name__}: {original_error}")
            print("".join(traceback.format_exception(type(original_error), original_error, original_error.__traceback__)))
            await ctx.reply("<:disapprove:1517452151012589662> An unexpected error occurred while executing this command.", ephemeral=True, mention_author=False)
