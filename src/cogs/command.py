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
        class Windows(base.WindowManager.Windows):
            def __init__(self, default: base.Window, generated: base.Window):
                super().__init__(default=default)
                self.generated = generated

        class GenerateButton(discord.ui.Button):
            def __init__(self, channel: discord.TextChannel, window: base.Window):
                super().__init__(label='Push!')
                self.channel = channel
                self.window = window

            async def callback(self, interaction: discord.Interaction):
                await self.window.response(interaction=interaction)

    def __init__(self, bot):
        super().__init__(bot=bot)
        self.emoji_poop = '\N{Pile of Poo}'
        self.disco_emoji_poop = ':poop:'
        self.url_emoji_poop = 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/twitter/322/pile-of-poo_1f4a9.png'

    @commands.command()
    async def poop(self, ctx: commands.Context):
        windows = self.PoopGeneratorWindowManager.Windows(
            default=base.Window(embed=discord.Embed(
                title='Poop Generator', description='Poopが生成できます。'
            ), view=discord.ui.View()),
            generated=base.Window(content=self.disco_emoji_poop)
        )
        windows.default.embed.set_thumbnail(url=self.url_emoji_poop)
        windows.default.view.add_item(self.PoopGeneratorWindowManager.GenerateButton(channel=ctx.channel, window=windows.generated))
        await PoopGenerator.PoopGeneratorWindowManager(
            bot=self.bot,
            channel=ctx.channel,
            windows=windows
        ).init(override=True)


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
            self.window_manager = base.WindowManager(
                bot=self.bot, channel=ctx.channel, windows=base.WindowManager.Windows(
                    default=base.Window(embed=discord.Embed(title='Parrot くん', description=namespace.sentence))
                )
            )
            await self.window_manager.init()
            await self.window_manager.destroy()


async def setup(bot):
    await bot.add_cog(ParrotReturn(bot))
    await bot.add_cog(PoopGenerator(bot))
