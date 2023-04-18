import abc
import typing
from typing import Optional, List, Dict

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
from enum import Enum


class CmdSetException(Exception):
    pass


# super class of all windows
# we must use when we send any messages to users
class Window:
    def __init__(self, content: str = None, embed: discord.Embed = None,
                 view: discord.ui.View = None, emojis: typing.List[str] = []):
        self.content = content
        self.embed = embed
        self.view = view
        self.emojis = emojis

    async def send(self, channel: discord.TextChannel) -> discord.Message:
        message = await channel.send(content=self.content, embed=self.embed, view=self.view)
        for emoji in self.emojis:
            await message.add_reaction(emoji)
        return message

    async def response(self, interaction: discord.Interaction):
        if self.view is None:
            message = await interaction.response.send_message(content=self.content, embed=self.embed)
        else:
            message = await interaction.response.send_message(content=self.content, embed=self.embed, view=self.view)
        for emoji in self.emojis:
            await message.add_reaction(emoji)
        return message

    async def edit(self, message: discord.Message) -> None:
        await message.edit(content=self.content, embed=self.embed, view=self.view)


class ExWindow:
    class Pattern(Enum):
        default = 0
        
    def __init__(self, content: Optional[str] = None, embed: Optional[discord.Embed] = None,
                 embeds: List[discord.Embed] = None, view: Optional[discord.ui.View] = None,
                 emojis: List[str] = None):
        self.content = content
        self.embed = embed
        self.embeds = embeds
        self.view = view
        self.emojis = emojis

        self.contents: List[str] = []
        self.embed_patterns: List[discord.Embed] = []

    async def send(self, channel: Union[discord.TextChannel, discord.InteractionResponse]) -> discord.Message:
        if self.embed is None:
            if self.view is None:
                message = await channel.send(content=self.content, embeds=self.embeds)
            else:
                message = await channel.send(content=self.content, embeds=self.embeds, view=self.view)
        else:
            if self.view is None:
                message = await channel.send(content=self.content, embed=self.embed)
            else:
                message = await channel.send(content=self.content, embed=self.embed, view=self.view)

        for emoji in self.emojis:
            await message.add_reaction(emoji)

        return message

    async def reply(self, sender: discord.Message) -> discord.Message:
        if self.embed is None:
            if self.view is None:
                message = await sender.reply(content=self.content, embeds=self.embeds)
            else:
                message = await sender.reply(content=self.content, embeds=self.embeds, view=self.view)
        else:
            if self.view is None:
                message = await sender.reply(content=self.content, embed=self.embed)
            else:
                message = await sender.reply(content=self.content, embed=self.embed, view=self.view)

        for emoji in self.emojis:
            await message.add_reaction(emoji)

        return message

    async def edit(self, sender: discord.Message) -> discord.Message:
        if self.embed is None:
            if self.view is None:
                message = await sender.edit(content=self.content, embeds=self.embeds)
            else:
                message = await sender.edit(content=self.content, embeds=self.embeds, view=self.view)
        else:
            if self.view is None:
                message = await sender.edit(content=self.content, embed=self.embed)
            else:
                message = await sender.edit(content=self.content, embed=self.embed, view=self.view)

        for emoji in self.emojis:
            await message.add_reaction(emoji)

        return message


class EditableWindow(Window):
    def set_embed(self, embed: discord.Embed) -> None:
        self.embed = embed

    def set_view(self, view: discord.ui.View) -> None:
        self.view = view


class WindowManager(commands.Cog):
    class Windows:
        def __init__(self, default: Window, executing=Window(embed=discord.Embed(
                    title='Error', description='このコマンドは現在実行中です。新たに実行はできません。', color=discord.Color.red()
                ))):
            self.default = default
            self.executing = executing

    def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel, windows: Windows):
        self.bot = bot
        self.guild = channel.guild
        self.channel = channel
        self.windows = windows
        self.messages: typing.List[discord.Message] = []

    # this method must be called once only when an instance is initialized
    async def init(self, override=False) -> None:
        if override:
            await self.bot.add_cog(self, guild=self.guild, override=True)
            self.messages.append(await self.windows.default.send(self.channel))
        else:
            try:
                await self.bot.add_cog(self, guild=self.guild)
            except discord.ClientException:
                await self.windows.executing.send(self.channel)
            else:
                self.messages.append(await self.windows.default.send(self.channel))

    async def destroy(self) -> None:
        await self.bot.remove_cog(self.qualified_name, guild=self.guild)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        pass


class Runner(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot, channel: discord.TextChannel):
        self.bot = bot
        self.guild = channel.guild
        self.channel = channel

    async def destroy(self):
        pass


# button used on class Runner
class Button(discord.ui.Button):
    def __init__(self, runner: Runner, style: discord.ButtonStyle = None, label: Optional[str] = None, disabled=False,
                 custom_id: Optional[str] = None, url: Optional[str] = None,
                 emoji: Optional[Union[discord.PartialEmoji, discord.Emoji, str]] = None, row: Optional[int] = None):
        super().__init__(style=style, label=label, disabled=disabled,
                         custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.runner = runner


# super class of all commands
class Command(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot, allow_duplicated=False):
        self.bot = bot
        self.allow_duplicated = allow_duplicated
        # command parser
        self.parser = commandparser.CommandParser()
        self.window_manager: Union[WindowManager, None] = None


class ExCommand(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot, allow_duplicated=False, runner: Runner = None, runners: typing.List[Runner] = []):
        self.bot = bot
        self.allow_duplicated = allow_duplicated
        self.parser = commandparser.CommandParser()
        self.runner = runner
        self.runners = runners
