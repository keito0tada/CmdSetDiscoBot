import abc
import typing

from discord.ext import commands, tasks
import discord
import argparse
import re
import datetime
import os
import asyncio
from typing import Union
from bases import commandparser
from dataclasses import dataclass
import enum
from enum import IntEnum


# super class of all windows
# we must use when we send any messages to users
class Window:
    def __init__(self, embed: discord.Embed = None, view: discord.ui.View = None, emojis: typing.List[str] = []):
        self.embed = embed
        self.view = view
        self.emojis = emojis

    async def send(self, channel: discord.TextChannel) -> discord.Message:
        message = await channel.send(embed=self.embed, view=self.view)
        for emoji in self.emojis:
            await message.add_reaction(emoji)
        return message

    async def edit(self, message: discord.Message) -> None:
        await message.edit(embed=self.embed, view=self.view)


class EditableWindow(Window):
    def set_embed(self, embed: discord.Embed) -> None:
        self.embed = embed

    def set_view(self, view: discord.ui.View) -> None:
        self.view = view


class WindowManager(commands.Cog):
    class WindowID(IntEnum):
        EXECUTING = 0
        DEFAULT = 1

    class Windows:
        def __init__(self, executing: Union[Window, None] = None, default: Union[Window, None] = None):
            self.executing = None
            self.default = default
            if executing is None:
                self.executing: Window = Window(embed=discord.Embed(
                    title='Error', description='このコマンドは現在実行中です。新たに実行はできません。', color=discord.Color.red()
                ))

    def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel,
                 windows: Windows):
        self.bot = bot
        self.guild = channel.guild
        self.channel = channel
        self.windows = windows
        self.messages: typing.List[discord.Message] = []

    # this method must be called once only when an instance is initialized
    async def init(self) -> None:
        try:
            await self.bot.add_cog(self, guild=self.guild)
        except discord.ClientException:
            await self.windows[self.WindowID.EXECUTING].send(self.channel)
        else:
            assert len(self.messages) == 0
            self.messages.append(await self.windows[WindowManager.WindowID.DEFAULT].send(self.channel))

    async def send(self, window_id: WindowID) -> None:
        self.messages.append(await self.windows[window_id].send(self.channel))

    async def edit(self, window_id: WindowID, message: discord.Message) -> None:
        await self.windows[window_id].edit(message)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        pass


# super class of all commands
class Command(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.window_managers: typing.List[WindowManager] = []
        # command parser
        self.parser = commandparser.CommandParser()
