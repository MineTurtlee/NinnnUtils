from discord import Message
from discord.ext.commands import Cog

async def setup(bot):
    await bot.add_cog(Prefix(bot))

class Prefix(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.content.startswith(self.bot.command_prefix):
            return
            # To enable prefix command, uncomment (remove """) the lines below

            """
            context = self.bot.get_context(message)
            if context.valid:
                await self.bot.invoke(context)
            """