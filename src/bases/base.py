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


class Popups:
    def __init__(self, modal_patterns: List[Optional[discord.ui.Modal]]):
        self.modal_patterns = modal_patterns
        self.modal = modal_patterns[0]

    def set_pattern(self, index: int):
        self.modal = self.modal_patterns[index]

    async def response_send(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)


class ExWindow:
    class Pattern(Enum):
        default = 0
        
    def __init__(self, patterns: int, content_patterns: List[Optional[str]] = None,
                 embed_patterns: List[Optional[discord.Embed]] = None,
                 embeds_patterns: List[Optional[List[discord.Embed]]] = None,
                 view_patterns: List[Optional[discord.ui.View]] = None,
                 emojis_patterns: List[Optional[List[str]]] = None):
        self.content: Optional[str] = None
        self.embed: Optional[discord.Embed] = None
        self.embeds: Optional[List[discord.Embed]] = None
        self.view: Optional[discord.ui.View] = None
        self.emojis: Optional[List[str]] = None

        self.patterns = patterns
        if content_patterns is None:
            self.content_patterns = [None for i in range(patterns)]
        else:
            self.content_patterns = content_patterns + [
                None for i in range(patterns - len(content_patterns))
            ]
        if embed_patterns is None:
            self.embed_patterns = [None for i in range(patterns)]
        else:
            self.embed_patterns = embed_patterns + [
                None for i in range(patterns - len(embed_patterns))
            ]
        if embeds_patterns is None:
            self.embeds_patterns = [None for i in range(patterns)]
        else:
            self.embeds_patterns = embeds_patterns + [
                None for i in range(patterns - len(embeds_patterns))
            ]
        if view_patterns is None:
            self.view_patterns = [None for i in range(patterns)]
        else:
            self.view_patterns = view_patterns + [
                None for i in range(patterns - len(view_patterns))
            ]
        if emojis_patterns is None:
            self.emojis_patterns = [None for i in range(patterns)]
        else:
            self.emojis_patterns = emojis_patterns + [
                None for i in range(patterns - len(emojis_patterns))
            ]
        self.set_pattern(0)

    def set_pattern(self, pattern_id: int):
        if self.patterns <= pattern_id:
            raise ValueError
        else:
            self.content = self.content_patterns[pattern_id]
            self.embed = self.embed_patterns[pattern_id]
            self.embeds = self.embeds_patterns[pattern_id]
            self.view = self.view_patterns[pattern_id]
            self.emojis = self.emojis_patterns[pattern_id]

    async def send(self, sender: discord.abc.Messageable) -> discord.Message:
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    if self.view is None:
                        message = await sender.send(embeds=self.embeds)
                    else:
                        message = await sender.send(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.send(embed=self.embed)
                    else:
                        message = await sender.send(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.send(content=self.content)
                    else:
                        message = await sender.send(content=self.content, view=self.view)
                else:
                    if self.view is None:
                        message = await sender.send(content=self.content, embeds=self.embeds)
                    else:
                        message = await sender.send(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.send(content=self.content, embed=self.embed)
                    else:
                        message = await sender.send(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        if self.emojis is not None:
            for emoji in self.emojis:
                await message.add_reaction(emoji)

        return message

    async def reply(self, sender: discord.Message) -> discord.Message:
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    if self.view is None:
                        message = await sender.reply(embeds=self.embeds)
                    else:
                        message = await sender.reply(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.reply(embed=self.embed)
                    else:
                        message = await sender.reply(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.reply(content=self.content)
                    else:
                        message = await sender.reply(content=self.content, view=self.view)
                else:
                    if self.view is None:
                        message = await sender.reply(content=self.content, embeds=self.embeds)
                    else:
                        message = await sender.reply(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.reply(content=self.content, embed=self.embed)
                    else:
                        message = await sender.reply(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        if self.emojis is not None:
            for emoji in self.emojis:
                await message.add_reaction(emoji)

        return message

    async def edit(self, sender: discord.Message) -> discord.Message:
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    if self.view is None:
                        message = await sender.edit(embeds=self.embeds)
                    else:
                        message = await sender.edit(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.edit(embed=self.embed)
                    else:
                        message = await sender.edit(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.edit(content=self.content)
                    else:
                        message = await sender.edit(content=self.content, view=self.view)
                else:
                    if self.view is None:
                        message = await sender.edit(content=self.content, embeds=self.embeds)
                    else:
                        message = await sender.edit(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        message = await sender.edit(content=self.content, embed=self.embed)
                    else:
                        message = await sender.edit(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        await sender.clear_reactions()
        if self.emojis is not None:
            for emoji in self.emojis:
                await message.add_reaction(emoji)

        return message

    async def response_send(self, interaction: discord.Interaction) -> discord.Message:
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    if self.view is None:
                        await interaction.response.send_message(embeds=self.embeds)
                    else:
                        await interaction.response.send_message(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        await interaction.response.send_message(embed=self.embed)
                    else:
                        await interaction.response.send_message(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    if self.view is None:
                        await interaction.response.send_message(content=self.content)
                    else:
                        await interaction.response.send_message(content=self.content, view=self.view)
                else:
                    if self.view is None:
                        await interaction.response.send_message(content=self.content, embeds=self.embeds)
                    else:
                        await interaction.response.send_message(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        await interaction.response.send_message(content=self.content, embed=self.embed)
                    else:
                        await interaction.response.send_message(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        message = await interaction.original_response()
        if self.emojis is not None:
            for emoji in self.emojis:
                await message.add_reaction(emoji)

        return message

    async def response_edit(self, interaction: discord.Interaction) -> discord.Message:
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    await interaction.response.edit_message(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    await interaction.response.edit_message(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    await interaction.response.edit_message(content=self.content, view=self.view)
                else:
                    await interaction.response.edit_message(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    await interaction.response.edit_message(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        message = await interaction.original_response()
        await message.clear_reactions()
        if self.emojis is not None:
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
    def __init__(self, bot: discord.ext.commands.Bot, allow_duplicated=False, runner: Runner = None, runners: List[Runner] = []):
        self.bot = bot
        self.allow_duplicated = allow_duplicated
        self.parser = commandparser.CommandParser()
        self.runner = runner
        self.runners = runners
