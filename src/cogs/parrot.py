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
            namespace = self.parser.parse_args(args=args)
        except commandparser.InputArgumentError as e:
            await ctx.channel.send(embed=e.embed)
        else:
            embed = discord.Embed(
                title='Parrotくん', description='「{}」'.format(namespace.sentence)
            )
            embed.set_thumbnail(url='https://em-content.zobj.net/thumbs/240/twitter/322/parrot_1f99c.png')
            await ctx.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ParrotReturn(bot))
