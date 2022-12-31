import typing

import discord
from discord.ext import commands, tasks
from bases import base
from bases import commandparser
import heapq
import datetime


class Schedule(base.Command):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot=bot)
        self.parser.add_argument('sentence')
        self.parser.add_argument('date')
        self.scheduled_messages: typing.List[typing.Tuple[datetime.datetime, base.Window, discord.TextChannel]] = []

    @commands.command()
    async def schedule(self, ctx: commands.Context, *args):
        if not self.printer.is_running():
            self.printer.start()
        try:
            namespace = self.parser.parse_args(args=args)
        except commandparser.InputArgumentError as e:
            await ctx.channel.send(embed=e.embed)
        else:
            print(namespace.sentence)
            print(namespace.date)
            heapq.heappush(self.scheduled_messages, (datetime.datetime.strptime(namespace.date, '%Y/%m/%d/%H:%M'),
                                                     base.Window(embed=discord.Embed(description=namespace.sentence)),
                                                     ctx.channel))
            await base.Window(embed=discord.Embed(
                title="予約完了", description=namespace.date + 'に予約しました。'
            )).send(ctx.channel)

    @tasks.loop(seconds=60)
    async def printer(self):
        now = datetime.datetime.now()
        print(now)
        while len(self.scheduled_messages) > 0 and self.scheduled_messages[0][0] <= now:
            window = self.scheduled_messages[0][1]
            channel = self.scheduled_messages[0][2]
            heapq.heappop(self.scheduled_messages)
            await window.send(channel=channel)


async def setup(bot: commands.Bot):
    await bot.add_cog(Schedule(bot=bot))