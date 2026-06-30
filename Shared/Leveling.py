import os, json, asyncio, io
from PIL import Image, ImageFont, ImageDraw
from discord import Member, Guild, Forbidden, File
from main import BASE_DIR, NinnnUtils, LEVEL_FILE
from .User import *
from .Data import *
from .Errors import *

# ------------------------------------------------------------------------
#                            Data Management                             |
# ------------------------------------------------------------------------
def load_levels():
    if not os.path.exists(LEVEL_FILE):
        return {}
    with open(LEVEL_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}
        
def save_levels(data):
    with open(LEVEL_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# -------------------------------------------------------------------------
#                            Helper Funcs                                 |
# -------------------------------------------------------------------------

def get_xp_needed(level: int) -> int:
    return 100 + (level * 10)

async def add_xp(bot: NinnnUtils, member: Member, guild: Guild, xp_to_add: int, announce_channel=None):
    if member.bot:
        return
        
    levels = load_levels()
    guild_id = str(guild.id)
    user_id = str(member.id)
    
    if guild_id not in levels:
        levels[guild_id] = {"config": {"channel_id": None, "rewards": {}}, "users": {}}
        
    if user_id not in levels[guild_id]["users"]:
        levels[guild_id]["users"][user_id] = {"xp": 0, "level": 0, "color": get_user_color(user_id) or "white"}
        
    user_data = levels[guild_id]["users"][user_id]
    user_data["xp"] += xp_to_add
    
    leveled_up = False
    while user_data["xp"] >= get_xp_needed(user_data["level"]):
        user_data["xp"] -= get_xp_needed(user_data["level"])
        user_data["level"] += 1
        leveled_up = True
        
    save_levels(levels)
    
    if leveled_up:
        rewards = levels[guild_id]["config"].get("rewards", {})
        current_level = user_data["level"]
        reward = rewards.get(str(current_level))
        if reward:
            if isinstance(reward, (str, int)):
                reward = {"role_id": int(reward)}

            if reward.get("money", 0) > 0 or reward.get("give_item") or reward.get("xp", 0) > 0:
                data = load_data()
                economy_user = get_user_data(data, guild_id, member.id)
                if reward.get("money", 0) > 0:
                    economy_user["balance"] += reward["money"]
                if reward.get("give_item"):
                    inventory_add(economy_user["inventory"], reward["give_item"], reward.get("give_item_amount", 1))
                save_data(data)

            if reward.get("role_id"):
                role = guild.get_role(int(reward["role_id"]))
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except Forbidden as error:
                        add_bot_error_entry(guild.id, None, member, f"level reward role: {role.name}", error)

            if reward.get("temp_role_id"):
                role = guild.get_role(int(reward["temp_role_id"]))
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except Forbidden as error:
                        add_bot_error_entry(guild.id, None, member, f"level temp role: {role.name}", error)
                        role = None
                if role and reward.get("duration", 0) > 0:
                    async def remove_temp_role(r):
                        await asyncio.sleep(reward.get("duration", 0))
                        try:
                            await member.remove_roles(r)
                        except Forbidden as error:
                            add_bot_error_entry(guild.id, None, member, f"level temp role remove: {r.name}", error)
                    bot.loop.create_task(remove_temp_role(role))

            if reward.get("xp", 0) > 0:
                await add_xp(bot, member, guild, reward["xp"], announce_channel=announce_channel)

        guild_config = levels[guild_id]["config"]
        if guild_config.get("level_up_message_enabled", False) and announce_channel is not None:
            try:
                await announce_channel.send(
                    f"{format_user_reference(member)} just reached **Level {current_level}**!"
                )
            except Forbidden as error:
                add_bot_error_entry(guild.id, announce_channel.id, member, "level up message", error)
            except Exception:
                pass

        channel_id = levels[guild_id]["config"].get("channel_id")
        target_channel = guild.get_channel(int(channel_id)) if channel_id else None
        
        if target_channel:
            card_bytes = await create_levelup_card(member, current_level)
            if card_bytes:
                file = File(fp=card_bytes, filename="levelup.png")
                try:
                    await target_channel.send(
                        content=f"{format_user_reference(member)}, you just reached **Level {current_level}**!",
                        file=file
                    )
                except Forbidden as error:
                    add_bot_error_entry(guild.id, target_channel.id, member, "level banner", error)

async def create_levelup_card(member: Member, level: int):
    base_path = os.path.dirname(__file__)
    bg_path = os.path.join(base_path, "levelup_bg.png")
    font_path = os.path.join(base_path, "Minecraft.ttf")
    
    if not os.path.exists(bg_path):
        return None
        
    background = Image.open(bg_path).convert("RGBA")
    avatar_bytes = await member.display_avatar.with_format("png").read()
    
    bg_width = background.width
    center_x = bg_width // 2

    with Image.open(io.BytesIO(avatar_bytes)) as avatar:
        avatar = avatar.convert("RGBA").resize((120, 120))
        background.paste(avatar, (center_x - 60, 40))
        
    draw = ImageDraw.Draw(background)
    try:
        font = ImageFont.truetype(font_path, 25)
    except Exception:
        font = ImageFont.load_default()
        
    draw.text((center_x, 190), f"{format_banner_username(get_banner_name(member))} you are now Level {level}!", fill="white", font=font, anchor="mm")
    
    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer