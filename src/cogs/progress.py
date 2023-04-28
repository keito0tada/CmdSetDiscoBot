import zoneinfo

import discord
from discord.ext import commands, tasks
from typing import Dict, List
import psycopg2
import psycopg2.extras
import datetime

from bases import base
import enum
import os

#DATABASE_URL = os.getenv('DATABASE_URL')
TIME = datetime.time(hour=0, minute=0, tzinfo=zoneinfo.ZoneInfo('Asia/Tokyo'))


class Progress(base.Command):
    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(bot=bot)
        self.printer.start()

    @commands.command()
    async def progress(self, ctx: commands.Context):
        pass

    @tasks.loop(time=TIME)
    async def printer(self):
        pass


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(Progress(bot=bot))
