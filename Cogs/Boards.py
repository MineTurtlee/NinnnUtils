from discord.ext.commands import Cog, hybrid_group, Context, has_permissions
from discord import app_commands, TextChannel, Embed, Color, RawReactionActionEvent
from Shared.Boards import *

async def setup(bot):
    await bot.add_cog(Boards(bot))

class Boards(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_group(name="boards", description="Boards reaction management")
    async def b(self, ctx): pass

    @b.command(name="add", description="Set up a reaction board for an emoji")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        emoji="The emoji to watch for (standard or custom)",
        required_count="Number of reactions needed to post to the board",
        channel="The channel where board messages will be sent"
    )
    @has_permissions(manage_guild=True)
    async def board_add(self, ctx: Context, emoji: str, required_count: int, channel: TextChannel):
        guild_id = str(ctx.guild.id)
        board_data = load_board_data()
        if guild_id not in board_data:
            board_data[guild_id] = {}
        board_data[guild_id][emoji] = {
            "channel_id": channel.id,
            "required_count": required_count,
            "tracked_messages": {}
        }
        save_board_data(board_data)
        embed = Embed(
            title="<:list:1517497572770451567> Board Configured!",
            description=f"When a message gets {required_count} {emoji} reactions, it will be sent to {channel.mention}.",
            color=Color.green()
        )
        await ctx.send(embed=embed)


    @b.command(name="delete", description="Delete a reaction board configuration", aliases=["del", "d"])
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(emoji="The emoji board you want to remove")
    @has_permissions(manage_guild=True)
    async def board_del(self, ctx: Context, emoji: str):
        guild_id = str(ctx.guild.id)
        board_data = load_board_data()
        if guild_id in board_data and emoji in board_data[guild_id]:
            del board_data[guild_id][emoji]
            if not board_data[guild_id]:
                del board_data[guild_id]
            save_board_data(board_data)
            await ctx.send(f"<:trash:1517497581058527404> Successfully removed the board for {emoji}.")
        else:
            await ctx.send(f"<:disapprove:1517452151012589662> No board configuration found for {emoji} in this server.", ephemeral=True)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        reactor = guild.get_member(payload.user_id)

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
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
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
