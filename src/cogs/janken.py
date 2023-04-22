import discord
from discord.ext import commands
from typing import Dict, List

from bases import base
import enum


class Janken(base.ExCommand):
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
		class JankenWindow(base.ExWindow):
			class HandButton(discord.ui.Button):
				emojis = ['\N{Fisted Hand Sign}', '\N{Victory Hand}', '\N{Raised Hand}']

				def __init__(self, runner: 'Janken.Runner', index: int):
					self.runner = runner
					self.index = index
					super().__init__(emoji=self.emojis[index])

				async def callback(self, interaction: discord.Interaction):
					if await self.runner.hand(index=self.index, user_id=interaction.user.id):
						self.runner.janken_window.embed.add_field(name=interaction.user.name, value='')
					await self.runner.janken_window.response_edit(interaction=interaction)

			class EndButton(discord.ui.Button):
				def __init__(self, runner: 'Janken.Runner'):
					self.runner = runner
					super().__init__(label='ぽい！', style=discord.ButtonStyle.primary)

				async def callback(self, interaction: discord.Interaction):
					state = await self.runner.check()
					if Janken.State.rock_win <= state <= Janken.State.paper_win:
						self.runner.janken_window.set_pattern(pattern_id=state + 1)
						self.runner.janken_window.embed.clear_fields()
						for member in self.runner.channel.members:
							if member.id in self.runner.victors:
								self.runner.janken_window.embed.add_field(name=member.name, value='')
					elif Janken.State.rock_draw <= state <= Janken.State.draw:
						self.runner.janken_window.set_pattern(pattern_id=4)
						self.runner.janken_window.embed.clear_fields()
					await self.runner.janken_window.response_edit(interaction=interaction)

			class NextButton(discord.ui.Button):
				def __init__(self, runner: 'Janken.Runner'):
					self.runner = runner
					super().__init__(label='もう一回!', style=discord.ButtonStyle.primary)

				async def callback(self, interaction: discord.Interaction):
					await self.runner.go_next_janken(interaction=interaction)

			def __init__(self, runner: 'Janken.Runner'):
				view_choose = discord.ui.View()
				view_choose.add_item(Janken.Runner.JankenWindow.HandButton(
					runner=runner, index=0
				))
				view_choose.add_item(Janken.Runner.JankenWindow.HandButton(
					runner=runner, index=1
				))
				view_choose.add_item(Janken.Runner.JankenWindow.HandButton(
					runner=runner, index=2
				))
				view_choose.add_item(Janken.Runner.JankenWindow.EndButton(runner=runner))
				view_next = discord.ui.View()
				view_next.add_item(Janken.Runner.JankenWindow.NextButton(runner=runner))
				super().__init__(patterns=5, embed_patterns=[
					discord.Embed(title='じゃんけん～～', description='参加者'),
					discord.Embed(title='グーの勝ち！', description='勝者は'),
					discord.Embed(title='チョキの勝ち!', description='勝者は'),
					discord.Embed(title='パーの勝ち!', description='勝者は'),
					discord.Embed(title='あいこで～～', description='参加者')
				], view_patterns=[
					view_choose, view_next, view_next, view_next, view_choose
				])
				self.embed_patterns[0].set_thumbnail(url='https://em-content.zobj.net/thumbs/240/twitter/322/pig-face_1f437.png')
				self.embed_patterns[1].set_thumbnail(url='https://em-content.zobj.net/thumbs/240/twitter/322/oncoming-fist_1f44a.png')
				self.embed_patterns[2].set_thumbnail(url='https://em-content.zobj.net/thumbs/240/twitter/322/victory-hand_270c-fe0f.png')
				self.embed_patterns[3].set_thumbnail(url='https://em-content.zobj.net/thumbs/240/twitter/322/raised-hand_270b.png')
				self.embed_patterns[4].set_thumbnail(url='https://em-content.zobj.net/thumbs/240/twitter/322/thinking-face_1f914.png')

		def __init__(self, bot: discord.ext.commands.Bot, command: 'Janken', channel: discord.TextChannel):
			super().__init__(bot=bot, channel=channel)
			self.command = command
			self.janken_window = Janken.Runner.JankenWindow(runner=self)
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

		async def hand(self, index: int, user_id: int) -> bool:
			for i in range(3):
				if user_id in self.hands[i]:
					self.hands[i].remove(user_id)
					self.hands[index].append(user_id)
					return False
			self.hands[index].append(user_id)
			return True

		async def check(self):
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

	async def go_next_janken(self, runner: 'Janken.Runner', interaction: discord.Interaction):
		next_runner = Janken.Runner(bot=self.bot, command=self, channel=runner.channel)
		await next_runner.response_run(interaction=interaction)
		self.runners.remove(runner)
		del runner
		self.runners.append(next_runner)

	@commands.command()
	async def janken(self, ctx: commands.Context):
		runner = Janken.Runner(bot=self.bot, command=self, channel=ctx.channel)
		await runner.run()
		self.runners.append(runner)


async def setup(bot: commands.Bot):
	await bot.add_cog(Janken(bot=bot))
