import typing
from typing import Optional

import discord
from discord.ext import commands

from bases import base


class Poll(base.Command):
    class Runner(base.Runner):
        class EditPollWindow(base.Window):
            def __init__(self, runner: 'Poll.Runner'):
                embed_patterns = [
                    discord.Embed(title='Poll', description='右下のボタンから投票を作成できます。'),
                    discord.Embed(title='Poll', description='送信するとチャンネルに投稿されます。'),
                    discord.Embed(title='投稿しました。')
                ]
                view_patterns = [
                    discord.ui.View(), discord.ui.View()
                ]
                view_patterns[0].add_item(Poll.Runner.TransitionButton(runner=runner, index=1))
                view_patterns[0].add_item(Poll.Runner.CancelButton(runner=runner))
                view_patterns[1].add_item(Poll.Runner.AddButton(runner=runner))
                view_patterns[1].add_item(Poll.Runner.CancelButton(runner=runner))
                view_patterns[1].add_item(Poll.Runner.SendButton(runner=runner))
                super().__init__(patterns=3, embed_patterns=embed_patterns, view_patterns=view_patterns)

        class SamplePollWindow(base.Window):
            def __init__(self, runner: 'Poll.Runner'):
                embed_patterns = [
                    discord.Embed(title='title', description='description')
                ]
                view_patterns = [discord.ui.View()]
                super().__init__(patterns=1, embed_patterns=embed_patterns, view_patterns=view_patterns)
        
        class PollPopUps(base.Popups):
            def __init__(self, runner: 'Poll.Runner'):
                modal_patterns = [Poll.Runner.SetTitleModal(runner=runner)]
                super().__init__(modal_patterns=modal_patterns)

        class TransitionButton(discord.ui.Button):
            def __init__(self, runner: 'Poll.Runner', index: int,
                         style=discord.ButtonStyle.secondary, label='transition', emoji: Optional[str] = None):
                super().__init__(style=style, label=label, emoji=emoji)
                self.runner = runner
                self.index = index

            async def callback(self, interaction: discord.Interaction):
                self.runner.poll_window.set_pattern(self.index)
                await self.runner.poll_window.response_edit(interaction=interaction)

        class SendModalButton(discord.ui.Button):
            def __init__(self, runner: 'Poll.Runner', modal: discord.ui.Modal,
                         style=discord.ButtonStyle.secondary, label='send a modal',
                         emoji: Optional[str] = None):
                super().__init__(style=style, label=label, emoji=emoji)
                self.runner = runner
                self.modal = modal

        class SetTitleModal(discord.ui.Modal, title='Poll Generator'):
            poll_title = discord.ui.TextInput(label='題名')
            poll_description = discord.ui.TextInput(label='説明', style=discord.TextStyle.paragraph)

            def __init__(self, runner: 'Poll.Runner'):
                super().__init__()
                self.runner = runner

            async def on_submit(self, interaction: discord.Interaction):
                await self.runner.set_title(title=self.poll_title.value,
                                            description=self.poll_description.value)
                await interaction.response.pong()

        class AddButton(discord.ui.Button):
            def __init__(self, runner: 'Poll.Runner'):
                super().__init__(style=discord.ButtonStyle.primary, label='add', emoji='\N{Pile of Poo}', row=2)
                self.runner = runner

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.send_modal(Poll.Runner.SetTitleModal(runner=self.runner))

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
                await self.runner.send_poll()
                self.runner.poll_window.set_pattern(pattern_id=2)
                await self.runner.poll_window.response_edit(interaction=interaction)

        def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel):
            self.thread: typing.Union[discord.Thread, None] = None
            self.poll_window: typing.Optional[Poll.Runner.EditPollWindow] = None
            self.sample_poll_window: Optional[Poll.Runner.SamplePollWindow] = None
            super().__init__(bot=bot, channel=channel)

        async def run(self, author: discord.User):
            self.thread = await self.channel.create_thread(name='Poll Generator')
            await self.thread.add_user(author)
            self.poll_window = Poll.Runner.EditPollWindow(runner=self)
            await self.poll_window.send(sender=self.thread)
            self.sample_poll_window = Poll.Runner.SamplePollWindow(runner=self)

        async def set_title(self, title: str, description: str):
            self.sample_poll_window.embeds[2] = discord.Embed(title=title, description=description)

        async def send_poll(self):
            await self.sample_poll_window.send(sender=self.channel)

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
