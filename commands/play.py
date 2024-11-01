import discord
from discord import app_commands
from discord import FFmpegPCMAudio
import yt_dlp as youtube_dl
import asyncio

queues = {}

def setup(client: discord.Client):
    @client.tree.command(name="join", description="Join a voice channel.")
    async def join(interaction: discord.Interaction):
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            voice_client = interaction.guild.voice_client
            if voice_client is None:
                await channel.connect()
                await interaction.response.send_message(f"Joined {channel}.")
            else:
                await interaction.response.send_message(f"I am already connected to {voice_client.channel}.")
        else:
            await interaction.response.send_message("You are not in a voice channel.")

    @client.tree.command(name="leave", description="Leave the current voice channel.")
    async def leave(interaction: discord.Interaction):
        if interaction.guild.voice_client:
            voice_client = interaction.guild.voice_client
            await voice_client.disconnect()
            queues.pop(voice_client.channel.id, None)
            await interaction.response.send_message(f"Left {voice_client.channel}.")
        else:
            await interaction.response.send_message("Not currently in a voice channel.")

    @client.tree.command(name="play", description="Play audio from YouTube using a link or search keyword.")
    @app_commands.describe(search="YouTube link or search keyword")
    async def play(interaction: discord.Interaction, search: str):
        await interaction.response.defer()
        if not interaction.guild.voice_client:
            await interaction.followup.send("I am not connected to any voice channel.")
            return

        channel_id = interaction.guild.voice_client.channel.id
        if channel_id not in queues:
            queues[channel_id] = []

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1'
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search, download=False)
                video_info = info['entries'][0] if 'entries' in info else info
                url = video_info['url']
                webpage_url = video_info['webpage_url']
                title = video_info.get('title', 'Unknown Title')
                duration = video_info.get('duration', 0)
                thumbnail = video_info.get('thumbnail')

            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            if not interaction.guild.voice_client.is_playing():
                source = FFmpegPCMAudio(url, **ffmpeg_options)
                interaction.guild.voice_client.play(
                    source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), interaction.client.loop)
                )

                embed = discord.Embed(color=discord.Color.blue())
                embed.description = f"[{title}]({webpage_url})"
                embed.add_field(name="Duration", value=f"{duration // 60}:{duration % 60:02d}", inline=True)
                embed.add_field(name="Queue Position", value="Currently playing", inline=True)
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)

                await interaction.followup.send(embed=embed)
            else:
                queues[channel_id].append((url, title, duration, thumbnail, interaction.user, webpage_url))
                queue_position = len(queues[channel_id])

                embed = discord.Embed(title="Added to Queue", color=discord.Color.green())
                embed.description = f"[{title}]({webpage_url})"
                embed.add_field(name="Duration", value=f"{duration // 60}:{duration % 60:02d}", inline=True)
                embed.add_field(name="Queue Position", value=str(queue_position), inline=True)
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)

                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    async def play_next(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        channel_id = voice_client.channel.id

        if queues[channel_id]:
            url, title, duration, thumbnail, user, webpage_url = queues[channel_id].pop(0)
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            source = FFmpegPCMAudio(url, **ffmpeg_options)
            voice_client.play(
                source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction), interaction.client.loop)
            )

            embed = discord.Embed(color=discord.Color.blue())
            embed.description = f"[{title}]({webpage_url})"
            embed.add_field(name="Duration", value=f"{duration // 60}:{duration % 60:02d}", inline=True)
            embed.add_field(name="Queue Position", value="Currently playing", inline=True)
            embed.set_footer(text=f"Requested by {user.name}", icon_url=user.avatar.url)
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("The queue is now empty.")

    @client.tree.command(name="pause", description="Pause the current playback")
    async def pause_playing(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Playback paused.")
        else:
            await interaction.response.send_message("Nothing is playing or already paused.")

    @client.tree.command(name="resume", description="Resume the paused playback")
    async def resume_playing(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Playback resumed.")
        else:
            await interaction.response.send_message("Nothing is paused or playing.")

    @client.tree.command(name="stop", description="Stop playback and clear the queue.")
    async def stop_playing(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        channel_id = voice_client.channel.id

        if voice_client.is_playing():
            voice_client.stop()  # Stop the current playback
            queues.pop(channel_id, None)  # Clear the queue
            await interaction.response.send_message("Playback stopped and the queue has been cleared.")
        else:
            await interaction.response.send_message("Nothing is playing.")

    @client.tree.command(name="clear", description="Clear the current queue.")
    async def clear_queue(interaction: discord.Interaction):
        if interaction.guild.voice_client:
            channel_id = interaction.guild.voice_client.channel.id
            queues.pop(channel_id, None)  # Clear the queue
            await interaction.response.send_message("The queue has been cleared.")
        else:
            await interaction.response.send_message("I am not connected to any voice channel.")

    @client.tree.command(name="skip", description="Skip the currently playing track.")
    async def skip(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Skipped the current track.")
        else:
            await interaction.response.send_message("Nothing is currently playing.")

    @client.tree.command(name="queue", description="View the current queue.")
    async def view_queue(interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            await interaction.response.send_message("I am not connected to any voice channel.")
            return

        channel_id = interaction.guild.voice_client.channel.id
        if channel_id in queues and queues[channel_id]:
            embed = discord.Embed(title="Current Queue", color=discord.Color.purple())

            for i, song in enumerate(queues[channel_id], start=1):
                url, title, duration, thumbnail, user, webpage_url = song

                # Format duration
                duration_str = f"{duration // 60}:{duration % 60:02d}"

                # Use numbering and clickable title link in value
                field_value = f"{i}. **[{title}]({webpage_url})**\n**Duration:** {duration_str}"

                embed.add_field(name="Queue Item", value=field_value, inline=False)

            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("The queue is empty.")
