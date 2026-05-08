import discord
from discord import app_commands, FFmpegPCMAudio
import yt_dlp
import asyncio
import random

# Toggle state per guild
annoy_enabled = {}

# Short meme sound clips
ANNOYING_CLIPS = [
    "https://www.youtube.com/watch?v=ub82Xb1C8os",  # Vine boom
    "https://www.youtube.com/watch?v=2ZIpFytCSVc",  # Bruh
    "https://www.youtube.com/watch?v=B19L6fxDDiA",  # Airhorn
    "https://www.youtube.com/watch?v=OqxlGsODPCQ",  # Bruh 2
    "https://www.youtube.com/watch?v=bKnlCQwvqrg",  # MLG hitmarker
    "https://www.youtube.com/watch?v=o-YBDTqX_ZU",  # Windows XP error
    "https://www.youtube.com/watch?v=gYkACVDFmeg",  # Noot noot
    "https://www.youtube.com/watch?v=ZTidn2dBYbY",  # What are you doing in my swamp
    "https://www.youtube.com/watch?v=aBkTkxKoS4c",  # Spooky scary skeletons intro
    "https://www.youtube.com/watch?v=weKKRwCBFRQ",  # Fart sound
    "https://www.youtube.com/watch?v=0isKu6w7ixQ",  # Sad violin
    "https://www.youtube.com/watch?v=LDU_Txk06tM",  # JOJO pose
]

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -t 5',  # Max 5 seconds so it cuts off long videos
}

YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
}


def get_audio_url(youtube_url: str):
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']


def setup(client: discord.Client):

    @client.tree.command(name="annoy", description="Toggle annoy mode — bot interrupts anyone speaking in VC.")
    async def annoy(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        current = annoy_enabled.get(guild_id, False)
        annoy_enabled[guild_id] = not current

        if annoy_enabled[guild_id]:
            await interaction.response.send_message("😈 Annoy mode **ON** — good luck talking in VC.")
        else:
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("😇 Annoy mode **OFF** — you're safe now.")

    @client.listen('on_voice_state_update')
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild
        guild_id = guild.id

        if not annoy_enabled.get(guild_id, False):
            return

        if member.bot:
            return

        if after.channel is None:
            return

        voice_client = guild.voice_client
        if voice_client and voice_client.is_playing():
            return

        try:
            if voice_client is None:
                voice_client = await after.channel.connect()
            elif voice_client.channel != after.channel:
                await voice_client.move_to(after.channel)

            clip_url = random.choice(ANNOYING_CLIPS)

            loop = asyncio.get_event_loop()
            audio_url = await loop.run_in_executor(None, get_audio_url, clip_url)

            source = FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
            voice_client.play(source)

        except Exception as e:
            print(f"[annoy] Error: {e}")