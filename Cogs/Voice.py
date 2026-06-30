import yt_dlp, asyncio, os
from main import BASE_DIR, FFMPEG_OPTIONS, FFMPEG_PATH, YTDL_OPTIONS
from discord.ext.commands import Cog, hybrid_group, Context
from discord import FFmpegPCMAudio
from discord.app_commands import describe, default_permissions, allowed_contexts, allowed_installs, checks

async def setup(bot):
    await bot.add_cog(Voice(bot))

class Voice(Cog):
    def __init__(self, bot):
        self.bot = bot

    @hybrid_group(name="voice", description="VC commands", invoke_without_command=True)
    async def v(self, ctx):
        pass

    @Cog.listener()
    async def on_voice_state_update(member, before, after):
        voice_client = member.guild.voice_client
        if not voice_client:
            return
        if before.channel and before.channel.id == voice_client.channel.id:
            human_members = [m for m in voice_client.channel.members if not m.bot]
            if len(human_members) == 0:
                print(f"🤫 Voice channel empty in {member.guild.name}. Starting 30s leave timer...")
                await asyncio.sleep(30)
                if voice_client.channel:
                    current_humans = [m for m in voice_client.channel.members if not m.bot]
                    if len(current_humans) == 0:
                        await voice_client.disconnect()
                        print(f"Left empty voice channel in {member.guild.name} after 30 seconds.")

    @v.command(name="voice-play", description="Connect to your voice channel and play a YouTube audio link")
    @allowed_installs(guilds=True, users=False)
    @describe(youtube_url="The YouTube video link (e.g., https://www.youtube.com/watch?v=...)")
    @checks.cooldown(1, 30.0, key=lambda i: i.guild_id)
    async def voice_play(self, ctx: Context, youtube_url: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("<:disapprove:1517452151012589662> You must be in a voice channel to use this command!", ephemeral=True)
            return

        await ctx.interaction.response.defer() if ctx.interaction else ""
        voice_channel = ctx.author.voice.channel

        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                stream_url = info['url']
                video_title = info.get('title', 'Unknown Title')

            voice_client = ctx.guild.voice_client
            if voice_client is None:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

            if voice_client.is_playing():
                voice_client.stop()

            audio_source = FFmpegPCMAudio(stream_url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS)
            voice_client.play(audio_source, after=lambda e: print(f"Playback ended. Error: {e}") if e else None)
            await ctx.send(f"<:music:1517575582764765224> Now playing: **{video_title}** in {voice_channel.mention}!")

        except Exception as e:
            await ctx.send(f"<:disapprove:1517452151012589662> Failed to play audio. Error: {e}")

    @v.command(name="voice-leave", description="Disconnect the bot from the voice channel")
    @allowed_installs(guilds=True, users=False)
    async def voice_leave(self, ctx: Context):
        voice_client = ctx.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
            await ctx.send("<:wave:1517576345603936296> Disconnected from the voice channel.")
        else:
            await ctx.send("<:disapprove:1517452151012589662> I'm not connected to a voice channel!", ephemeral=True)

    