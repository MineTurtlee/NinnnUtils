from main import BLACKLISTED_GUILDS

async def blacklist_startup_cleanup(bot):
    await bot.wait_until_ready()
    print("Running startup blacklist check...")
    print('-------------------------------------')
    for guild in bot.guilds:
        if guild.id in BLACKLISTED_GUILDS:
            print(f"Found blacklisted guild on startup: {guild.name} ({guild.id}). Leaving...")
            try:
                await guild.leave()
            except Exception as e:
                print(f"Failed to leave {guild.name}: {e}")