import discord
from discord.ext import commands
from typing import Dict, List
import psycopg2
import psycopg2.extras

from bases import base
import enum
import os

#DATABASE_URL = os.getenv('DATABASE_URL')


class JankenWindow(base.Window):
    class HandButton(discord.ui.Button):
        emojis = ['\N{Fisted Hand Sign}', '\N{Victory Hand}', '\N{Raised Hand}']

        def __init__(self, runner: 'Janken.Runner', index: int, pattern_id: int):
            super().__init__(emoji=self.emojis[index])
            self.runner = runner
            self.index = index
            self.pattern_id = pattern_id

        async def callback(self, interaction: discord.Interaction):
            self.runner.hand(index=self.index, user=interaction.user)
            self.runner.janken_window.set_pattern(pattern_id=self.pattern_id)
            fields = []
            for name in self.runner.participants:
                fields.append({'name': name, 'value': '', 'inline': True})
            self.runner.janken_window.embed_dict.setdefault('fields', fields)
            await self.runner.janken_window.response_edit(interaction=interaction)

    class EndButton(discord.ui.Button):
        def __init__(self, runner: 'Janken.Runner'):
            self.runner = runner
            super().__init__(label='ぽい！', style=discord.ButtonStyle.primary)

        async def callback(self, interaction: discord.Interaction):
            state = await self.runner.check()
            if Janken.State.rock_win <= state <= Janken.State.paper_win:
                self.runner.janken_window.set_pattern(pattern_id=state + 1)
                fields = []
                for member in self.runner.channel.members:
                    if member.id in self.runner.victors:
                        fields.append({'name': member.name, 'value': ''})
                self.runner.janken_window.embed_dict.setdefault('fields',fields)
            elif Janken.State.rock_draw <= state <= Janken.State.draw:
                self.runner.janken_window.set_pattern(pattern_id=4)
            await self.runner.janken_window.response_edit(interaction=interaction)

    class NextButton(discord.ui.Button):
        def __init__(self, runner: 'Janken.Runner'):
            self.runner = runner
            super().__init__(label='もう一回!', style=discord.ButtonStyle.primary)

        async def callback(self, interaction: discord.Interaction):
            await self.runner.go_next_janken(interaction=interaction)

    def __init__(self, runner: 'Janken.Runner'):
        super().__init__(patterns=5, embed_patterns=[
            {'title': 'じゃんけん〜〜', 'description': '参加者', 'thumbnail':
                {'url': 'https://em-content.zobj.net/thumbs/240/twitter/322/pig-face_1f437.png'}},
            {'title': 'グーの勝ち!!', 'description': '勝者は', 'thumbnail':
                {'url': 'https://em-content.zobj.net/thumbs/240/twitter/322/oncoming-fist_1f44a.png'}},
            {'title': 'チョキの勝ち!!', 'description': '勝者は', 'thumbnail':
                {'url': 'https://em-content.zobj.net/thumbs/240/twitter/322/victory-hand_270c-fe0f.png'}},
            {'title': 'パーの勝ち!!', 'description': '勝者は', 'thumbnail':
                {'url': 'https://em-content.zobj.net/thumbs/240/twitter/322/raised-hand_270b.png'}},
            {'title': 'あいこで〜〜', 'description': '参加者', 'thumbnail':
                {'url': 'https://em-content.zobj.net/thumbs/240/twitter/322/thinking-face_1f914.png'}}
        ], view_patterns=[
            [
                JankenWindow.HandButton(runner=runner, index=0, pattern_id=0),
                JankenWindow.HandButton(runner=runner, index=1, pattern_id=0),
                JankenWindow.HandButton(runner=runner, index=2, pattern_id=0),
                JankenWindow.EndButton(runner=runner)
            ],
            [JankenWindow.NextButton(runner=runner)],
            [JankenWindow.NextButton(runner=runner)],
            [JankenWindow.NextButton(runner=runner)],
            [
                JankenWindow.HandButton(runner=runner, index=0, pattern_id=4),
                JankenWindow.HandButton(runner=runner, index=1, pattern_id=4),
                JankenWindow.HandButton(runner=runner, index=2, pattern_id=4),
                JankenWindow.EndButton(runner=runner)
            ]
        ])


class Janken(base.Command):
    class State(enum.IntEnum):
        rock_win = 0
        scissor_win = 1
        paper_win = 2
        rock_draw = 3
        scissor_draw = 4
        paper_draw = 5
        draw = 6
        default = 7

    class Runner(base.Runner):
        def __init__(self, command: 'Janken', channel: discord.TextChannel):
            super().__init__(channel=channel)
            self.command = command
            self.janken_window = JankenWindow(runner=self)
            self.participants: List[str] = []
            self.hands: List[List[int]] = [[] for i in range(3)]
            self.result = Janken.State.default
            self.victors: List[int] = []

        async def go_next_janken(self, interaction: discord.Interaction):
            self.janken_window.view.stop()
            await self.command.go_next_janken(runner=self, interaction=interaction)

        async def run(self):
            await self.janken_window.send(sender=self.channel)

        async def response_run(self, interaction: discord.Interaction):
            await self.janken_window.response_send(interaction=interaction)

        def hand(self, index: int, user: discord.User):
            if user.name not in self.participants:
                self.participants.append(user.name)
            for i in range(3):
                if user.id in self.hands[i]:
                    self.hands[i].remove(user.id)
                    self.hands[index].append(user.id)
            self.hands[index].append(user.id)

        async def score(self):
            pass

        async def check(self):
            self.participants = []
            self.victors = []
            cnt_participants: int = sum(len(l) for l in self.hands)
            for i in range(3):
                if len(self.hands[(i + 1) % 3]) > 0:
                    if len(self.hands[i]):
                        self.result = Janken.State(Janken.State.rock_win + i)
                    for index in self.hands[i]:
                        self.victors.append(index)

            if len(self.victors) == 0:
                for i in range(3):
                    if len(self.hands[i]) > 0:
                        self.result = Janken.State(Janken.State.rock_draw + i)
            elif len(self.victors) == cnt_participants:
                self.result = Janken.State.draw

            self.hands = [[] for i in range(3)]
            return self.result

    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(bot=bot)
        self.data: Dict[List[int]] = {}
        #self.database_connector = psycopg2.connect(DATABASE_URL)
        #with self.database_connector.cursor() as cur:
        #    cur.execute(
        #        'CREATE TABLE IF NOT EXISTS janken(channel_id BIGINT, user_id BIGINT, rate INTEGER, rock_win INTEGER, scissor_win INTEGER, paper_win INTEGER, rock_draw INTEGER, scissor_draw INTEGER, paper_win INTEGER, rock_lose INTEGER, scissor_win INTEGER, paper_win INTEGER)')
        #    self.database_connector.commit()

        #with self.database_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
         #   cur.execute(
          #      'SELECT channel_id, user_id, rate, rock_win, scissor_win, paper_win, rock_draw, scissor_draw, paper_draw, rock_lose, scissor_lose, paper_lose FROM janken')
           # results = cur.fetchall()
            #self.database_connector.commit()

    async def go_next_janken(self, runner: 'Janken.Runner', interaction: discord.Interaction):
        next_runner = Janken.Runner(command=self, channel=runner.channel)
        await next_runner.response_run(interaction=interaction)
        self.runners.remove(runner)
        del runner
        self.runners.append(next_runner)

    @commands.command()
    async def janken(self, ctx: commands.Context):
        runner = Janken.Runner(command=self, channel=ctx.channel)
        await runner.run()
        self.runners.append(runner)

    @commands.command()
    async def test(self, ctx: commands.Context):
        embed = discord.Embed(title='*{}*'.format(ctx.author.name))
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Janken(bot=bot))
