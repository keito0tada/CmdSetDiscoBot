from discord.ext import commands, tasks
import discord
import argparse
import re
import datetime
import os
from bases import commandparser
from bases import base


class ParrotReturn(base.Command):
    def __init__(self, bot):
        super().__init__(bot=bot)
        self.parser.add_argument('sentence')

    @commands.command()
    async def parrot(self, ctx: commands.Context, *args):
        try:
            self.parser.parse_args(args=args)
        except commandparser.InputArgumentError as e:
            await ctx.channel.send(embed=e.embed)
        else:
            self.message_manager = base.MessageManager(
                channel=ctx.channel, windows=dict([(base.WindowName.default, base.Window(
                    embed=discord.Embed(title='Parrot くん', description=self.parser.namespace.sentence)))])
            )
            await self.message_manager.send()


async def setup(bot):
    print('loaded')
    await bot.add_cog(ParrotReturn(bot))
