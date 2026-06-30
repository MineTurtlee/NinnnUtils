from discord.ext.commands import Cog, hybrid_command, Context
from discord import Color, Embed
from discord.app_commands import allowed_contexts, allowed_installs, describe, choices, Choice
from deep_translator import GoogleTranslator
import base64

async def setup(bot):
    await bot.add_cog(Codables(bot))

class Codables(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @hybrid_command(name="encode-decode", description="Encode or decode text using various methods (Base64, Base32, Base16, Binary)")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(
        text="The text you want to process",
        encoding_type="Choose the format method",
        action="Choose whether to encode (encrypt) or decode (decrypt)"
    )
    @choices(
        encoding_type=[
            Choice(name="Base64", value="base64"),
            Choice(name="Base16 (Hex)", value="base16"),
            Choice(name="Binary", value="binary")
        ],
        action=[
            Choice(name="Encode (Text ➔ Format)", value="encode"),
            Choice(name="Decode (Format ➔ Text)", value="decode")
        ]
    )
    async def encode_decode_command(self, ctx: Context, text: str, encoding_type: str, action: str):
        try:
            """if action == "encode":
                text_bytes = text.encode("utf-8")
                if encoding_type == "base64":
                    result = base64.b64encode(text_bytes).decode("utf-8")
                elif encoding_type == "base32":
                    result = base64.b32encode(text_bytes).decode("utf-8")
                elif encoding_type == "base16":
                    result = base64.b16encode(text_bytes).decode("utf-8")
                elif encoding_type == "binary":
                    result = " ".join(f"{ord(char):08b}" for char in text)
                title_text = f"<:locked:1517574877257924809> {encoding_type} Encoding Complete"
                field_name = "Encoded Result:"
                color_choice = discord.Color.red()
            else:
                if encoding_type == "base64":
                    result = base64.b64decode(text.encode("utf-8")).decode("utf-8")
                elif encoding_type == "base32":
                    result = base64.b32decode(text.encode("utf-8")).decode("utf-8")
                elif encoding_type == "base16":
                    result = base64.b16decode(text.encode("utf-8")).decode("utf-8")
                elif encoding_type == "binary":
                    binary_values = text.split()
                    result = "".join(chr(int(b, 2)) for b in binary_values)
                title_text = f"<:unlocked:1517574880034558102> {encoding_type} Decoding Complete"
                field_name = "Decoded Plain Text Result:"
                color_choice = discord.Color.green()"""

            match action:
                case "encode":
                    text_bytes = text.encode("utf-8")
                    match encoding_type:
                        case "base64": result = base64.b64encode(text_bytes).decode("utf-8")
                        case "base32": result = base64.b32encode(text_bytes).decode("utf-8")
                        case "base16": result = base64.b16encode(text_bytes).decode("utf-8")
                        case "binary": result = " ".join(f"{ord(char):08b}" for char in text)
                    title_text = f"<:locked:1517574877257924809> {encoding_type} Encoding Complete"
                    field_name = "Encoded Result:"
                    color_choice = Color.red()
                case "decode":
                    match encoding_type:
                        case "base64": result = base64.b64decode(text.encode("utf-8")).decode("utf-8")
                        case "base32": result = base64.b32decode(text.encode("utf-8")).decode("utf-8")
                        case "base16": result = base64.b16decode(text.encode("utf-8")).decode("utf-8")
                        case "binary":
                            binary_values = text.split()
                            result = "".join(chr(int(b, 2)) for b in binary_values)

                    title_text = f"<:unlocked:1517574880034558102> {encoding_type} Decoding Complete"
                    field_name = "Decoded Plain Text Result:"
                    color_choice = Color.green()

            if len(result) > 1000:
                result = result[:950] + "\n\n*(Truncated due to size limits...)*"

            embed = Embed(title=title_text, color=color_choice)
            embed.add_field(name="Input:", value=f"`{text}`", inline=False)
            embed.add_field(name=field_name, value=f"`{result}`", inline=False)
            embed.set_footer(text=f"Processed for {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            print(f"Cipher Log: \"{ctx.user.name}\" performed {action} using {encoding_type}.")

        except Exception as e:
            await ctx.send(
                f"<:disapprove:1517452151012589662> Operation failed. Please check that your input perfectly matches the formatting for {encoding_type}! Error: {e}",
                ephemeral=True
            )

    @hybrid_command(name="translate", description="Translate text into another language")
    @allowed_installs(guilds=True, users=True)
    @allowed_contexts(guilds=True, dms=True, private_channels=True)
    @describe(
        text="The message you want to translate",
        to_language="The language code to translate into (e.g., 'en', 'es', 'fr', 'ja')",
        from_language="Optional: Specify the original language code (defaults to auto-detect)"
    )
    async def translate(self, ctx: Context, text: str, to_language: str = "en", from_language: str = "auto"):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=False)
        try:
            translator = GoogleTranslator(source=from_language, target=to_language)
            translated_text = translator.translate(text)
            await ctx.send(content=translated_text)
            print(f"translation log : \"{ctx.author.name}\" translated \"{text}\" from {from_language} to \"{translated_text}\" in {to_language}")
        except Exception as e:
            await ctx.send(f"<:disapprove:1517452151012589662> Translation failed. Please ensure you used valid ISO language codes! Error: {e}", ephemeral=True)
