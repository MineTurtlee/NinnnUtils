from discord.ext.commands import Cog, Context, hybrid_command
from discord.app_commands import *
from discord import Interaction, Color
from Views.EmbedModal import CustomEmbedModal

async def setup(bot):
    await bot.add_cog(Custom(bot))

class Custom(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="embed", description="Create a fully-loaded customized embed message using a styling menu")
    @describe(
        color="Choose a preset theme color for the embed accent line",
        footer="Optional: Custom text at the very bottom row of the embed",
        footer_icon="Optional: Direct image URL for a tiny icon next to the footer text",
        thumbnail="Optional: Direct image URL to place as a small card in the top right",
        image="Optional: Direct image URL to place as a giant full-width display banner"
    )
    @choices(
        color=[
            Choice(name="🔴 Red", value="red"),
            Choice(name="🔵 Blue", value="blue"),
            Choice(name="🟢 Green", value="green"),
            Choice(name="🟡 Yellow", value="yellow"),
            Choice(name="🟣 Purple", value="purple"),
            Choice(name="⚫ Dark Grey", value="dark"),
            Choice(name="<:spark:1517583248421552305> Random Color", value="random")
        ]
    )
    async def embed_builder(
        interaction: Interaction,
        color: str = "blue",
        footer: str = None,
        footer_icon: str = None,
        thumbnail: str = None,
        image: str = None
    ):
        color_map = {
            "red": Color.red(),
            "blue": Color.blue(),
            "green": Color.green(),
            "yellow": Color.yellow(),
            "purple": Color.purple(),
            "dark": Color.dark_embed(),
            "random": Color.random()
        }
        chosen_color = color_map.get(color, Color.blue())

        modal = CustomEmbedModal(
            color=chosen_color, 
            thumbnail=thumbnail, 
            image=image, 
            footer_text=footer,
            footer_icon=footer_icon
        )
        await interaction.response.send_modal(modal)
