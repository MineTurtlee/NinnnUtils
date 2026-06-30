from discord.ext.commands import Cog, hybrid_group, has_permissions, Context
from discord import app_commands, Embed, Color, Member
from Shared.Data import *
from Shared.User import *
from Shared.Guild import *
from Views.Shop import ShopView
import random

async def setup(bot):
    await bot.add_cog(Economy())

class Economy(Cog):
    @hybrid_group(name="eco", description="Economy commands", invoke_without_command=True)
    async def e(self, ctx): pass

    @e.command(name="leaderboard", description="Show the server economy leaderboard")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def eco_leaderboard(self, ctx: Context, limit: int = 10):
        if limit <= 0:
            return await ctx.send("<:disapprove:1517452151012589662> Limit must be greater than 0.", ephemeral=True)

        data = load_data()
        guild = get_guild_data(data, str(ctx.guild.id))
        users = guild.get("users", {})
        if not users:
            return await ctx.send("No economy data for this server.", ephemeral=True)

        leaderboard = []
        for uid, udata in users.items():
            balance = udata.get("balance", 0)
            leaderboard.append((uid, balance))

        leaderboard.sort(key=lambda x: x[1], reverse=True)
        top = leaderboard[:limit]

        description_lines = []
        for idx, (uid, bal) in enumerate(top, start=1):
            try:
                member = await ctx.guild.fetch_member(int(uid))
                name = member.display_name
            except Exception:
                name = f"User left server (`{uid}`)"
            description_lines.append(f"`#{idx}` **{name}** - ${bal}")

        embed = Embed(title=f"<:chalice:1517579767573123092> Economy Standings Leaderboard - {ctx.guild.name}", color=Color.gold())
        embed.description = "\n".join(description_lines)
        await ctx.send(embed=embed)


    @e.group(name="balance", description="Check your balance (or another user's if owner)")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.describe(user="The user you want to check (Owner only)")
    async def eco_balance(self, ctx: Context, user: Member = None):
        if user and ctx.user.id != ctx.guild.owner_id:
            return await ctx.send("<:disapprove:1517452151012589662> Only the server owner can check other users' balances!", ephemeral=True)
        target = user or ctx.author
        data = load_data()
        money = data.get(str(ctx.guild.id), {}).get("users", {}).get(str(target.id), {}).get("balance", 0)
        await ctx.send(f"<:money:1517580310395486239> {target.display_name}'s balance: **${money}**")


    @e.command(name="daily", description="Claim your daily reward")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.checks.cooldown(1, 86400, key=lambda i: (i.user.id, i.guild.id))
    async def eco_daily(self, ctx: Context):
        data = load_data()
        user_data = get_user_data(data, str(ctx.guild.id), str(ctx.user.id))
        earnings = random.randint(150, 200)
        user_data["balance"] += earnings
        save_data(data)
        await ctx.send(f"<:money:1517580310395486239> You claimed your daily reward and earned **${earnings}**!")


    @e.command(name="pay", description="Pay another user from your balance")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def eco_pay(self, ctx: Context, user: Member, amount: int):
        if amount <= 0:
            return await ctx.send("<:disapprove:1517452151012589662> Amount must be greater than 0.", ephemeral=True)
        data = load_data()
        guild_id = str(ctx.guild.id)
        sender_data = get_user_data(data, guild_id, str(ctx.user.id))
        receiver_data = get_user_data(data, guild_id, str(user.id))
        if sender_data["balance"] < amount:
            return await ctx.send("<:disapprove:1517452151012589662> You don't have enough money!", ephemeral=True)
        sender_data["balance"] -= amount
        receiver_data["balance"] += amount
        save_data(data)
        await ctx.send(f"<:approve:1517452125687513158> Successfully sent **${amount}** to {format_user_reference(user)}!")


    @e.group(name="shop", description="View the server shop")
    @app_commands.allowed_installs(guilds=True, users=False)
    async def eco_shop(self, ctx: Context):
        data = load_data()
        shop_items = data.get(str(ctx.guild.id), {}).get("shop", {})
        if not shop_items:
            await ctx.send("The shop is currently empty!")
            return
        embed = Embed(title="<:chalice:1517579767573123092> Server Shop", color=Color.gold())
        embed.description = "Click a button below to purchase an item! \n ~~───────────────────────────~~"
        for item, info in shop_items.items():
            embed.add_field(name=f"{item} - ${info['price']}", value=info['desc'], inline=False)
        await ctx.send(embed=embed, view=ShopView(shop_items, str(ctx.guild.id)))


    @eco_shop.command(name="add", description="Add an item to the shop")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def eco_shop_add(self, ctx: Context, name: str, desc: str, price: int):
        name = normalize_item(name)
        data = load_data()
        guild = get_guild_data(data, str(ctx.guild.id))
        guild["shop"][name] = {"desc": desc, "price": price}
        save_data(data)
        await ctx.send(f"<:approve:1517452125687513158> Added **{name}** to the shop!")


    @eco_shop.command(name="del", description="Remove an item from the shop")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def eco_shop_del(self, ctx: Context, name: str):
        data = load_data()
        guild = get_guild_data(data, str(ctx.guild.id))
        canonical = find_item_key(guild["shop"], name)
        if canonical:
            del guild["shop"][canonical]
            save_data(data)
            await ctx.send(f"<:approve:1517452125687513158> Removed **{canonical}** from the shop.")
        else:
            await ctx.send(f"<:disapprove:1517452151012589662> **{name}** was not found in the shop.", ephemeral=True)


    @e.group(name="inventory", description="Check your inventory (or another user's if owner)")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.describe(user="The user you want to check (Owner only)")
    async def eco_inventory(self, ctx: Context, user: Member = None):
        if user and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("<:disapprove:1517452151012589662> Only the server owner can check others' inventories.", ephemeral=True)
        target = user or ctx.send
        data = load_data()
        user_data = get_user_data(data, str(ctx.guild.id), str(target.id))
        inv = user_data.get("inventory", {})
        embed = Embed(title=f"<:box:1517581439552585759> {target.display_name}'s Inventory", color=Color.green())
        if not inv:
            embed.description = "This inventory is currently empty."
        else:
            embed.description = "\n".join(f"• {item} ×{count}" for item, count in inv.items())
        await ctx.send(embed=embed)


    @eco_inventory.command(name="edit", description="Edit a user's inventory (Owner Only)")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    @has_permissions(manage_guild=True)
    async def eco_inventory_edit(self, ctx: Context, user: Member, item: str, action: str, amount: int = 1):
        item = normalize_item(item)
        action = action.lower().strip()
        if action not in ("add", "remove"):
            return await ctx.send("<:disapprove:1517452151012589662> Action must be **add** or **remove**.", ephemeral=True)
        data = load_data()
        user_data = get_user_data(data, str(ctx.guild.id), str(user.id))
        if action == "add":
            inventory_add(user_data["inventory"], item, amount)
        else:
            removed = inventory_remove(user_data["inventory"], item, amount)
            if removed < amount:
                save_data(data)
                return await ctx.send(
                    f"<:warning:1517452174991556758> Only removed **{removed}x {item}** - {user.display_name} didn't have enough.", ephemeral=True
                )
        save_data(data)
        direction = "to" if action == "add" else "from"
        await ctx.send(f"<:approve:1517452125687513158> {action.capitalize()}d **{amount}x {item}** {direction} {user.display_name}'s inventory.")


    @eco_balance.command(name="edit", description="Set a user's balance (Owner Only)")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.default_permissions(manage_guild=True)
    async def eco_balance_edit(self, ctx: Context, user: Member, amount: int):
        data = load_data()
        user_data = get_user_data(data, str(ctx.guild.id), str(user.id))
        user_data["balance"] = amount
        save_data(data)
        await ctx.send(f"<:approve:1517452125687513158> Set {user.display_name}'s balance to **${amount}**.")
