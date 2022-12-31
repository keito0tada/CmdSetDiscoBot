from discord.ext import commands, tasks
import discord
import argparse
import re
import datetime
import os
from bases import commandparser
from bases import base


class PoopGenerator(base.Command):
    class PoopGeneratorWindowManager(base.WindowManager):
        class WindowID(base.WindowManager.WindowID):
            GENERATED = 2

        class GenerateButton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                pass

    def __init__(self):
        super().__init__()
        self.emoji_poop = '\N{Pile of Poo}'

    @commands.command()
    async def poop(self, ctx: commands.Context):
        view = discord.ui.View()
        view.add_item(self.PoopGeneratorWindowManager.GenerateButton(emoji=self.emoji_poop))
        PoopGenerator.PoopGeneratorWindowManager(
            bot=self.bot,
            channel=ctx.channel,
            windows=dict([(
                PoopGenerator.PoopGeneratorWindowManager.WindowID.DEFAULT,
                base.Window(embed=discord.Embed(
                    title='Poop Generator', description='Poopが生成できます。'
                ), emojis=[self.emoji_poop], view=view)
            ), (
                self.PoopGeneratorWindowManager.WindowID.GENERATED,
                base.Window(embed=discord.Embed(title=self.emoji_poop))
            )])
        )


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
            self.window_managers.append(base.WindowManager(
                channel=ctx.channel, windows=dict([(
                    base.WindowManager.WindowID.DEFAULT,
                    base.Window(embed=discord.Embed(title='Parrot くん', description=namespace.sentence))
                )])
            ))
            await self.window_managers[-1].init()


async def setup(bot):
    print('loaded')
    await bot.add_cog(ParrotReturn(bot))
