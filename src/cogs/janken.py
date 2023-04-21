import discord
from discord.ext import commands
from typing import Dict, List

from bases import base
import enum


class Rock(discord.ui.Button):
	async def callback(self, interaction: discord.Interaction):
		pass


class Janken(base.ExCommand):
	class State(enum):
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
					await self.runner.hand(index=self.index, user_id=interaction.user.id)

			class EndButton(discord.ui.Button):
				def __init__(self, runner: 'Janken.Runner'):
					self.runner = runner
					super().__init__(label='ぽい！', style=discord.ButtonStyle.primary)

				async def callback(self, interaction: discord.Interaction):
					state = await self.runner.check()

			def __init__(self, runner: 'Janken.Runner'):
				embed = discord.Embed(title='じゃんけん〜〜')
				view = discord.ui.View()
				view.add_item(Janken.Runner.JankenWindow.HandButton(
					runner=runner, index=0
				))
				view.add_item(Janken.Runner.JankenWindow.HandButton(
					runner=runner, index=1
				))
				view.add_item(Janken.Runner.JankenWindow.HandButton(
					runner=runner, index=2
				))
				view.add_item(Janken.Runner.JankenWindow.EndButton(runner=runner))
				super().__init__(patterns=1, embed_patterns=[
					embed
				], view_patterns=[
					view
				])

		def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel):
			super().__init__(bot=bot, channel=channel)
			self.janken_window = Janken.Runner.JankenWindow(runner=self)
			self.hands: List[List[int]] = [[] for i in range(3)]
			self.result = Janken.State.default

		async def run(self):
			await self.janken_window.send(sender=self.channel)

		async def hand(self, index: int, user_id: int):
			self.hands[index].append(user_id)

		async def check(self):
			victors: List[int] = []
			cnt_participants: int = sum(len(l) for l in self.hands)
			for i in range(3):
				if len(self.hands[(i + 1) % 3]) > 0:
					if len(self.hands[i]):
						self.result = Janken.State(Janken.State.rock_win + i)
					for index in self.hands[i]:
						victors.append(index)

			if len(victors) == 0:
				for i in range(3):
					if len(self.hands[i]) > 0:
						self.result = Janken.State(Janken.State.rock_draw + i)
			elif len(victors) == cnt_participants:
				self.result = Janken.State.draw

			return self.result

	@commands.command()
	async def janken(self, ctx: commands.Context):
		runner = Janken.Runner(bot=self.bot, channel=ctx.channel)
		await runner.run()
		self.runners.append(runner)


async def setup(bot: commands.Bot):
	await bot.add_cog(Janken(bot=bot))
