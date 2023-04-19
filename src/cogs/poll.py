import typing

import discord
from discord.ext import commands

from bases import base


class Poll(base.ExCommand):
    class Runner(base.Runner):
        class PollWindow(base.ExWindow):
            def __init__(self, runner: 'Poll.Runner'):
                embed_patterns = [
                    discord.Embed(title='Poll', description='右下のボタンから投票を作成できます。'),
                    discord.Embed(title='Poll', description='送信するとチャンネルに東工されます。'),
                ]
                view_patterns = [
                    discord.ui.View(), discord.ui.View()
                ]
                view_patterns[0].add_item(Poll.Runner.AddButton(runner=runner))
                view_patterns[0].add_item(Poll.Runner.CancelButton(runner=runner))
                view_patterns[1].add_item(Poll.Runner.AddButton(runner=runner))
                view_patterns[1].add_item(Poll.Runner.CancelButton(runner=runner))
                view_patterns[1].add_item(Poll.Runner.SendButton(runner=runner))
                super().__init__(patterns=2, embed_patterns=embed_patterns, view_patterns=view_patterns)

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

        class SendButton(discord.ui.Button):
            def __init__(self, runner: 'Poll.Runner'):
                super().__init__(style=discord.ButtonStyle.primary, label='send')
                self.runner = runner

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.send_message('sent')

        class CreatePollWindow(base.Window):
            def __init__(self):
                super().__init__(embed=discord.Embed(
                    title='Poll Generator',
                    description='you can generate polls'
                ))

        def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel):
            self.thread: typing.Union[discord.Thread, None] = None
            self.poll_window: typing.Optional[Poll.Runner.PollWindow] = None
            super().__init__(bot=bot, channel=channel)

        async def run(self, author: discord.User):
            self.thread = await self.channel.create_thread(name='Poll Generator')
            await self.thread.add_user(author)
            self.poll_window = Poll.Runner.PollWindow(runner=self)
            await self.poll_window.send(sender=self.thread)

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
