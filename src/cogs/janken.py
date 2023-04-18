import discord
from discord.ext import commands

from bases import base

class Rock(discord.ui.Button):
	async def callback(self, interaction: discord.Interaction):
		pass

class Janken(base.Command):
	@commands.command()
	async def janken(self, ctx: commands.Context):
		view = discord.ui.View()
		view.add_item(Rock(label='gu'))
		view.add_item(Rock(label='tyoki'))
		view.add_item(Rock(label='pa'))
		await ctx.send(view=view)


async def setup(bot: commands.Bot):
	await bot.add_cog(Janken(bot=bot))
