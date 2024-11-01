import discord
from discord import app_commands
import time

def setup(client: discord.Client, bot_start_time: float):
    @client.tree.command(name="uptime", description="Check the bot's uptime")
    async def uptime(interaction: discord.Interaction):
        current_time = time.time()
        uptime_seconds = int(current_time - bot_start_time)
        uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
        
        embed = discord.Embed(title="Bot Uptime", description=f"Uptime: {uptime_str}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
