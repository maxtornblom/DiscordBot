import discord
from discord.ext import commands
import os
import time
from dotenv import load_dotenv

import discord.ext

# Load token from .env filed
load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("Discord bot token is missing. Please check your .env file.")

# Create bot instance with intents
intents = discord.Intents.all()
client = commands.Bot(command_prefix=lambda bot, msg: [], intents=intents)

# Bot startup time
bot_start_time = time.time()

# Import and set up commands
from commands import setup_uptime, setup_play, setup_getFood

setup_uptime(client, bot_start_time)
setup_play(client)
setup_getFood(client)

# Sync slash commands when bot is ready
@client.event
async def on_ready():
    await client.tree.sync()  # Syncing globally
    print(f"{client.user} is ready and commands are synced globally.")

client.run(TOKEN)
