import asyncio
import os
import random
from datetime import datetime, timedelta
import discord
from discord import TextInput, app_commands, Status
from discord.ext import commands
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import base64
import queue
import threading
import traceback
from discord.ui import Modal, TextInput
from pypresence import Presence
from pypresence.types import ActivityType

from Shared.Guild import *
from Shared.Data import *
from Shared.User import *
from Shared.Leveling import *
from Shared.Lock import *
from Shared.Boards import *

# --
# the additional #es will be for ImNinnn
# -- 

# -------------------------------------------------------------------------------------------------------------
#                                               Configuration
# -------------------------------------------------------------------------------------------------------------

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
VERSION = os.getenv('BOT_VERSION')
VERSION_ALTERNATE = os.getenv('BOT_VERSION_ALTERNATE')
RPC_CLIENT_ID = os.getenv('DISCORD_RPC_CLIENT_ID', '').strip()
raw_blacklist = os.getenv('SERVER_BLACKLIST', '')
BLACKLISTED_GUILDS = [int(sid.strip()) for sid in raw_blacklist.split(',') if sid.strip().isdigit()]
ACTIVITY_TEXT = os.getenv('ACTIVITY')
SHARD_COUNT = int(os.getenv('SHARD_COUNT', '0'))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'economy.json')
LOVE_FILE = os.path.join(BASE_DIR, 'love.json')
FUN_FILE = os.path.join(BASE_DIR, 'fun.json')
BOARD_FILE = os.path.join(BASE_DIR, 'board.json')
GUILD_FILE = os.path.join(BASE_DIR, 'guild.json')
LOCK_CONFIG_FILE = os.path.join(BASE_DIR, 'lock_config.json')
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")
LEVEL_FILE = os.path.join(BASE_DIR, 'level.json')
USER_FILE = os.path.join(BASE_DIR, 'user.json')

# -------------------------------------------------------------------------------------------------------------
#                                               Bot Setup
# -------------------------------------------------------------------------------------------------------------

class NinnnUtils(commands.AutoShardedBot):
    def __init__(self, intents, shard_count: int = 0):
        super().__init__(
            command_prefix="/", # or just implement a command handler to return if you don't want prefixed commands
            intents=intents,
            shard_count=shard_count or None,
        )


    async def setup_hook(self):
        shard_info = (
            f"{self.shard_count} shard(s)" if self.shard_count else "auto sharding"
        )
        print(f"[Sharding] Running with {shard_info}")
        await self.tree.sync()
        print("Slash commands synced!")

    async def on_ready(self):
        for cog in os.listdir("./Cogs"):
            if cog.endswith(".py"):
                try: await self.load_extension(f"Cogs.{cog[:-3]}")
                except Exception as e: print(f"[{cog[:-3]}] An error occurred trying to load: {e}")

    async def on_shard_ready(self, shard_id: int):
        print(f"[Shard {shard_id}] Ready")

    async def on_shard_connect(self, shard_id: int):
        print(f"[Shard {shard_id}] Connected")

    async def on_shard_disconnect(self, shard_id: int):
        print(f"[Shard {shard_id}] Disconnected")

    async def on_shard_resumed(self, shard_id: int):
        print(f"[Shard {shard_id}] Resumed")

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# -------------------------------------------------------------------------------------------------------------
#                                               Message Cache
# -------------------------------------------------------------------------------------------------------------

message_cache = []
deleted_cache = []
edited_cache = []
bot_error_cache = []
active_minigame_users = set()
server_pauses = {}
all_paused_guilds = set()
reaction_xp_cooldowns = {}
local_rpc = None
local_rpc_thread = None
local_rpc_stop_event = threading.Event()
local_rpc_queue = queue.Queue(maxsize=1)

# -------------------------------------------------------------------------------------------------------------
#                                               Data Management
# -------------------------------------------------------------------------------------------------------------

locked_channels, admin_log_channels = load_lock_config()
# See Shared for all data management functions

# -------------------------------------------------------------------------------------------------------------
#                                               UI Views
# -------------------------------------------------------------------------------------------------------------

# See Views for all views

# -------------------------------------------------------------------------------------------------------------
#                                               Events
# -------------------------------------------------------------------------------------------------------------

# See Events.py

# -------------------------------------------------------------------------------------------------------------
#                                               Error Handling
# -------------------------------------------------------------------------------------------------------------

# See Events.py or Shared/Errors.py

# -------------------------------------------------------------------------------------------------------------
#                                               Presence Update Loop
# -------------------------------------------------------------------------------------------------------------

presence_index = 0
# See RPC.py (Cogs)

# -------------------------------------------------------------------------------------------------------------
#                                               Blacklist Handling
# -------------------------------------------------------------------------------------------------------------

# Events.py for new joins, Shared/Blacklist.py for start blacklist

# -------------------------------------------------------------------------------------------------------------
#                                               User Level Commands
# -------------------------------------------------------------------------------------------------------------

# They're now in Leveling.py

# -------------------------------------------------------------------------------------------------------------
#                                               Admin Commands
# -------------------------------------------------------------------------------------------------------------

# See Admin.py

# -------------------------------------------------------------------------------------------------------------
#                                               Deleted Edited / Ghost Pings / Error
# -------------------------------------------------------------------------------------------------------------

# See Ghosts.py

# -------------------------------------------------------------------------------------------------------------
#                                               Counter And Reply Commands
# -------------------------------------------------------------------------------------------------------------

# See Responses.py

# -------------------------------------------------------------------------------------------------------------
#                                               Board Commands
# -------------------------------------------------------------------------------------------------------------

# Middle Joke: are you French? because Eiffel 4 u <3

# -------------------------------------------------------------------------------------------------------------
#                                               Lock Commands
# -------------------------------------------------------------------------------------------------------------

# See Locks.py

# -------------------------------------------------------------------------------------------------------------
#                                               Welcome/Goodbye Commands
# -------------------------------------------------------------------------------------------------------------

# See Welcomer.py

# -------------------------------------------------------------------------------------------------------------
#                                               Economy Commands
# -------------------------------------------------------------------------------------------------------------




@bot.tree.command(name="eco-leaderboard", description="Show the server economy leaderboard")
@app_commands.allowed_installs(guilds=True, users=False)
async def eco_leaderboard(interaction: discord.Interaction, limit: int = 10):
    if limit <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Limit must be greater than 0.", ephemeral=True)

    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    users = guild.get("users", {})
    if not users:
        return await interaction.response.send_message("No economy data for this server.", ephemeral=True)

    leaderboard = []
    for uid, udata in users.items():
        balance = udata.get("balance", 0)
        leaderboard.append((uid, balance))

    leaderboard.sort(key=lambda x: x[1], reverse=True)
    top = leaderboard[:limit]

    description_lines = []
    for idx, (uid, bal) in enumerate(top, start=1):
        try:
            member = await interaction.guild.fetch_member(int(uid))
            name = member.display_name
        except Exception:
            name = f"User left server (`{uid}`)"
        description_lines.append(f"`#{idx}` **{name}** - ${bal}")

    embed = discord.Embed(title=f"<:chalice:1517579767573123092> Economy Standings Leaderboard - {interaction.guild.name}", color=discord.Color.gold())
    embed.description = "\n".join(description_lines)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="eco-balance", description="Check your balance (or another user's if owner)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.describe(user="The user you want to check (Owner only)")
async def eco_balance(interaction: discord.Interaction, user: discord.Member = None):
    if user and interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Only the server owner can check other users' balances!", ephemeral=True)
    target = user or interaction.user
    data = load_data()
    money = data.get(str(interaction.guild.id), {}).get("users", {}).get(str(target.id), {}).get("balance", 0)
    await interaction.response.send_message(f"<:money:1517580310395486239> {target.display_name}'s balance: **${money}**")


@bot.tree.command(name="eco-daily", description="Claim your daily reward")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.cooldown(1, 86400, key=lambda i: (i.user.id, i.guild.id))
async def eco_daily(interaction: discord.Interaction):
    data = load_data()
    user_data = get_user_data(data, str(interaction.guild.id), str(interaction.user.id))
    earnings = random.randint(150, 200)
    user_data["balance"] += earnings
    save_data(data)
    await interaction.response.send_message(f"<:money:1517580310395486239> You claimed your daily reward and earned **${earnings}**!")


@bot.tree.command(name="eco-pay", description="Pay another user from your balance")
@app_commands.allowed_installs(guilds=True, users=False)
async def eco_pay(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Amount must be greater than 0.", ephemeral=True)
    data = load_data()
    guild_id = str(interaction.guild.id)
    sender_data = get_user_data(data, guild_id, str(interaction.user.id))
    receiver_data = get_user_data(data, guild_id, str(user.id))
    if sender_data["balance"] < amount:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You don't have enough money!", ephemeral=True)
    sender_data["balance"] -= amount
    receiver_data["balance"] += amount
    save_data(data)
    await interaction.response.send_message(f"<:approve:1517452125687513158> Successfully sent **${amount}** to {format_user_reference(user)}!")


@bot.tree.command(name="eco-shop", description="View the server shop")
@app_commands.allowed_installs(guilds=True, users=False)
async def eco_shop(interaction: discord.Interaction):
    data = load_data()
    shop_items = data.get(str(interaction.guild.id), {}).get("shop", {})
    if not shop_items:
        await interaction.response.send_message("The shop is currently empty!")
        return
    embed = discord.Embed(title="<:chalice:1517579767573123092> Server Shop", color=discord.Color.gold())
    embed.description = "Click a button below to purchase an item! \n ~~───────────────────────────~~"
    for item, info in shop_items.items():
        embed.add_field(name=f"{item} - ${info['price']}", value=info['desc'], inline=False)
    await interaction.response.send_message(embed=embed, view=ShopView(shop_items, str(interaction.guild.id)))


@bot.tree.command(name="eco-shop-add", description="Add an item to the shop")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_shop_add(interaction: discord.Interaction, name: str, desc: str, price: int):
    name = normalize_item(name)
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    guild["shop"][name] = {"desc": desc, "price": price}
    save_data(data)
    await interaction.response.send_message(f"<:approve:1517452125687513158> Added **{name}** to the shop!")


@bot.tree.command(name="eco-shop-del", description="Remove an item from the shop")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_shop_del(interaction: discord.Interaction, name: str):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    canonical = find_item_key(guild["shop"], name)
    if canonical:
        del guild["shop"][canonical]
        save_data(data)
        await interaction.response.send_message(f"<:approve:1517452125687513158> Removed **{canonical}** from the shop.")
    else:
        await interaction.response.send_message(f"<:disapprove:1517452151012589662> **{name}** was not found in the shop.", ephemeral=True)


@bot.tree.command(name="eco-inventory", description="Check your inventory (or another user's if owner)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.describe(user="The user you want to check (Owner only)")
async def eco_inventory(interaction: discord.Interaction, user: discord.Member = None):
    if user and interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Only the server owner can check others' inventories.", ephemeral=True)
    target = user or interaction.user
    data = load_data()
    user_data = get_user_data(data, str(interaction.guild.id), str(target.id))
    inv = user_data.get("inventory", {})
    embed = discord.Embed(title=f"<:box:1517581439552585759> {target.display_name}'s Inventory", color=discord.Color.green())
    if not inv:
        embed.description = "This inventory is currently empty."
    else:
        embed.description = "\n".join(f"• {item} ×{count}" for item, count in inv.items())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="eco-inventory-edit", description="Edit a user's inventory (Owner Only)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_inventory_edit(interaction: discord.Interaction, user: discord.Member, item: str, action: str, amount: int = 1):
    item = normalize_item(item)
    action = action.lower().strip()
    if action not in ("add", "remove"):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Action must be **add** or **remove**.", ephemeral=True)
    data = load_data()
    user_data = get_user_data(data, str(interaction.guild.id), str(user.id))
    if action == "add":
        inventory_add(user_data["inventory"], item, amount)
    else:
        removed = inventory_remove(user_data["inventory"], item, amount)
        if removed < amount:
            save_data(data)
            return await interaction.response.send_message(
                f"<:warning:1517452174991556758> Only removed **{removed}x {item}** - {user.display_name} didn't have enough.", ephemeral=True
            )
    save_data(data)
    direction = "to" if action == "add" else "from"
    await interaction.response.send_message(f"<:approve:1517452125687513158> {action.capitalize()}d **{amount}x {item}** {direction} {user.display_name}'s inventory.")


@bot.tree.command(name="eco-balance-edit", description="Set a user's balance (Owner Only)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_balance_edit(interaction: discord.Interaction, user: discord.Member, amount: int):
    data = load_data()
    user_data = get_user_data(data, str(interaction.guild.id), str(user.id))
    user_data["balance"] = amount
    save_data(data)
    await interaction.response.send_message(f"<:approve:1517452125687513158> Set {user.display_name}'s balance to **${amount}**.")




# -------------------------------------------------------------------------------------------------------------
#                                               Minigames
# -------------------------------------------------------------------------------------------------------------




@bot.tree.command(name="game-slot", description="Play the economy slot machine and wager money")
@app_commands.allowed_installs(guilds=True, users=False)
async def game_slot(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Bet amount must be greater than 0.", ephemeral=True)

    data = load_data()
    guild_id = str(interaction.guild.id)
    user_data = get_user_data(data, guild_id, str(interaction.user.id))
    before_balance = user_data["balance"]

    if before_balance < amount:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You don't have enough money to place that bet.", ephemeral=True)

    emojis = ['🍒', '🍎', '🍇', '💎', '🔔', '🍋']
    e1, e2, e3 = (random.choice(emojis) for _ in range(3))

    if e1 == e2 == e3:
        user_data["balance"] += amount*10
        result_text = f"<:chalice:1517579767573123092> **JACKPOT!** You won **${amount*10}**!"
        color = discord.Color.green()
    else:
        user_data["balance"] -= amount
        result_text = f"<:money:1517580310395486239> You lost **${amount}**. Better luck next time!"
        color = discord.Color.red()

    save_data(data)

    embed = discord.Embed(title="<:777:1518352060574208031> Economy Slot Machine", description=f"Bet: **${amount}**", color=color)
    embed.add_field(name="Result", value=f"| {e1} | {e2} | {e3} |", inline=False)
    embed.add_field(name="Outcome", value=result_text, inline=False)
    embed.set_footer(text=f"Before: ${before_balance} • After: ${user_data['balance']}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="game-coinflip", description="Play coinflip and wager money")
@app_commands.allowed_installs(guilds=True, users=False)
async def game_coinflip(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Bet amount must be greater than 0.", ephemeral=True)

    data = load_data()
    guild_id = str(interaction.guild.id)
    user_data = get_user_data(data, guild_id, str(interaction.user.id))
    before_balance = user_data["balance"]

    if before_balance < amount:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You don't have enough money to place that bet.", ephemeral=True)

    result = random.choice(["heads", "tails"])
    if result == "heads":
        user_data["balance"] += amount
        result_text = f"<:chalice:1517579767573123092> You won **${amount}**! The coin landed on **Heads**."
        color = discord.Color.green()
    else:
        user_data["balance"] -= amount
        result_text = f"<:money:1517580310395486239> You lost **${amount}**. The coin landed on **Tails**."
        color = discord.Color.red()

    save_data(data)

    embed = discord.Embed(title="<:coin:1518351100783231138> Coin Flip", description=f"Bet: **${amount}**", color=color)
    embed.add_field(name="Result", value=result_text, inline=False)
    embed.set_footer(text=f"Before: ${before_balance} • After: ${user_data['balance']}")
    await interaction.response.send_message(embed=embed)


class MinesButton(discord.ui.Button):
    def __init__(self, index: int, row: int, col: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="❓", row=row)
        self.index = index
        self.row_index = row
        self.col_index = col

    async def callback(self, interaction: discord.Interaction):
        view: MinesGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)
        view.action_taken = True
        if self.index in view.mine_positions:
            self.style = discord.ButtonStyle.danger
            self.label = "<:explosive:1517578642723573880>"
            self.disabled = True
            view.reveal_board()
            view.finished = True
            view.disable_all_items()
            active_minigame_users.discard(view.user_id)
            data = load_data()
            user_data = get_user_data(data, view.guild_id, view.user_id)
            after_balance = user_data["balance"]
            view.embed.title = "💥 Minesweeper - Lost"
            view.embed.description = (
                f"You hit a mine and lost your wager of **${view.amount}**.\n"
                f"Safe tiles found: **{len(view.revealed_positions)}/{view.total_safe}**"
            )
            view.embed.set_footer(text=f"Before: ${view.before_balance} • After: ${after_balance}")
            await interaction.response.edit_message(embed=view.embed, view=view)
            return

        self.disabled = True
        self.style = discord.ButtonStyle.success
        view.revealed_positions.add(self.index)
        adjacent = view.adjacent_mine_count(self.index)
        self.label = str(adjacent) if adjacent > 0 else "0"
        view.update_embed()
        if len(view.revealed_positions) >= view.total_safe:
            await view.finish_game(interaction)
            return
        await interaction.response.edit_message(embed=view.embed, view=view)


class MinesCashoutButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Cash Out", row=4)

    async def callback(self, interaction: discord.Interaction):
        view: MinesGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)
        if not view.action_taken:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> You must reveal at least one tile before cashing out.", ephemeral=True)

        payout = view.calculate_payout()
        data = load_data()
        user_data = get_user_data(data, view.guild_id, view.user_id)
        user_data["balance"] += payout
        save_data(data)
        active_minigame_users.discard(view.user_id)
        view.finished = True
        view.disable_all_items()
        view.embed.title = "<:money:1517580310395486239> Minesweeper - Cash Out"
        view.embed.description = (
            f"You cashed out with **${payout}**.\n"
            f"Safe tiles found: **{len(view.revealed_positions)}/{view.total_safe}**"
        )
        view.embed.set_footer(text=f"Before: ${view.before_balance} • After: ${user_data['balance']}")
        await interaction.response.edit_message(embed=view.embed, view=view)

class MinesGameView(discord.ui.View):
    def __init__(self, amount: int, mines: int, guild_id: str, user_id: int, before_balance: int):
        super().__init__(timeout=180)
        self.amount = amount
        self.mines = mines
        self.guild_id = guild_id
        self.user_id = user_id
        self.before_balance = before_balance
        self.finished = False
        self.action_taken = False
        self.revealed_positions = set()
        self.total_cells = 20
        self.total_safe = self.total_cells - self.mines
        self.mine_positions = set(random.sample(range(self.total_cells), self.mines))
        self.initial_revealed_index = None
        self.embed = discord.Embed(
            title="<:explosive:1517578642723573880> Minesweeper Gamble",
            description="",
            color=discord.Color.red(),
        )
        for row in range(5):
            for col in range(4):
                index = row * 4 + col
                button = MinesButton(index=index, row=row, col=col)
                self.add_item(button)
        self.add_item(MinesCashoutButton())
        self.message = None
        self.reveal_initial_tile()
        self.update_embed()

    def player_safe_count(self) -> int:
        return len(self.revealed_positions) - (1 if self.initial_revealed_index is not None else 0)

    def calculate_payout(self) -> int:
        multiplier = 1 + self.mines * 0.01
        payout = self.amount * (multiplier ** self.player_safe_count())
        return int(round(payout))

    def adjacent_mine_count(self, index: int) -> int:
        row = index // 4
        col = index % 4
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = row + dr
                nc = col + dc
                if 0 <= nr < 5 and 0 <= nc < 4:
                    if nr * 4 + nc in self.mine_positions:
                        count += 1
        return count

    def update_embed(self):
        safe_count = len(self.revealed_positions)
        payout = self.calculate_payout()
        self.embed.title = "<:explosive:1517578642723573880> Minesweeper Gamble"
        self.embed.description = (
            f"Bet: **${self.amount}**\n"
            f"Mines: **{self.mines}**\n"
            f"Safe tiles found: **{safe_count}/{self.total_safe}**\n"
            f"Cash out value: **${payout}**\n"
            f"Click any tile, or cash out at any time."
        )
        self.embed.set_footer(text=f"Before: ${self.before_balance}")

    def reveal_board(self):
        for item in self.children:
            if isinstance(item, MinesButton):
                if item.index in self.mine_positions:
                    item.disabled = True
                    item.style = discord.ButtonStyle.danger
                    item.label = "<:explosive:1517578642723573880>"
                else:
                    item.disabled = True

    def reveal_initial_tile(self):
        safe_positions = [i for i in range(self.total_cells) if i not in self.mine_positions]
        if not safe_positions:
            return
        initial_index = random.choice(safe_positions)
        self.initial_revealed_index = initial_index
        self.revealed_positions.add(initial_index)

        for item in self.children:
            if isinstance(item, MinesButton) and item.index == initial_index:
                item.disabled = True
                item.style = discord.ButtonStyle.primary
                adjacent = self.adjacent_mine_count(item.index)
                item.label = str(adjacent) if adjacent > 0 else "0"
                break

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    async def finish_game(self, interaction: discord.Interaction):
        payout = self.calculate_payout()
        data = load_data()
        user_data = get_user_data(data, self.guild_id, self.user_id)
        user_data["balance"] += payout
        save_data(data)
        active_minigame_users.discard(self.user_id)
        self.finished = True
        self.disable_all_items()
        self.embed.title = "<:chalice:1517579767573123092> Minesweeper - Victory"
        self.embed.description = (
            f"You safely revealed all non-mine tiles and won **${payout}**!\n"
            f"Safe tiles found: **{len(self.revealed_positions)}/{self.total_safe}**"
        )
        self.embed.set_footer(text=f"Before: ${self.before_balance} • After: ${user_data['balance']}")
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.finished:
            return
        active_minigame_users.discard(self.user_id)
        self.finished = True
        self.disable_all_items()
        self.reveal_board()
        if self.message:
            self.embed.title = "<:hourglass:1517574046252924938> Minesweeper - Timed Out"
            self.embed.description = (
                f"Time expired and your wager of **${self.amount}** was lost.\n"
                f"Safe tiles found: **{len(self.revealed_positions)}/{self.total_safe}**"
            )
            self.embed.set_footer(text=f"Before: ${self.before_balance}")
            try:
                await self.message.edit(embed=self.embed, view=self)
            except Exception:
                pass


@bot.tree.command(name="game-mines", description="Play minesweeper and wager money")
@app_commands.allowed_installs(guilds=True, users=False)
async def game_mines(interaction: discord.Interaction, amount: int, mines: int):
    if amount <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Bet amount must be greater than 0.", ephemeral=True)
    if mines < 3 or mines > 10:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Number of mines must be between 3 and 10.", ephemeral=True)

    data = load_data()
    guild_id = str(interaction.guild.id)
    user_data = get_user_data(data, guild_id, str(interaction.user.id))
    before_balance = user_data["balance"]

    if interaction.user.id in active_minigame_users:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You already have an active minigame. Finish or wait for it to time out before starting another.", ephemeral=True)

    if before_balance < amount:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You don't have enough money to place that bet.", ephemeral=True)

    user_data["balance"] -= amount
    save_data(data)
    view = MinesGameView(amount=amount, mines=mines, guild_id=guild_id, user_id=interaction.user.id, before_balance=before_balance)
    active_minigame_users.add(interaction.user.id)
    await interaction.response.send_message(embed=view.embed, view=view)
    view.message = await interaction.original_response()


class TowerButton(discord.ui.Button):
    def __init__(self, row: int, col: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="❓", row=row)
        self.row_index = row
        self.col_index = col

    async def callback(self, interaction: discord.Interaction):
        view: TowersGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)
        if self.row_index != view.current_row:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> You must click a button in the current row first.", ephemeral=True)

        view.action_taken = True
        if self.col_index in view.correct_positions[self.row_index]:
            self.style = discord.ButtonStyle.success
            self.disabled = True
            view.reveal_row(self.row_index)
            view.current_row -= 1
            view.update_embed()
            if view.current_row < 0:
                await view.finish_game(interaction)
                return
            view.update_row_buttons()
            await interaction.response.edit_message(embed=view.embed, view=view)
        else:
            self.style = discord.ButtonStyle.danger
            view.reveal_row(self.row_index)
            view.finished = True
            active_minigame_users.discard(view.user_id)
            view.disable_all_items()
            data = load_data()
            user_data = get_user_data(data, view.guild_id, view.user_id)
            after_balance = user_data["balance"]
            view.embed.title = "<:tower:1518350397008252958> Tower Gamble - Lost"
            view.embed.description = (
                f"You chose the wrong button and lost your wager of **${view.amount}**.\n"
                f"Rows cleared: {view.rows_cleared()}/5"
            )
            view.embed.set_footer(text=f"Before: ${view.before_balance} • After: ${after_balance}")
            await interaction.response.edit_message(embed=view.embed, view=view)


class CashoutButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Cash Out", row=0)

    async def callback(self, interaction: discord.Interaction):
        view: TowersGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)
        if not view.action_taken:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> You must pick at least one tile before cashing out.", ephemeral=True)

        payout = view.calculate_payout(view.rows_cleared())
        data = load_data()
        user_data = get_user_data(data, view.guild_id, view.user_id)
        user_data["balance"] += payout
        save_data(data)
        after_balance = user_data["balance"]
        active_minigame_users.discard(view.user_id)
        view.finished = True
        view.disable_all_items()
        view.embed.title = "<:money:1517580310395486239> Tower Gamble - Cash Out"
        view.embed.description = (
            f"You cashed out with **${payout}**.\n"
            f"Rows cleared: {view.rows_cleared()}/5"
        )
        view.embed.set_footer(text=f"Before: ${view.before_balance} • After: ${after_balance}")
        await interaction.response.edit_message(embed=view.embed, view=view)


class TowersGameView(discord.ui.View):
    def __init__(self, amount: int, guild_id: str, user_id: int, before_balance: int):
        super().__init__(timeout=180)
        self.amount = amount
        self.guild_id = guild_id
        self.user_id = user_id
        self.before_balance = before_balance
        self.finished = False
        self.action_taken = False
        self.current_row = 4
        self.correct_positions = [set(random.sample(range(3), 2)) for _ in range(5)]
        self.embed = discord.Embed(
            title="<:tower:1518350397008252958> Tower Gamble",
            description="",
            color=discord.Color.red(),
        )
        self.update_embed()
        for row in range(5):
            for col in range(3):
                button = TowerButton(row=row, col=col)
                button.disabled = row != self.current_row
                self.add_item(button)
        self.add_item(CashoutButton())
        self.message = None

    def rows_cleared(self) -> int:
        return max(0, 4 - self.current_row)

    def calculate_payout(self, completed_rows: int) -> int:
        return int(round(self.amount * (1.07 ** completed_rows)))

    def update_embed(self):
        completed = self.rows_cleared()
        potential = self.calculate_payout(completed)
        next_row = 5 - self.current_row
        self.embed.title = "<:tower:1518350397008252958> Tower Gamble"
        self.embed.description = (
            f"Bet: **${self.amount}**\n"
            f"Rows cleared: **{completed}/5**\n"
            f"Current cash out value: **${potential}**\n"
            f"Click a button in row **{next_row}** below, or cash out at any time."
        )
        self.embed.set_footer(text=f"Before: ${self.before_balance}")

    def update_row_buttons(self):
        for item in self.children:
            if isinstance(item, TowerButton):
                if item.row_index == self.current_row:
                    item.disabled = False
                    item.style = discord.ButtonStyle.secondary
                else:
                    item.disabled = True

    def reveal_row(self, row_index: int):
        for item in self.children:
            if isinstance(item, TowerButton) and item.row_index == row_index:
                item.disabled = True
                if item.col_index in self.correct_positions[row_index]:
                    item.style = discord.ButtonStyle.success
                else:
                    item.style = discord.ButtonStyle.danger

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    async def finish_game(self, interaction: discord.Interaction):
        payout = self.calculate_payout(5)
        data = load_data()
        user_data = get_user_data(data, self.guild_id, self.user_id)
        user_data["balance"] += payout
        save_data(data)
        active_minigame_users.discard(self.user_id)
        self.finished = True
        self.disable_all_items()
        self.embed.title = "<:chalice:1517579767573123092> Tower Gamble - Victory"
        self.embed.description = (
            f"You reached the top and won **${payout}**!\n"
            f"Rows cleared: **5/5**"
        )
        self.embed.set_footer(text=f"Before: ${self.before_balance} • After: ${user_data['balance']}")
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.finished:
            return
        active_minigame_users.discard(self.user_id)
        self.finished = True
        self.disable_all_items()
        if self.message:
            data = load_data()
            user_data = get_user_data(data, self.guild_id, self.user_id)
            after_balance = user_data["balance"]
            self.embed.title = "<:hourglass:1517574046252924938> Tower Gamble - Timed Out"
            self.embed.description = (
                f"Time expired and your wager of **${self.amount}** was lost.\n"
                f"Rows cleared: **{self.rows_cleared()}/5**"
            )
            self.embed.set_footer(text=f"Before: ${self.before_balance} • After: ${after_balance}")
            try:
                await self.message.edit(embed=self.embed, view=self)
            except Exception:
                pass


@bot.tree.command(name="game-towers", description="Play tower gamble and wager money")
@app_commands.allowed_installs(guilds=True, users=False)
async def game_towers(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Bet amount must be greater than 0.", ephemeral=True)

    data = load_data()
    guild_id = str(interaction.guild.id)
    user_data = get_user_data(data, guild_id, str(interaction.user.id))
    before_balance = user_data["balance"]

    if interaction.user.id in active_minigame_users:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You already have an active minigame. Finish or wait for it to time out before starting another.", ephemeral=True)

    if before_balance < amount:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You don't have enough money to place that bet.", ephemeral=True)

    user_data["balance"] -= amount
    save_data(data)
    view = TowersGameView(amount=amount, guild_id=guild_id, user_id=interaction.user.id, before_balance=before_balance)
    active_minigame_users.add(interaction.user.id)
    await interaction.response.send_message(embed=view.embed, view=view)
    view.message = await interaction.original_response()

class DeveloperCodeSelect(discord.ui.Select):
    def __init__(self, correct_index: int):
        self.correct_index = correct_index
        options = [discord.SelectOption(label=f"Code {i+1}", value=str(i)) for i in range(10)]
        super().__init__(placeholder="Choose the different code...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        view: WorkGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)

        selected_index = int(self.values[0])
        
        if selected_index == self.correct_index:
            view.finished = True
            view.disable_all_items()
            payout = get_work_payout(view.difficulty)
            data = load_data()
            user_data = get_user_data(data, view.guild_id, view.user_id)
            user_data["balance"] += payout
            save_data(data)
            view.embed.title = "<:list:1517497572770451567> Developer Job - Success!"
            view.embed.description = f"You found the odd code string and earned **${payout}**!"
            await interaction.response.edit_message(embed=view.embed, view=view)
        else:
            view.finished = True
            view.disable_all_items()
            view.embed.title = "<:list:1517497572770451567> Developer Job - Failed!"
            view.embed.description = "That's not the odd code! You didn't earn anything this time."
            await interaction.response.edit_message(embed=view.embed, view=view)


class DeveloperCodeButton(discord.ui.Button):
    def __init__(self, index: int, code: str, is_odd: bool, row: int):
        super().__init__(style=discord.ButtonStyle.secondary, label=code, row=row)
        self.index = index
        self.code = code
        self.is_odd = is_odd

    async def callback(self, interaction: discord.Interaction):
        view: WorkGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)

        if self.is_odd:
            view.finished = True
            view.disable_all_items()
            payout = get_work_payout(view.difficulty)
            data = load_data()
            user_data = get_user_data(data, view.guild_id, view.user_id)
            user_data["balance"] += payout
            save_data(data)
            view.embed.title = "<:list:1517497572770451567> Developer Job - Success!"
            view.embed.description = f"You found the odd code string and earned **${payout}**!"
            await interaction.response.edit_message(embed=view.embed, view=view)
        else:
            self.disabled = True
            self.style = discord.ButtonStyle.danger
            view.finished = True
            view.disable_all_items()
            view.embed.title = "<:list:1517497572770451567> Developer Job - Failed!"
            view.embed.description = "That's not the odd code! You didn't earn anything this time."
            await interaction.response.edit_message(embed=view.embed, view=view)


class FarmerCropButton(discord.ui.Button):
    def __init__(self, index: int, crop: str, is_target: bool, is_dirt: bool, row: int, col: int):
        super().__init__(style=discord.ButtonStyle.secondary, label=crop, row=row)
        self.index = index
        self.crop = crop
        self.is_target = is_target
        self.is_dirt = is_dirt
        self.col_index = col

    async def callback(self, interaction: discord.Interaction):
        view: WorkGameView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
        if view.finished:
            return await interaction.response.send_message("<:disapprove:1517452151012589662> This game has already ended.", ephemeral=True)

        if self.is_dirt:
            self.disabled = True
            await interaction.response.defer()
            return

        if self.is_target:
            view.correct_crops_clicked.add(self.index)
            self.disabled = True
            self.style = discord.ButtonStyle.success
            if len(view.correct_crops_clicked) == len(view.target_crop_indices):
                view.finished = True
                view.disable_all_items()
                payout = get_work_payout(view.difficulty)
                data = load_data()
                user_data = get_user_data(data, view.guild_id, view.user_id)
                user_data["balance"] += payout
                save_data(data)
                view.embed.title = "🌱 Farmer Job - Success!"
                view.embed.description = f"You collected all the correct crops and earned **${payout}**!"
                await interaction.response.edit_message(embed=view.embed, view=view)
            else:
                await interaction.response.defer()
        else:
            self.disabled = True
            self.style = discord.ButtonStyle.danger
            view.finished = True
            view.disable_all_items()
            view.embed.title = "🌱 Farmer Job - Failed!"
            view.embed.description = "You clicked the wrong crop! You didn't earn anything this time."
            await interaction.response.edit_message(embed=view.embed, view=view)


class WorkGameView(discord.ui.View):
    def __init__(self, job_type: str, guild_id: str, user_id: int, amount: int, difficulty: str = "normal"):
        difficulty_settings = WORK_DIFFICULTY_SETTINGS.get(difficulty, WORK_DIFFICULTY_SETTINGS["normal"])
        super().__init__(timeout=difficulty_settings["timeout"])
        self.job_type = job_type
        self.guild_id = guild_id
        self.user_id = user_id
        self.amount = amount
        self.difficulty = difficulty if difficulty in WORK_DIFFICULTY_SETTINGS else "normal"
        self.timeout_seconds = difficulty_settings["timeout"]
        self.developer_button_count = difficulty_settings["developer_buttons"]
        self.farmer_target_count = difficulty_settings["farmer_targets"]
        self.math_operations = difficulty_settings["math_operations"]
        self.finished = False
        self.correct_crops_clicked = set()
        self.target_crop_indices = set()
        self.embed = discord.Embed(color=discord.Color.blue())
        self.message = None

        if job_type == "developer":
            self.setup_developer_job()
        elif job_type == "farmer":
            self.setup_farmer_job()
        elif job_type == "math":
            self.setup_math_job()

    def setup_developer_job(self):
        code_string = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=6))
        code_options = [code_string] * (self.developer_button_count - 1)
        odd_code = self.mutate_string(code_string)
        code_options.append(odd_code)
        random.shuffle(code_options)
        
        self.embed.title = "<:list:1517497572770451567> Developer Job"
        self.embed.description = (
            f"Find the code string that is different from the others!\n"
            f"<:timer:1517996239583576194> **{self.timeout_seconds} seconds left**"
        )
        
        odd_index = code_options.index(odd_code)
        for i, code in enumerate(code_options):
            is_odd = (i == odd_index)
            button = DeveloperCodeButton(i, code, is_odd, row=i // 5)
            self.add_item(button)

    def setup_farmer_job(self):
        crops = ["🥕", "🥬", "🌾", "🫛", "🥔"]
        target_crop = random.choice(crops)
        wrong_crops = random.sample([c for c in crops if c != target_crop], 2)

        target_positions = set(random.sample(range(8), self.farmer_target_count))
        wrong_positions = set(random.sample([i for i in range(8) if i not in target_positions], 2))
        self.target_crop_indices = target_positions

        self.embed.title = "🌱 Farmer Job"
        self.embed.description = (
            f"Collect all **{len(target_positions)}** {target_crop} crops from the farm!\n"
            f"Click the right crops and avoid the others.\n"
            f"<:timer:1517996239583576194> **{self.timeout_seconds} seconds left**"
        )

        for i in range(8):
            row = i // 4
            col = i % 4
            if i in target_positions:
                button = FarmerCropButton(i, target_crop, True, False, row, col)
            elif i in wrong_positions:
                wrong_crop = wrong_crops.pop()
                button = FarmerCropButton(i, wrong_crop, False, False, row, col)
            else:
                button = FarmerCropButton(i, "🟫", False, True, row, col)
            self.add_item(button)

    def setup_math_job(self):
        self.embed.title = "<:plus:1518348756570079262> Math Teacher Job"
        self.embed.description = f"Solve the equation!\n<:timer:1517996239583576194> **{self.timeout_seconds} seconds left**"
        
        operation = random.choice(self.math_operations)
        if operation == "/":
            num2 = random.randint(2, 12)
            self.correct_answer = random.randint(2, 12)
            num1 = num2 * self.correct_answer
        else:
            num1 = random.randint(10, 99)
            num2 = random.randint(1, 50)
        
        if operation == "+":
            self.correct_answer = num1 + num2
        elif operation == "-":
            self.correct_answer = num1 - num2
        elif operation == "*":
            self.correct_answer = num1 * num2
        else:
            self.correct_answer = num1 // num2
        
        self.equation = f"{num1} {operation} {num2} = ?"
        self.embed.description = f"**{self.equation}**\n<:timer:1517996239583576194> **{self.timeout_seconds} seconds left**"
        
        answer_input = discord.ui.TextInput(
            label="Your Answer",
            placeholder="Enter the answer",
            min_length=1,
            max_length=10,
        )
    
        class MathAnswerModal(discord.ui.Modal):
            def __init__(self, view: "WorkGameView"):
                super().__init__(title="Answer")
                self.add_item(answer_input)
                self.view = view
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                if modal_interaction.user.id != self.view.user_id:
                    return await modal_interaction.response.send_message("<:multi:1518348755261460661> This is not for you.", ephemeral=True)
                if self.view.finished:
                    return await modal_interaction.response.send_message("<:disapprove:1517452151012589662> Game already finished.", ephemeral=True)
                
                try:
                    user_answer = int(answer_input.value)
                    if user_answer == self.view.correct_answer:
                        self.view.finished = True
                        self.view.disable_all_items()
                        payout = get_work_payout(self.view.difficulty)
                        data = load_data()
                        user_data = get_user_data(data, self.view.guild_id, self.view.user_id)
                        user_data["balance"] += payout
                        save_data(data)
                        self.view.embed.title = "<:multi:1518348755261460661> Math Teacher Job - Success!"
                        self.view.embed.description = f"Correct! The answer is **{self.view.correct_answer}**. You earned **${payout}**!"
                        await modal_interaction.response.defer()
                        await self.view.message.edit(embed=self.view.embed, view=self.view)
                    else:
                        self.view.finished = True
                        self.view.disable_all_items()
                        self.view.embed.title = "<:minus:1518348754111959150> Math Teacher Job - Failed!"
                        self.view.embed.description = f"Wrong! The correct answer is **{self.view.correct_answer}**. You didn't earn anything this time."
                        await modal_interaction.response.defer()
                        await self.view.message.edit(embed=self.view.embed, view=self.view)
                except ValueError:
                    await modal_interaction.response.send_message("<:disapprove:1517452151012589662> Please enter a valid number.", ephemeral=True)
        
        submit_button = discord.ui.Button(label="Submit Answer", style=discord.ButtonStyle.primary)
        
        async def submit_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("<:disapprove:1517452151012589662> This game is not for you.", ephemeral=True)
            await interaction.response.send_modal(MathAnswerModal(self))
        
        submit_button.callback = submit_callback
        self.add_item(submit_button)

    def mutate_string(self, s: str) -> str:
        chars = list(s)
        pos = random.randint(0, len(chars) - 1)
        pool = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        pool = pool.replace(chars[pos], "")
        chars[pos] = random.choice(pool)
        return "".join(chars)

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        if self.finished:
            return
        self.finished = True
        self.disable_all_items()
        if self.message:
            self.embed.title = "<:timer:1517996239583576194> Work - Timed Out"
            self.embed.description = "Time expired! You didn't earn anything this time."
            try:
                await self.message.edit(embed=self.embed, view=self)
            except Exception:
                pass


work_cooldowns = {}

WORK_DIFFICULTY_SETTINGS = {
    "easy": {
        "timeout": 30,
        "developer_buttons": 8,
        "farmer_targets": 2,
        "math_operations": ["+", "-"],
        "payout_range": (200, 300),
    },
    "normal": {
        "timeout": 25,
        "developer_buttons": 10,
        "farmer_targets": 3,
        "math_operations": ["*", "-"],
        "payout_range": (450, 550),
    },
    "hard": {
        "timeout": 20,
        "developer_buttons": 12,
        "farmer_targets": 4,
        "math_operations": ["*", "/"],
        "payout_range": (700, 800),
    },
}


def get_work_payout(difficulty: str) -> int:
    settings = WORK_DIFFICULTY_SETTINGS.get(difficulty, WORK_DIFFICULTY_SETTINGS["normal"])
    low, high = settings["payout_range"]
    return random.randint(low, high)


@bot.tree.command(name="game-work", description="Work to earn money (get 1 of 3 random jobs, 2 hour cooldown)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.describe(difficulty="Choose the work difficulty")
@app_commands.choices(
    difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Normal", value="normal"),
        app_commands.Choice(name="Hard", value="hard"),
    ]
)
async def game_work(interaction: discord.Interaction, difficulty: str = "normal"):
    difficulty = difficulty.lower().strip()
    if difficulty not in WORK_DIFFICULTY_SETTINGS:
        difficulty = "normal"

    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    cooldown_key = f"{guild_id}_{user_id}"
    
    now = datetime.now()
    if cooldown_key in work_cooldowns:
        last_use = work_cooldowns[cooldown_key]
        elapsed = (now - last_use).total_seconds()
        remaining = 7200 - elapsed
        
        if remaining > 0:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            return await interaction.response.send_message(
                f"<:timer:1517996239583576194> You can work again in **{minutes}m {seconds}s**.",
                ephemeral=True
            )
    
    data = load_data()
    user_data = get_user_data(data, guild_id, user_id)
    
    job_type = random.choice(["developer", "farmer", "math"])
    amount = 0
    
    work_cooldowns[cooldown_key] = now
    
    view = WorkGameView(job_type, guild_id, interaction.user.id, amount, difficulty)
    await interaction.response.send_message(embed=view.embed, view=view)
    view.message = await interaction.original_response()




# -------------------------------------------------------------------------------------------------------------
#                                               Crafting Commands
# -------------------------------------------------------------------------------------------------------------




@bot.tree.command(name="eco-craft-add", description="Add a recipe (Owner Only)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_craft_add(interaction: discord.Interaction, item: str, req1_name: str, req1_count: int, req2_name: str = None, req2_count: int = 0, delay: int = 0):
    item = normalize_item(item)
    req1_name = normalize_item(req1_name)
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    recipe = {"reqs": {req1_name: req1_count}, "delay": delay}
    if req2_name:
        recipe["reqs"][normalize_item(req2_name)] = req2_count
    guild["recipes"][item] = recipe
    save_data(data)
    await interaction.response.send_message(f"<:approve:1517452125687513158> Added recipe: **{item}** (Time: {delay}s).")


@bot.tree.command(name="eco-craft", description="Craft an item")
@app_commands.allowed_installs(guilds=True, users=False)
async def eco_craft(interaction: discord.Interaction, item: str, amount: int = 1):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    user_data = get_user_data(data, str(interaction.guild.id), str(interaction.user.id))
    canonical_item = find_item_key(guild["recipes"], item)
    if not canonical_item:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> This item is not craftable.", ephemeral=True)
    recipe = guild["recipes"][canonical_item]
    delay = recipe.get("delay", 0)
    for req_item, count in recipe["reqs"].items():
        if inventory_count(user_data["inventory"], req_item) < (count * amount):
            return await interaction.response.send_message(f"<:disapprove:1517452151012589662> You don't have enough **{req_item}**.", ephemeral=True)
    await interaction.response.send_message(f"🔨 Starting to craft {amount}x **{canonical_item}**... (Wait {delay}s)")
    if delay > 0:
        await asyncio.sleep(delay)
        data = load_data()
        guild = get_guild_data(data, str(interaction.guild.id))
        user_data = get_user_data(data, str(interaction.guild.id), str(interaction.user.id))
        for req_item, count in recipe["reqs"].items():
            if inventory_count(user_data["inventory"], req_item) < (count * amount):
                return await interaction.followup.send("<:disapprove:1517452151012589662> Crafting failed: You spent your ingredients while waiting!", ephemeral=True)
    for req_item, count in recipe["reqs"].items():
        inventory_remove(user_data["inventory"], req_item, count * amount)
    inventory_add(user_data["inventory"], canonical_item, amount)
    save_data(data)
    await interaction.followup.send(f"<:approve:1517452125687513158> Finished crafting {amount}x **{canonical_item}**!")


@bot.tree.command(name="eco-craft-del", description="Remove a recipe (Owner Only)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_craft_del(interaction: discord.Interaction, item: str):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    canonical = find_item_key(guild["recipes"], item)
    if canonical:
        del guild["recipes"][canonical]
        save_data(data)
        await interaction.response.send_message(f"<:trash:1517497581058527404> Removed recipe for **{canonical}**.")
    else:
        await interaction.response.send_message(f"<:disapprove:1517452151012589662> No recipe found for **{item}**.", ephemeral=True)


@bot.tree.command(name="eco-use-add", description="Add usage effect (including giving an item or XP)")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
@app_commands.describe(
    item="The item whose use effect you want to define",
    money="Money reward granted when the item is used",
    xp="XP reward granted when the item is used",
    message="Custom response message after using the item",
    role="Role to grant when the item is used",
    temp_role="Temporary role to grant when the item is used",
    duration="Length of the temporary role in seconds",
    delay="Delay before the use effect completes",
    instant_message="Message to send immediately before delay",
    give_item="Optional item to grant when used",
    give_item_amount="Quantity of the granted item"
)
async def eco_use_add(interaction: discord.Interaction, item: str, money: int = 0, xp: int = 0, message: str = "Used item!", role: discord.Role = None, temp_role: discord.Role = None, duration: int = 0, delay: int = 0, instant_message: str = None, give_item: str = None, give_item_amount: int = 1):
    item = normalize_item(item)
    if give_item:
        give_item = normalize_item(give_item)

    if role:
        if interaction.user.top_role <= role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> You cannot configure an item to grant a role that is equal or higher than your highest role.",
                ephemeral=True
            )
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> I cannot assign that role because it is equal or higher than my highest role.",
                ephemeral=True
            )

    if temp_role:
        if interaction.user.top_role <= temp_role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> You cannot configure an item to grant a temporary role that is equal or higher than your highest role.",
                ephemeral=True
            )
        if interaction.guild.me.top_role <= temp_role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> I cannot assign that temporary role because it is equal or higher than my highest role.",
                ephemeral=True
            )

    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    guild["item_uses"][item] = {
        "money": money,
        "xp": xp,
        "message": message,
        "role_id": role.id if role else None,
        "temp_role_id": temp_role.id if temp_role else None,
        "duration": duration,
        "delay": delay,
        "instant_message": instant_message,
        "give_item": give_item,
        "give_item_amount": give_item_amount
    }
    save_data(data)
    await interaction.response.send_message(
        f"<:approve:1517452125687513158> Effect registered for **{item}**. (Gives: {give_item_amount}x {give_item if give_item else 'None'})"
    )


@bot.tree.command(name="eco-use", description="Use an item from your inventory")
@app_commands.allowed_installs(guilds=True, users=False)
async def eco_use(interaction: discord.Interaction, item: str, number_of_times: int = 1):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    user_data = get_user_data(data, str(interaction.guild.id), str(interaction.user.id))
    if inventory_count(user_data["inventory"], item) < number_of_times:
        return await interaction.response.send_message(f"<:disapprove:1517452151012589662> You need **{number_of_times}x** of this item to do that.", ephemeral=True)
    canonical_item = find_item_key(guild["item_uses"], item)
    if not canonical_item:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> This item has no special use effect.", ephemeral=True)
    effect = guild["item_uses"][canonical_item]
    if number_of_times > 1 and (effect.get("role_id") or effect.get("temp_role_id")):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You cannot use role-giving items multiple times at once.", ephemeral=True)
    if effect.get("instant_message"):
        await interaction.response.send_message(effect["instant_message"])
    else:
        await interaction.response.defer()
    if effect.get("delay", 0) > 0:
        await asyncio.sleep(effect["delay"])
    total_money = 0
    reward_items_given = []
    total_xp = 0
    for _ in range(number_of_times):
        inventory_remove(user_data["inventory"], item)
        total_money += effect.get("money", 0)
        total_xp += effect.get("xp", 0)
        if effect.get("give_item"):
            reward_name = effect["give_item"]
            reward_amount = effect.get("give_item_amount", 1)
            inventory_add(user_data["inventory"], reward_name, reward_amount)
            reward_items_given.append(reward_name)
        if number_of_times == 1:
            if effect.get("role_id"):
                role = interaction.guild.get_role(effect["role_id"])
                if role and interaction.guild.me.top_role > role:
                    try:
                        await interaction.user.add_roles(role)
                    except discord.Forbidden as error:
                        add_bot_error_entry(interaction.guild.id, interaction.channel_id, interaction.user, "item use role grant", error)
            if effect.get("temp_role_id"):
                role = interaction.guild.get_role(effect["temp_role_id"])
                if role and interaction.guild.me.top_role > role:
                    try:
                        await interaction.user.add_roles(role)
                    except discord.Forbidden as error:
                        add_bot_error_entry(interaction.guild.id, interaction.channel_id, interaction.user, "item use temp role grant", error)
                        continue
                    async def remove_role(r):
                            await asyncio.sleep(effect["duration"])
                            try:
                                await interaction.user.remove_roles(r)
                            except discord.Forbidden as error:
                                add_bot_error_entry(interaction.guild.id, interaction.channel_id, interaction.user, "item use temp role remove", error)
                    bot.loop.create_task(remove_role(role))
    user_data["balance"] += total_money
    save_data(data)
    if total_xp > 0:
        await add_xp(interaction.user, interaction.guild, total_xp, announce_channel=interaction.channel)
    final_msg = f"<:spark:1517583248421552305> [{number_of_times}x] {effect['message']}"
    if total_money > 0:
        final_msg += f" (Reward: ${total_money})"
    if total_xp > 0:
        final_msg += f" (+{total_xp} XP)"
    if reward_items_given:
        final_msg += f" (Received: {reward_items_given[0]}!)"
    if interaction.response.is_done():
        await interaction.followup.send(final_msg)
    else:
        await interaction.response.send_message(final_msg)


@bot.tree.command(name="eco-use-del", description="Remove usage effect")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_use_del(interaction: discord.Interaction, item: str):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    canonical = find_item_key(guild["item_uses"], item)
    if canonical:
        del guild["item_uses"][canonical]
        save_data(data)
        await interaction.response.send_message(f"<:trash:1517497581058527404> Removed usage effect for **{canonical}**.")
    else:
        await interaction.response.send_message(f"<:disapprove:1517452151012589662> No usage effect found for **{item}**.", ephemeral=True)


@bot.tree.command(name="eco-value-set", description="Set the selling price for an item")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_value_set(interaction: discord.Interaction, item: str, value: int):
    item = normalize_item(item)
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    guild["item_values"][item] = value
    save_data(data)
    await interaction.response.send_message(f"<:approve:1517452125687513158> Users can now sell **{item}** for **${value}**.")


@bot.tree.command(name="eco-value-del", description="Remove the selling price for an item")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.default_permissions(manage_guild=True)
async def eco_value_del(interaction: discord.Interaction, item: str):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    canonical = find_item_key(guild["item_values"], item)
    if canonical:
        del guild["item_values"][canonical]
        save_data(data)
        await interaction.response.send_message(f"<:approve:1517452125687513158> Removed selling price for **{canonical}**. It can no longer be sold.")
    else:
        await interaction.response.send_message(f"<:disapprove:1517452151012589662> **{item}** doesn't have a price set.", ephemeral=True)


@bot.tree.command(name="eco-sell", description="Sell a specific amount of an item from your inventory")
@app_commands.allowed_installs(guilds=True, users=False)
async def eco_sell(interaction: discord.Interaction, item: str, amount: int = 1):
    if amount <= 0:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You must sell at least 1 item.", ephemeral=True)
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    user_data = get_user_data(data, str(interaction.guild.id), str(interaction.user.id))
    canonical_item = find_item_key(guild.get("item_values", {}), item)
    if canonical_item is None:
        return await interaction.response.send_message(f"<:disapprove:1517452151012589662> **{item}** cannot be sold. No price has been set for it.", ephemeral=True)
    item_price = guild["item_values"][canonical_item]
    user_count = inventory_count(user_data["inventory"], canonical_item)
    if user_count < amount:
        return await interaction.response.send_message(
            f"<:disapprove:1517452151012589662> You don't have enough! You have **{user_count}x {canonical_item}**, but tried to sell **{amount}x**.", ephemeral=True
        )
    inventory_remove(user_data["inventory"], canonical_item, amount)
    total_value = item_price * amount
    user_data["balance"] += total_value
    save_data(data)
    await interaction.response.send_message(
        f"<:money:1517580310395486239> You sold **{amount}x {canonical_item}** for a total of **${total_value}**!\n"
        f"Your new balance is **${user_data['balance']}**."
    )


@bot.tree.command(name="info-values", description="Show all items that can be sold and their prices")
@app_commands.allowed_installs(guilds=True, users=False)
async def info_values(interaction: discord.Interaction):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    prices = guild.get("item_values", {})
    if not prices:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> No items have a selling price set yet.", ephemeral=True)

    embed = discord.Embed(title="<:money:1517580310395486239> Item Market Prices", color=discord.Color.gold())
    for item, price in prices.items():
        embed.add_field(name=item, value=f"Sell Price: **${price}**", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="info-recipes", description="Show all available crafting recipes")
@app_commands.allowed_installs(guilds=True, users=False)
async def info_recipes(interaction: discord.Interaction):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    recipes = guild.get("recipes", {})
    if not recipes:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> No crafting recipes found.", ephemeral=True)

    embed = discord.Embed(title="<:craft:1518348021161660539> Crafting Book", color=discord.Color.blue())
    for result_item, recipe in recipes.items():
        ing_list = ", ".join(f"{amt}x {name}" for name, amt in recipe["reqs"].items())
        delay_str = f"<:timer:1517996239583576194> {recipe.get('delay', 0)}s" if recipe.get("delay", 0) > 0 else ""
        embed.add_field(name=result_item, value=f"Requires: {ing_list}{(' \n' + delay_str) if delay_str else ''}", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="info-uses", description="Show what items do when used")
@app_commands.allowed_installs(guilds=True, users=False)
async def info_uses(interaction: discord.Interaction):
    data = load_data()
    guild = get_guild_data(data, str(interaction.guild.id))
    uses = guild.get("item_uses", {})
    if not uses:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> No item effects have been set up.", ephemeral=True)

    embed = discord.Embed(title="<:Vial:1517681553377857628> Item Effects Directory", color=discord.Color.green())
    for item, effect in uses.items():
        details = []
        money = effect.get("money", 0)
        if money > 0:
            details.append(f"<:money:1517580310395486239> Gives Money: **${money}**")
        xp_amount = effect.get("xp", 0)
        if xp_amount > 0:
            details.append(f"<:Vial:1517681553377857628> Grants XP: **{xp_amount} XP**")
        give_item = effect.get("give_item")
        if give_item:
            amt = effect.get("give_item_amount", 1)
            details.append(f"<:box:1517581439552585759> Gives: **{amt}x {give_item}**")
        if effect.get("role_id"):
            role = interaction.guild.get_role(effect["role_id"])
            if role:
                details.append(f"<:shield:1518340640801427566> Grants Role: **{role.name}**")
        if effect.get("temp_role_id"):
            role = interaction.guild.get_role(effect["temp_role_id"])
            dur = effect.get("duration", 0)
            if role:
                details.append(f"<:hourglass:1517574046252924938> Temp Role: **{role.name}** ({dur}s)")
        delay = effect.get("delay", 0)
        if delay > 0:
            details.append(f"<:timer:1517996239583576194> Delay: {delay}s")
        msg = effect.get("message")
        if msg and msg != "Used item!":
            details.append(f"<:list:1517497572770451567> Message: *{msg}*")
        if details:
            embed.add_field(name=item, value="\n".join(details), inline=False)

    if not embed.fields:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> No item effects have been set up.", ephemeral=True)

    await interaction.response.send_message(embed=embed)




# -------------------------------------------------------------------------------------------------------------
#                                               Leveling System
# -------------------------------------------------------------------------------------------------------------










@bot.tree.command(name="lvl-leaderboard", description="Display the top 10 highest-level users in this guild")
@app_commands.allowed_installs(guilds=True, users=False)
async def level_leaderboard(interaction: discord.Interaction):
    levels = load_levels()
    g_id = str(interaction.guild_id)
    
    users_dict = levels.get(g_id, {}).get("users", {})
    if not users_dict:
        return await interaction.response.send_message("📭 No active XP statistics logged in this server yet.", ephemeral=True)
        
    sorted_users = sorted(users_dict.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
    
    embed = discord.Embed(title=f"<:graph:1517584522877866065> Level Standings Leaderboard - {interaction.guild.name}", color=discord.Color.gold())
    
    description_text = ""
    for index, (u_id, data) in enumerate(sorted_users[:10], start=1):
        member = interaction.guild.get_member(int(u_id))
        name_str = member.display_name if member else f"User left server (`{u_id}`)"
        description_text += f"`#{index}` **{name_str}** - Lvl {data['level']} ({data['xp']} XP)\n"
        
    embed.description = description_text
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="lvl-edit", description="(Admin) Manually adjust or set a target user's level and XP indexes")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.has_permissions(manage_guild=True)
async def lvl_edit(interaction: discord.Interaction, user: discord.Member, level: int, xp: int = 0):
    levels = load_levels()
    g_id, u_id = str(interaction.guild_id), str(user.id)
    
    if g_id not in levels: levels[g_id] = {"config": {}, "users": {}}
    
    levels[g_id]["users"][u_id] = {
        "xp": max(0, xp),
        "level": max(0, level),
        "color": levels[g_id]["users"].get(u_id, {}).get("color", "white")
    }
    save_levels(levels)
    await interaction.response.send_message(f"<:gear:1517576939097952496> Action complete. Set {format_user_reference(user)} to **Level {level}** with **{xp} XP**.", ephemeral=True)


@bot.tree.command(name="lvl-channel-set", description="(Admin) Route level-up image logs into a designated text stream")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.has_permissions(manage_guild=True)
async def lvl_channel_set(interaction: discord.Interaction, channel: discord.TextChannel):
    levels = load_levels()
    g_id = str(interaction.guild_id)
    
    if g_id not in levels: levels[g_id] = {"config": {}, "users": {}}
    
    levels[g_id]["config"]["channel_id"] = channel.id
    save_levels(levels)
    await interaction.response.send_message(f"<:bell:1517497562184024275> Destination updated! Level-up notifications will now send to {channel.mention}.")


@bot.tree.command(name="lvl-channel-remove", description="(Admin) Disable level-up notification image cards from sending")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.has_permissions(manage_guild=True)
async def lvl_channel_remove(interaction: discord.Interaction):
    levels = load_levels()
    g_id = str(interaction.guild_id)
    
    if g_id not in levels or "config" not in levels[g_id] or levels[g_id]["config"].get("channel_id") is None:
        return await interaction.response.send_message(
            "<:disapprove:1517452151012589662> There is no level-up notification channel configured for this server currently.", 
            ephemeral=True
        )
    
    levels[g_id]["config"]["channel_id"] = None
    save_levels(levels)
    
    await interaction.response.send_message(
        "<:trash:1517497581058527404> Configuration removed! Level-up image banners are now disabled for this server.", 
        ephemeral=True
    )


@bot.tree.command(name="toggle-lvl-up-message", description="(Admin) Enable or disable level-up chat messages")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.has_permissions(manage_guild=True)
async def toggle_lvl_up_message(interaction: discord.Interaction):
    levels = load_levels()
    g_id = str(interaction.guild_id)

    if g_id not in levels:
        levels[g_id] = {"config": {"channel_id": None, "rewards": {}, "level_up_message_enabled": False}, "users": {}}
    elif "config" not in levels[g_id]:
        levels[g_id]["config"] = {"channel_id": None, "rewards": {}, "level_up_message_enabled": False}

    current_state = levels[g_id]["config"].get("level_up_message_enabled", False)
    new_state = not current_state
    levels[g_id]["config"]["level_up_message_enabled"] = new_state
    save_levels(levels)

    status_text = "enabled" if new_state else "disabled"
    await interaction.response.send_message(
        f"📢 Level-up chat messages are now **{status_text}** for this server.",
        ephemeral=True
    )


@bot.tree.command(name="lvl-rewards-set", description="(Admin) Map an automatic reward milestone to a level")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    level="The target level milestone",
    role="Optional role to grant at this level",
    temp_role="Optional temporary role to grant at this level",
    duration="Duration for the temporary role in seconds",
    money="Optional money reward granted at this level",
    xp="Optional XP reward granted at this level",
    item="Optional item to give at this level",
    item_amount="Quantity of the item to give"
)
async def lvl_rewards_set(interaction: discord.Interaction, level: int, role: discord.Role = None, temp_role: discord.Role = None, duration: int = 0, money: int = 0, xp: int = 0, item: str = None, item_amount: int = 1):
    if not role and not temp_role and money <= 0 and xp <= 0 and not item:
        return await interaction.response.send_message(
            "<:disapprove:1517452151012589662> You must specify at least one reward: role, temp_role, money, xp, or item.",
            ephemeral=True
        )

    if role:
        if interaction.user.top_role <= role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> You cannot configure a level reward role that is equal or higher than your highest role.",
                ephemeral=True
            )
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> I cannot assign that role because it is equal or higher than my highest role.",
                ephemeral=True
            )

    if temp_role:
        if interaction.user.top_role <= temp_role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> You cannot configure a temporary role reward that is equal or higher than your highest role.",
                ephemeral=True
            )
        if interaction.guild.me.top_role <= temp_role:
            return await interaction.response.send_message(
                "<:disapprove:1517452151012589662> I cannot assign that temporary role because it is equal or higher than my highest role.",
                ephemeral=True
            )

    reward_data = {
        "role_id": role.id if role else None,
        "temp_role_id": temp_role.id if temp_role else None,
        "duration": duration,
        "money": money,
        "xp": xp,
        "give_item": normalize_item(item) if item else None,
        "give_item_amount": item_amount
    }

    levels = load_levels()
    g_id = str(interaction.guild_id)

    if g_id not in levels:
        levels[g_id] = {"config": {"channel_id": None, "rewards": {}}, "users": {}}
    if "rewards" not in levels[g_id]["config"]:
        levels[g_id]["config"]["rewards"] = {}
        
    levels[g_id]["config"]["rewards"][str(level)] = reward_data
    save_levels(levels)

    reward_parts = []
    if role:
        reward_parts.append(f"role {role.mention}")
    if temp_role:
        reward_parts.append(f"temp role {temp_role.mention} for {duration}s")
    if money > 0:
        reward_parts.append(f"${money}")
    if xp > 0:
        reward_parts.append(f"{xp} XP")
    if item:
        reward_parts.append(f"{item_amount}x {normalize_item(item)}")

    await interaction.response.send_message(
        f"<:box:1517581439552585759> Level {level} reward configured: {', '.join(reward_parts)}.", ephemeral=True
    )


def format_level_reward_summary(guild: discord.Guild, level: str, reward_data: dict) -> str:
    parts = []

    role_id = reward_data.get("role_id")
    if role_id:
        role = guild.get_role(role_id)
        parts.append(f"Role: {role.mention if role else f'`{role_id}`'}")

    temp_role_id = reward_data.get("temp_role_id")
    if temp_role_id:
        role = guild.get_role(temp_role_id)
        duration = reward_data.get("duration", 0)
        parts.append(f"Temp role: {role.mention if role else f'`{temp_role_id}`'} for `{duration}s`")

    money = reward_data.get("money", 0)
    if money > 0:
        parts.append(f"Money: `${money}`")

    xp = reward_data.get("xp", 0)
    if xp > 0:
        parts.append(f"XP: `{xp}`")

    give_item = reward_data.get("give_item")
    if give_item:
        amount = reward_data.get("give_item_amount", 1)
        parts.append(f"Item: `{amount}x {give_item}`")

    if not parts:
        return f"Level {level}: No rewards configured."

    return f"Level {level}: " + " | ".join(parts)


@bot.tree.command(name="info-lvl-rewards", description="Show the level rewards configured for this guild")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.describe(level="Optional specific level to inspect")
async def info_lvl_rewards(interaction: discord.Interaction, level: int = None):
    levels = load_levels()
    g_id = str(interaction.guild_id)
    guild_data = levels.get(g_id, {})
    rewards = guild_data.get("config", {}).get("rewards", {})

    if not rewards:
        return await interaction.response.send_message("📭 No level rewards are configured for this server yet.", ephemeral=True)

    embed = discord.Embed(
        title=f"<:box:1517581439552585759> Level Rewards - {interaction.guild.name}",
        color=discord.Color.gold()
    )

    if level is not None:
        reward_data = rewards.get(str(level))
        if not reward_data:
            return await interaction.response.send_message(f"<:disapprove:1517452151012589662> No rewards are configured for level {level} in this server.", ephemeral=True)

        embed.description = format_level_reward_summary(interaction.guild, str(level), reward_data)
    else:
        sorted_levels = sorted(rewards.items(), key=lambda item: int(item[0]))
        embed.description = "\n".join(
            format_level_reward_summary(interaction.guild, lvl, reward_data)
            for lvl, reward_data in sorted_levels
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="lvl-rewards-del", description="(Admin) Delete all rewards configured for a level")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(level="The level whose rewards should be removed")
async def lvl_rewards_del(interaction: discord.Interaction, level: int):
    levels = load_levels()
    g_id = str(interaction.guild_id)

    if g_id not in levels or "config" not in levels[g_id] or "rewards" not in levels[g_id]["config"]:
        return await interaction.response.send_message(f"<:disapprove:1517452151012589662> No rewards are configured for level {level} in this server.", ephemeral=True)

    rewards = levels[g_id]["config"]["rewards"]
    if str(level) not in rewards:
        return await interaction.response.send_message(f"<:disapprove:1517452151012589662> No rewards are configured for level {level} in this server.", ephemeral=True)

    del rewards[str(level)]
    save_levels(levels)

    await interaction.response.send_message(f"<:trash:1517497581058527404> Removed all rewards configured for level {level}.", ephemeral=True)




# -------------------------------------------------------------------------------------------------------------
#                                               Owner Commands
# -------------------------------------------------------------------------------------------------------------






@bot.tree.command(name="own-stop-urgent", description="(owner) STOPS IMMEDIATLY IF SOMETHING WENT REALLY WRONG")
@app_commands.describe(channel="Optional announcement channel to send the force shutdown message to")
async def own_stop_urgent(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Stop.", ephemeral=True)

    target_channel = channel or bot.get_channel(1514173159052415026)
    if target_channel is None and isinstance(interaction.channel, discord.TextChannel):
        target_channel = interaction.channel

    force_text = "<:warning:1517452174991556758> The bot is going offline immediately due to an urgent issue."
    force_embed = discord.Embed(
        title="Force Shutdown",
        description=force_text,
        color=discord.Color.red()
    )

    if target_channel is not None:
        try:
            sent_msg = await target_channel.send(embed=force_embed)
            if target_channel.type == discord.ChannelType.news:
                try:
                    await sent_msg.publish()
                except Exception:
                    pass
        except discord.Forbidden as error:
            add_bot_error_entry(interaction.guild.id if interaction.guild else None, target_channel.id, interaction.user, "urgent shutdown notice", error)
        except Exception:
            pass

    if update_presence.is_running():
        update_presence.cancel()
    await interaction.response.send_message("Goodbye.")
    forced_activity = discord.Activity(type=discord.ActivityType.watching, name="App was shutdown forcefully...")
    for shard_id in bot.shards:
        await bot.change_presence(activity=forced_activity, status=discord.Status.dnd, shard_id=shard_id)
    close_local_rpc()
    await bot.close()


@bot.tree.command(name="own-game-work", description="(owner) Spawn a specific work game for debugging")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.describe(
    game="Choose which work game to spawn",
    difficulty="Choose the difficulty"
)
@app_commands.choices(
    game=[
        app_commands.Choice(name="Developer", value="developer"),
        app_commands.Choice(name="Farmer", value="farmer"),
        app_commands.Choice(name="Math Teacher", value="math"),
    ],
    difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Normal", value="normal"),
        app_commands.Choice(name="Hard", value="hard"),
    ]
)
async def own_game_work(interaction: discord.Interaction, game: str, difficulty: str = "normal"):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Owner only.", ephemeral=True)

    difficulty = difficulty.lower().strip()
    if difficulty not in WORK_DIFFICULTY_SETTINGS:
        difficulty = "normal"

    job_type = game.lower().strip()
    if job_type not in {"developer", "farmer", "math"}:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Invalid work game selected.", ephemeral=True)

    view = WorkGameView(job_type, str(interaction.guild.id), interaction.user.id, 0, difficulty)
    await interaction.response.send_message(embed=view.embed, view=view)
    view.message = await interaction.original_response()


@bot.tree.command(name="own-shard-info", description="(owner) Display shard status and guild distribution")
@app_commands.allowed_installs(guilds=True, users=False)
async def shard_info(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Owner only.", ephemeral=True)

    total_shards = len(bot.shards) or 1
    embed = discord.Embed(title="Shard Information", color=discord.Color.blurple())
    embed.add_field(name="Total Shards", value=str(total_shards), inline=True)
    embed.add_field(name="Total Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Total Users", value=str(len(bot.users)), inline=True)

    for shard_id, shard in bot.shards.items():
        guilds_on_shard = [g for g in bot.guilds if g.shard_id == shard_id]
        latency_ms = round(shard.latency * 1000, 1)
        embed.add_field(
            name=f"Shard {shard_id}",
            value=f"{latency_ms}ms | {len(guilds_on_shard)} guild(s)",
            inline=False,
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="own-shard-map", description="(owner) Show which guilds are assigned to each shard")
async def shard_map(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> You are not authorized to use this command.", ephemeral=True)

    shard_map = {}
    for guild in bot.guilds:
        shard_id = getattr(guild, 'shard_id', 0)
        shard_map.setdefault(shard_id, []).append(f"> **{guild.name}** ||({guild.id})||")

    embed = discord.Embed(
        title="Shard Assignment Map",
        description="Shows which servers are served by each shard.",
        color=discord.Color.blurple()
    )
    for shard_id in sorted(shard_map.keys()):
        guild_list = shard_map[shard_id]
        value = "\n".join(guild_list)
        embed.add_field(name=f"Shard {shard_id}", value=value, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


def build_bot_emoji_pages(emojis):
    pages = []
    current_lines = []

    def flush_page():
        if current_lines:
            pages.append("\n".join(current_lines))

    current_length = 0
    for emoji in emojis:
        emoji_line = f"{str(emoji)} `<:{emoji.name}:{emoji.id}>`{' animated' if emoji.animated else ''}"

        addition = len(emoji_line) + 1
        if current_lines and current_length + addition > 3200:
            flush_page()
            current_lines.clear()
            current_length = 0

        current_lines.append(emoji_line)
        current_length += addition

    flush_page()
    return pages or ["No custom emojis available."]


class BotEmojiPaginator(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(self.pages) - 1

    def build_embed(self):
        embed = discord.Embed(
            title="Bot Emojis",
            description=self.pages[self.index],
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page {self.index + 1}/{len(self.pages)}")
        return embed

    async def show_page(self, interaction: discord.Interaction):
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        await self.show_page(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
        await self.show_page(interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


@bot.tree.command(name="own-bot-emojis", description="(owner) Display all custom emojis the bot can use")
@app_commands.allowed_installs(guilds=True, users=False)
async def own_bot_emojis(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Owner only.", ephemeral=True)

    try:
        emojis = await bot.fetch_application_emojis()
    except discord.MissingApplicationID:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> The bot does not have an application ID yet.", ephemeral=True)
    except Exception as e:
        return await interaction.response.send_message(f"<:disapprove:1517452151012589662> Could not fetch application emojis: {e}", ephemeral=True)

    emojis = sorted(emojis, key=lambda emoji: emoji.name.lower())
    if not emojis:
        return await interaction.response.send_message("<:disapprove:1517452151012589662> The application does not have any custom emojis.", ephemeral=True)

    pages = build_bot_emoji_pages(emojis)
    view = BotEmojiPaginator(pages)
    await interaction.response.send_message(embed=view.build_embed(), view=view)
    view.message = await interaction.original_response()


@bot.tree.command(name="own-test-goodbye", description="Preview the goodbye banner for a specific user")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def test_goodbye(interaction: discord.Interaction, member: discord.Member = None):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Owner only.", ephemeral=True)

    target_member = member or interaction.user
    await interaction.response.defer()
    try:
        goodbye_file = await create_goodbye_card(target_member)
        if goodbye_file:
            await interaction.followup.send(f"<:image:1517497571470348539> **Goodbye Banner Preview** for {format_user_reference(target_member)}:", file=goodbye_file)
        else:
            await interaction.followup.send("<:disapprove:1517452151012589662> Failed to generate the image. Check the console for errors.")
    except Exception as e:
        print(f"Error in test-goodbye: {e}")
        await interaction.followup.send(f"<:warning:1517452174991556758> An error occurred: {e}")


@bot.tree.command(name="own-test-welcome", description="Preview the welcome banner for a specific user")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def test_welcome(interaction: discord.Interaction, member: discord.Member = None):
    if not await bot.is_owner(interaction.user):
        return await interaction.response.send_message("<:disapprove:1517452151012589662> Owner only.", ephemeral=True)

    target_member = member or interaction.user
    await interaction.response.defer()
    try:
        welcome_file = await create_welcome_card(target_member)
        if welcome_file:
            await interaction.followup.send(f"<:image:1517497571470348539> **Welcome Banner Preview** for {format_user_reference(target_member)}:", file=welcome_file)
        else:
            await interaction.followup.send("<:disapprove:1517452151012589662> Failed to generate the image. Check the console for errors.")
    except Exception as e:
        print(f"Error in test-welcome: {e}")
        await interaction.followup.send(f"<:warning:1517452174991556758> An error occurred: {e}")




# -------------------------------------------------------------------------------------------------------------
#                                               Personalization Commands
# -------------------------------------------------------------------------------------------------------------




@bot.tree.command(name="set-color", description="Choose the block color for your /level tracking progress bar")
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.choices(color=[app_commands.Choice(name=name.title(), value=name) for name in COLOR_EMOJIS.keys() if name != "black"])
async def set_profile_color(interaction: discord.Interaction, color: str):
    settings = load_user_settings()
    user_settings = get_user_settings_entry(settings, str(interaction.user.id))
    user_settings["color"] = color
    save_user_settings(settings)

    await interaction.response.send_message(
        f"<:image:1517497571470348539> Clean style! Your profile tracking bar is now set to {COLOR_EMOJIS[color]} **{color}** across all servers.",
        ephemeral=True
    )


@bot.tree.command(name="set-getping", description="Toggle whether the bot pings you when it references you")
@app_commands.allowed_installs(guilds=True, users=False)
async def set_getping(interaction: discord.Interaction):
    settings = load_user_settings()
    user_settings = get_user_settings_entry(settings, str(interaction.user.id))
    current_state = user_settings.get("user_pings", True)
    new_state = not current_state
    user_settings["user_pings"] = new_state
    save_user_settings(settings)

    status_text = "enabled" if new_state else "disabled"
    await interaction.response.send_message(
        f"<:bell:1517497562184024275> User pings are now **{status_text}** for you.",
        ephemeral=True
    )




# -------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    bot = NinnnUtils(intents=intents, shard_count=SHARD_COUNT)
    bot.run(TOKEN)