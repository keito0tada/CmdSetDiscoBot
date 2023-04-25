from discord.ext import commands, tasks
import discord
import argparse
import re
import datetime
import os
from bases import commandparser
from bases import base
from typing import List


class PoopWindow(base.Window):
    class GenerateButton(discord.ui.Button):
        def __init__(self, runner: 'PoopGenerator.Runner', style: discord.ButtonStyle):
            self.runner = runner
            super().__init__(label='Push!!', style=style)

        async def callback(self, interaction: discord.Interaction):
            self.runner.window.set_pattern(pattern_id=1)
            await self.runner.window.response_send(interaction=interaction)

    def __init__(self, runner: 'PoopGenerator.Runner'):
        super().__init__(patterns=2, content_patterns=[None, ':poop:'], embed_patterns=[
            {'title?': 'Poop Generator', 'description?': 'Poopを生成できます。',
             'thumbnail?': 'https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/twitter/322/pile-of-poo_1f4a9.png'},
            None
        ], view_patterns=[[
            PoopWindow.GenerateButton(runner=runner, style=discord.ButtonStyle.primary)
        ], None])


class PoopGenerator(base.Command):
    class Runner(base.Runner):
        def __init__(self, channel: discord.TextChannel):
            super().__init__(channel=channel)
            self.window = PoopWindow(runner=self)

        def destroy(self):
            pass

    def __init__(self, bot):
        super().__init__(bot=bot)

    @commands.command()
    async def poop(self, ctx: commands.Context):
        self.runners.append(PoopGenerator.Runner(channel=ctx.channel))


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(PoopGenerator(bot=bot))