from datetime import datetime
import traceback
import os
import discord
from discord.ext import commands
from discord.ext import tasks
from datetime import datetime
import asyncio
import sys
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.all()

if len(sys.argv) > 1: 
    TOKEN = API_KEY = os.getenv("API_KEY_TEST")
else:
    TOKEN = API_KEY = os.getenv("API_KEY_PROD")

bot = commands.Bot(command_prefix = '/',intents = intents)

@bot.event
async def on_ready():
    try:
        print("RUNNING")
        print("-------")
        await bot.tree.sync()
        await bot.change_presence(status=discord.Status.idle, activity=discord.Streaming(name = 'Youtube',url = 'https://www.youtube.com/watch?v=gUbWTVsRQAg'))

    except Exception as e:
        print(e)
        traceback.print_exc() 


initial_extensions = []

async def Load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}") 


async def main():
    async with bot:
        await Load()
        await bot.start(TOKEN)

asyncio.run(main())
