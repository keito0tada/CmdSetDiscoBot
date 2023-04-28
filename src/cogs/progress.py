import zoneinfo

import discord
from discord.ext import commands, tasks
from typing import Dict, List,Optional
import psycopg2
import psycopg2.extras
import datetime

from bases import base
import enum
import os

#DATABASE_URL = os.getenv('DATABASE_URL')
ZONE_TOKYO = zoneinfo.ZoneInfo('Asia/Tokyo')
TIME = datetime.time(hour=16, minute=51, tzinfo=ZONE_TOKYO)


class Progress(base.Command):
    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(bot=bot)
        self.printer.start()
        print(self.printer.next_iteration)
        self.channel: Optional[discord.TextChannel] = bot.get_channel(1099254013347758100)

    @commands.command()
    async def progress(self, ctx: commands.Context):
        if self.printer.is_running() == False:
            self.printer.start()
        self.channel = ctx.channel
        await ctx.channel.send('このチャンネルを進捗報告チャンネルとして登録しました。')

    @tasks.loop(time=TIME)
    async def printer(self):
        members_not_sent = self.channel.members
        now_time = datetime.datetime.now(tz=ZONE_TOKYO)
        start_time = now_time - datetime.timedelta(days=1)
        async for message in self.channel.history(after=start_time):
            if message.author in members_not_sent:
                members_not_sent.remove(message.author)

        if len(members_not_sent) > 0:
            mentions = ''
            for member in members_not_sent:
                mentions = '{0} {1}'.format(mentions, member.mention)
            await self.channel.send(embed=discord.Embed(
                title='今日の進捗はどうですか？', description=mentions
            ))


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(Progress(bot=bot))
