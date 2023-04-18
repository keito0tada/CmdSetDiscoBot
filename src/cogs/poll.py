import typing

import discord
from discord.ext import commands

from bases import base


class Poll(base.ExCommand):
    class Runner(base.Runner):
        class PollWindow(base.ExWindow):
            def __init__(self):
                super().__init__(embeds=[
                    discord.Embed(title='投票作成ツール', description='')])


        class AddButton(discord.ui.Button):
            def __init__(self, runner: 'Poll.Runner'):
                super().__init__(style=discord.ButtonStyle.primary, label='add')
                self.runner = runner

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.edit_message(content='hello')

        class CancelButton(discord.ui.Button):
            def __init__(self, runner: 'Poll.Runner'):
                super().__init__(style=discord.ButtonStyle.danger, label='cancel')
                self.runner: Poll.Runner = runner

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.send_message('canceled')
                await self.runner.destroy()

        class CreatePollWindow(base.Window):
            def __init__(self):
                super().__init__(embed=discord.Embed(
                    title='Poll Generator',
                    description='you can generate polls'
                ))

        def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel):
            self.thread: typing.Union[discord.Thread, None] = None
            super().__init__(bot=bot, channel=channel)

        async def run(self, author: discord.User):
            self.thread = await self.channel.create_thread(name='Poll Generator')
            await self.thread.add_user(author)
            view = discord.ui.View()
            view.add_item(Poll.Runner.AddButton(runner=self))
            view.add_item(Poll.Runner.CancelButton(runner=self))
            await self.thread.send(view=view)

        async def destroy(self):
            await self.thread.delete()

    def __init__(self, bot: commands.Bot):
        super().__init__(bot=bot, allow_duplicated=True)

    @commands.command()
    async def poll(self, ctx: commands.Context):
        runner = Poll.Runner(bot=self.bot, channel=ctx.channel)
        await runner.run(author=ctx.author)
        self.runners.append(runner)


async def setup(bot: commands.Bot):
    await bot.add_cog(Poll(bot=bot))
