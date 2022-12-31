import discord
from discord.ext import commands
from bases import base


class Help(base.Command):
    MAX_NUMBER_FIELD = 25

    class WindowManager(base.WindowManager):
        class Windows(base.WindowManager.Windows):
            def __init__(self, default: base.Window):
                super().__init__(default=default)

    @commands.command()
    async def help(self, ctx: commands.Context):
        index = 0
        window = None
        for command in self.bot.walk_commands():
            if index == 0:
                window = base.Window(embed=discord.Embed(title='コマンド一覧'))
            window.embed.add_field(name='/' + command.name)
            if index == Help.MAX_NUMBER_FIELD - 1:
                await window.send(ctx.channel)
            index = (index + 1) % Help.MAX_NUMBER_FIELD
        if index != 0:
            await window.send(ctx.channel)


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(bot)
