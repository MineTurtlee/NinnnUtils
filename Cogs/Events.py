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

        # To process prefixed commands, uncomment the below 
        # await self.bot.process_commands(message)

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

    @Cog.listener()
    async def on_guild_channel_delete(channel):
        changed = False

        if channel.id in locked_channels:
            locked_channels.pop(channel.id)
            changed = True

        if channel.id in admin_log_channels:
            admin_log_channels.pop(channel.id)
            changed = True

        if changed:
            save_lock_config(locked_channels, admin_log_channels)
