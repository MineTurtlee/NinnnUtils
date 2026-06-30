from discord.ext.commands import Cog, hybrid_group, Context
from discord import TextChannel, Color, Embed, ChannelType, Forbidden, Activity, ActivityType, Status
from discord.app_commands import describe
from main import NinnnUtils
from Shared.Errors import *
import asyncio

async def setup(bot):
    await bot.add_cog(Owner(bot))

class Owner(Cog):
    def __init__(self, bot: NinnnUtils):
        self.bot = bot

    async def cog_load(self):
        await self.bot.wait_until_ready()
        self.rpc = self.bot.get_cog("RPC")

    @hybrid_group(name="owner", description="Owner commands", invoke_without_command=True)
    async def owr(self, ctx):
        pass

    @owr.command(name="own-shutdown", description="(owner) Stop the bot for an update or just to restart")
    @describe(
        channel="Optional announcement channel to send the shutdown message to",
        reason="The shutdown reason to publish"
    )
    async def own_shutdown(
        self,
        ctx: Context,
        channel: TextChannel = None,
        reason: str = "No reason provided"
    ):
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send("<:disapprove:1517452151012589662> Do not even try...", ephemeral=True)

        target_channel = channel or bot.get_channel(1514173159052415026)
        if target_channel is None and isinstance(ctx.channel, TextChannel):
            target_channel = ctx.channel

        shutdown_text = (
            f"🔌 {reason}"
        )
        shutdown_embed = Embed(
            title="Bot Shutdown Initiated",
            description=shutdown_text,
            color=Color.light_gray()
        )

        published = False
        if target_channel is not None:
            try:
                sent_msg = await target_channel.send(embed=shutdown_embed)
                if target_channel.type == ChannelType.news:
                    try:
                        await sent_msg.publish()
                        published = True
                    except Exception:
                        published = False
            except Forbidden as error:
                add_bot_error_entry(ctx.guild.id if ctx.guild else None, target_channel.id, ctx.author, "shutdown notice", error)
                await ctx.send(
                    f"<:disapprove:1517452151012589662> Could not send the shutdown notice to {target_channel.mention}.",
                    ephemeral=True
                )
                return
            except Exception as e:
                await ctx.send(
                    f"<:disapprove:1517452151012589662> Could not send the shutdown notice to {target_channel.mention}. Error: {e}",
                    ephemeral=True
                )
                return

        if self.rpc.update_presence.is_running():
            self.rpc.update_presence.cancel()
            await asyncio.sleep(1)

        response_text = "Going to sleep..."
        if target_channel is not None:
            response_text = (
                f"Shutdown notice sent to {target_channel.mention}. "
                + ("Published to followers." if published else "")
            )

        await ctx.send(response_text)

        shutdown_activity = Activity(type=ActivityType.watching, name="App is shutting down!!! !! !")
        sleep_activity = Activity(type=ActivityType.watching, name="App is sleeping... zZzZzZ") # ok cool
        for shard_id in self.bot.shards:
            await self.bot.change_presence(activity=shutdown_activity, status=Status.dnd, shard_id=shard_id)
        await asyncio.sleep(10)
        for shard_id in self.bot.shards:
            await self.bot.change_presence(activity=sleep_activity, status=Status.idle, shard_id=shard_id)
        self.rpc.close_local_rpc()
        await self.bot.close()
