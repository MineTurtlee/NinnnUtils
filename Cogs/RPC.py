from main import RPC_CLIENT_ID, local_rpc_queue, local_rpc, local_rpc_thread, local_rpc_stop_event
from discord.ext.commands import Cog
from discord import Status
from discord.ext.tasks import loop
from dotenv import load_dotenv
import asyncio, time, queue, threading, os
from pypresence import Presence
from pypresence.types import ActivityType
from discord import ActivityType as at, Activity, Streaming

async def setup(bot):
    await bot.add_cog(RPC(bot))

class RPC(Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def start_local_rpc_worker(self):
        global local_rpc_thread
        if not RPC_CLIENT_ID:
            return
        if local_rpc_thread is not None and local_rpc_thread.is_alive():
            return
        local_rpc_thread = None

        def worker():
            global local_rpc, local_rpc_thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = None
            start_timestamp = time.time()

            try:
                client = Presence(RPC_CLIENT_ID, loop=loop)
                client.connect()
                local_rpc = client

                while not local_rpc_stop_event.is_set():
                    try:
                        activity_text = local_rpc_queue.get(timeout=1)
                    except queue.Empty:
                        continue

                    if activity_text is None:
                        break

                    try:
                        client.update(activity_type=ActivityType.WATCHING, 
                                    name=f"{self.bot.user}",
                                    state=activity_text, 
                                    details=f"Running {self.bot.user.name} bot",
                                    start=start_timestamp,
                                    buttons=[{"label": "Git", "url": "https://github.com/ImNinnn/NinnnUtils"},{"label": "Support Server", "url": "https://discord.gg/FSBPvc9zqY"}]
                        )
                    except Exception as e:
                        print(f"<:warning:1517452174991556758> Local RPC sync failed: {e}")
                        break
            except Exception as e:
                print(f"<:warning:1517452174991556758> Local RPC sync failed: {e}")
            finally:
                try:
                    if client is not None:
                        client.close()
                except Exception:
                    pass
                local_rpc = None
                local_rpc_thread = None
                loop.close()

        local_rpc_stop_event.clear()
        local_rpc_thread = threading.Thread(target=worker, name="LocalRPC", daemon=True)
        local_rpc_thread.start()


    def sync_local_rpc(self, activity_text: str):
        if not RPC_CLIENT_ID:
            return

        self.start_local_rpc_worker()

        try:
            while not local_rpc_queue.empty():
                local_rpc_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            local_rpc_queue.put_nowait(activity_text)
        except queue.Full:
            pass


    def close_local_rpc(self):
        global local_rpc_thread

        local_rpc_stop_event.set()
        try:
            while not local_rpc_queue.empty():
                local_rpc_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            local_rpc_queue.put_nowait(None)
        except queue.Full:
            pass

        if local_rpc_thread is not None:
            local_rpc_thread.join(timeout=5)
            local_rpc_thread = None


    @loop(seconds=15)
    async def update_presence(self):
        global presence_toggle, presence_index

        load_dotenv(override=True)
        raw_blacklist = os.getenv('SERVER_BLACKLIST', '')
        BLACKLISTED_GUILDS = [int(sid.strip()) for sid in raw_blacklist.split(',') if sid.strip().isdigit()]

        for guild in self.bot.guilds:
            if guild.id in BLACKLISTED_GUILDS:
                print(f"<:prohibited:1517497579582132436> Loop Check: Found blacklisted guild: {guild.name} ({guild.id}). Leaving...")
                try:
                    await guild.leave()
                except Exception as e:
                    print(f"<:disapprove:1517452151012589662> Failed to leave {guild.name}: {e}")

        load_dotenv(override=True)
        VERSION = os.getenv('BOT_VERSION')
        VERSION_ALTERNATE = os.getenv('BOT_VERSION_ALTERNATE')
        ACTIVITY_TEXT = os.getenv('ACTIVITY')

        # cycle between three presence messages
        online_users = sum(
            len([m for m in guild.members if m.status != Status.offline and not m.bot])
            for guild in self.bot.guilds
        )

        if presence_index == 0:
            activity_text = f"ver{VERSION} ┃ {online_users} online users"
        elif presence_index == 1:
            activity_text = f"ver{VERSION} ┃ {ACTIVITY_TEXT}"
        else:
            activity_text = f"ver{VERSION} ┃ alt{VERSION_ALTERNATE}"

        activity = Activity(type=at.watching, name=activity_text)

        for shard_id, shard in self.bot.shards.items():
            await self.bot.change_presence(
                activity=activity,
                status=Status.online,
                shard_id=shard_id,
            )

        self.sync_local_rpc(activity_text)

        presence_index = (presence_index + 1) % 3


    @update_presence.before_loop
    async def before_update_presence(self):
        await self.bot.wait_until_ready()
        self.sync_local_rpc("App just started... .. .")
        startup_activity = Streaming(
            name="App just started... .. .",
            url="https://www.twitch.tv/imninnn"
        )
        for shard_id in self.bot.shards:
            await self.bot.change_presence(activity=startup_activity, shard_id=shard_id)
        await asyncio.sleep(30)

    async def cog_load(self):
        await self.bot.wait_until_ready()
        if not self.update_presence.is_running():
            self.update_presence.start()