from src.bases import base
import discord
from discord.ext import commands


class CallOut(base.Command):
    def __init__(self):
        super().__init__()

    @commands.command
    def call_out(self):
        pass
