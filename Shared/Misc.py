from discord.ext.commands import Context

def is_server_owner(ctx: Context):
    return ctx.author.id == ctx.guild.owner_id

def normalize_item(name: str) -> str:
    return name.strip().title()

def find_item_key(dictionary: dict, item_name: str) -> str | None:
    target = item_name.strip().lower()
    for key in dictionary:
        if key.lower() == target:
            return key
    return None
