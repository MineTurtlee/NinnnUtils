from discord.ui import View, Button, button
from discord import ButtonStyle, Embed, Color, Interaction

class DeletedMediaView(View):
    def __init__(self, media_messages, user_who_requested):
        super().__init__(timeout=60)
        self.messages = media_messages
        self.index = 0
        self.requester = user_who_requested
        self.revealed = False
        self.update_button_states()

    def update_button_states(self):
        self.prev_button.disabled = (self.index == 0)
        self.next_button.disabled = (self.index == len(self.messages) - 1)
        if self.revealed:
            self.reveal_button.label = "Hide Media"
            self.reveal_button.style = ButtonStyle.secondary
        else:
            self.reveal_button.label = f"Reveal Media ({self.index + 1}/{len(self.messages)})"
            self.reveal_button.style = ButtonStyle.danger

    def build_media_embed(self):
        msg = self.messages[self.index]
        if self.revealed:
            text_content = msg['content'] if msg['content'] else "No text"
            embed = Embed(
                title=f"<:trash:1517497581058527404> Media sent by {msg['author'].display_name}",
                description=f"**{msg['author'].display_name}**: {text_content}\n-# Sent at {msg['created_at']}",
                color=Color.red()
            )
            embed.set_image(url=msg['media'])
            return embed
        return None

    async def handle_page_update(self, interaction: Interaction):
        self.update_button_states()
        embed = self.build_media_embed()
        if embed:
            await interaction.response.edit_message(content=None, embed=embed, view=self)
        else:
            await interaction.response.edit_message(content=self.main_text_layout, embed=self.main_embed_layout, view=self)

    @button(label="Reveal Media", style=ButtonStyle.danger)
    async def reveal_button(self, interaction: Interaction, button: Button):
        if interaction.user != self.requester:
            await interaction.response.send_message("<:disapprove:1517452151012589662> Only the person who ran the command can reveal media!", ephemeral=True)
            return
        self.revealed = not self.revealed
        await self.handle_page_update(interaction)

    @button(label="Previous media", style=ButtonStyle.primary)
    async def prev_button(self, interaction: Interaction, button: Button):
        if interaction.user != self.requester:
            await interaction.response.send_message("<:disapprove:1517452151012589662> Only the person who ran the command can flip pages!", ephemeral=True)
            return
        if self.index > 0:
            self.index -= 1
            await self.handle_page_update(interaction)

    @button(label="Next media", style=ButtonStyle.primary)
    async def next_button(self, interaction: Interaction, button: Button):
        if interaction.user != self.requester:
            await interaction.response.send_message("<:disapprove:1517452151012589662> Only the person who ran the command can flip pages!", ephemeral=True)
            return
        if self.index < len(self.messages) - 1:
            self.index += 1
            await self.handle_page_update(interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if hasattr(self, 'message'):
                await self.message.edit(view=self)
        except Exception:
            pass