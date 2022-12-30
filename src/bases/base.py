import abc
import typing

from discord.ext import commands, tasks
import discord
import argparse
import re
import datetime
import os
from typing import Union
from bases import commandparser
from dataclasses import dataclass
from enum import IntEnum


# super class of all windows
# we must use when we send any messages to users
class Window:
    def __init__(self, embed: discord.Embed = None, view: discord.ui.View = None):
        self.embed = embed
        self.view = view

    async def send(self, channel: discord.TextChannel) -> discord.Message:
        return await channel.send(embed=self.embed, view=self.view)

    async def edit(self, message: discord.Message) -> None:
        await message.edit(embed=self.embed, view=self.view)


class DynamicWindow(Window):
    def set_embed(self, embed: discord.Embed) -> None:
        self.embed = embed

    def set_view(self, view: discord.ui.View) -> None:
        self.view = view


class WindowName(IntEnum):
    default = 0


class MessageManager:
    def __init__(self, channel: discord.TextChannel, windows: typing.Dict[WindowName, Window]):
        self.channel = channel
        self.windows = windows
        self.message: Union[discord.Message, None] = None

    async def send(self):
        self.message = await self.windows[WindowName.default].send(self.channel)

    async def edit(self, window_name: WindowName):
        await self.windows[window_name].edit(self.message)


# super class of all commands
class Command(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.message_manager: Union[MessageManager, None] = None
        # command parser
        self.parser = commandparser.CommandParser()
        # parsed arguments
        self.args: Union[commandparser.CommandParser.Namespace, None] = None

    def is_running(self) -> bool:
        return self.message_manager is not None
