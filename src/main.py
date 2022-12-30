from discord.ext import commands, tasks
import discord
import asyncio

INITIAL_EXTENSIONS = [
    'cogs.command'
]
# TOKEN = os.getenv('DISCORD_BOT_TOKEN')
TOKEN = 'MTAyNzE2OTA5NjQyMjQwODI0Mw.GRpk0u.MURnA90p8zrw4nrBsMU1E2s297vzfpD7c-6sjM'
bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print('Ready!')


async def load_initial_extensions():
    for i in INITIAL_EXTENSIONS:
        await bot.load_extension(i)
    print(bot.extensions)


asyncio.run(load_initial_extensions())
bot.run(TOKEN)
