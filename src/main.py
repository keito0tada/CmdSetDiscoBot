from discord.ext import commands, tasks
import discord
import asyncio
import os

INITIAL_EXTENSIONS = [
    'cogs.parrot', 'cogs.poll', 'cogs.janken', 'cogs.poop'
]
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print('Ready!')
    await load_initial_extensions()


async def load_initial_extensions():
    for i in INITIAL_EXTENSIONS:
        await bot.load_extension(i)
    print(bot.extensions)

# asyncio.run(load_initial_extensions())
bot.run(TOKEN)
