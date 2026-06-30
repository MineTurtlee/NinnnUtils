from discord.ui import View, Button
from discord import Interaction, ButtonStyle
from Shared.Inventory import *
from Shared.Data import *
from Shared.User import *

class ShopView(View):
    def __init__(self, shop_items, guild_id):
        super().__init__(timeout=None)
        self.shop_items = shop_items
        self.guild_id = guild_id
        for item_name, info in shop_items.items():
            self.add_buy_button(item_name, info)

    def add_buy_button(self, name, info):
        button = Button(
            label=f"Buy {name} (${info['price']})",
            style=ButtonStyle.primary,
            custom_id=f"buy_{name}"
        )

        async def button_callback(interaction: Interaction):
            data = load_data()
            user_data = get_user_data(data, self.guild_id, str(interaction.user.id))
            price = info['price']

            if user_data["balance"] < price:
                await interaction.response.send_message("<:disapprove:1517452151012589662> You can't afford this!", ephemeral=True)
                return

            user_data["balance"] -= price
            inventory_add(user_data["inventory"], name)
            save_data(data)
            await interaction.response.send_message(f"<:approve:1517452125687513158> You bought **{name}**!", ephemeral=True)

        button.callback = button_callback
        self.add_item(button)