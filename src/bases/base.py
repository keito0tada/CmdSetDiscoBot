import abc
import typing
from typing import Optional, List, Dict, Union, NamedTuple
from collections import namedtuple

from discord.ext import commands, tasks
import discord
import argparse
import re
import datetime
import os
import asyncio
from bases import commandparser
import enum
from enum import Enum
import zoneinfo

ZONE_TOKYO = zoneinfo.ZoneInfo('Asia/Tokyo')


class DuplicatedSendError(Exception):
    pass


class Popups:
    def __init__(self, modal_patterns: List[Optional[discord.ui.Modal]]):
        self.modal_patterns = modal_patterns
        self.modal = modal_patterns[0]

    def set_pattern(self, index: int):
        self.modal = self.modal_patterns[index]

    async def response_send(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)


class IWindow(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def destroy(self):
        raise NotImplementedError

    @abc.abstractmethod
    def check_index(self, index: enum.IntEnum):
        raise NotImplementedError

    @abc.abstractmethod
    def get_embed_dict(self, index: enum.IntEnum) -> Optional[dict]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_embeds_dicts(self, index: enum.IntEnum) -> Optional[list]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_view_items(self, index: enum.IntEnum) -> Optional[dict]:
        raise NotImplementedError

    @abc.abstractmethod
    async def send(self, sender: discord.abc.Messageable, index: enum.IntEnum) -> 'IWindow':
        raise NotImplementedError

    @abc.abstractmethod
    async def reply(self, message: discord.Message, index: enum.IntEnum) -> 'IWindow':
        raise NotImplementedError

    @abc.abstractmethod
    async def response_send(self, interaction: discord.Interaction, index: enum.IntEnum) -> 'IWindow':
        raise NotImplementedError

    @abc.abstractmethod
    async def edit(self, message: discord.Message, index: enum.IntEnum) -> 'IWindow':
        raise NotImplementedError

    @abc.abstractmethod
    async def response_edit(self, interaction: discord.Interaction, index: enum.IntEnum) -> 'IWindow':
        raise NotImplementedError


class ExWindow(IWindow):
    def __init__(self, content: Optional[str] = None, embed_dict: Optional[dict] = None,
                 embeds_dicts: Optional[dict] = None, view_items: Optional[list[discord.ui.Item]] = None,
                 emojis: Optional[list[str]] = None):
        self.message: Optional[discord.Message] = None
        self.content = content
        self.embed_dict = embed_dict
        self._embed: Optional[discord.Embed] = None
        self.embeds_dicts = embeds_dicts
        self._embeds: Optional[list[discord.Embed]] = None
        self.view_items = view_items
        self._view: Optional[discord.ui.View()] = None
        self.emojis = emojis

    def is_sent(self) -> bool:
        return self.message is not None

    def check_index(self, index: enum.IntEnum):
        if index != 0:
            raise IndexError

    def destroy(self):
        self._view().stop()

    def get_embed_dict(self, index: enum.IntEnum):
        self.check_index(index=index)
        return self.embed_dict

    def get_embeds_dicts(self, index: enum.IntEnum):
        self.check_index(index=index)
        return self.embeds_dicts

    def get_view_items(self, index: enum.IntEnum):
        self.check_index(index=index)
        return self.view_items

    def _prepare_message(self):
        if self.embed_dict is None:
            self._embed = None
        else:
            self._embed = discord.Embed.from_dict(self.embed_dict)
        if self.embeds_dicts is None:
            self._embeds = None
        else:
            self._embeds = [discord.Embed.from_dict(embed) for embed in self.embeds_dicts]
        if self.view_items is None:
            self._view = None
        else:
            self._view = discord.ui.View()
            for item in self.view_items:
                self._view.add_item(item=item)

    async def send(self, sender: discord.abc.Messageable, index: enum.IntEnum) -> 'IWindow':
        if self.is_sent():
            raise DuplicatedSendError
        self._prepare_message()
        if self.content is None:
            if self._embed is None:
                if self._embeds is None:
                    raise ValueError
                else:
                    if self._view is None:
                        self.message = await sender.send(embeds=self._embeds)
                    else:
                        self.message = await sender.send(embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await sender.send(embed=self._embed)
                    else:
                        self.message = await sender.send(embed=self._embed, view=self._view)
                else:
                    raise ValueError
        else:
            if self._embed is None:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await sender.send(content=self.content)
                    else:
                        self.message = await sender.send(content=self.content, view=self._view)
                else:
                    if self._view is None:
                        self.message = await sender.send(content=self.content, embeds=self._embeds)
                    else:
                        self.message = await sender.send(content=self.content, embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await sender.send(content=self.content, embed=self._embed)
                    else:
                        self.message = await sender.send(content=self.content, embed=self._embed, view=self._view)
                else:
                    raise ValueError
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)
        return self

    async def reply(self, message: discord.Message, index: enum.IntEnum) -> 'IWindow':
        if self.is_sent():
            raise DuplicatedSendError
        self._prepare_message()
        if self.content is None:
            if self._embed is None:
                if self._embeds is None:
                    raise ValueError
                else:
                    if self._view is None:
                        self.message = await message.reply(embeds=self._embeds)
                    else:
                        self.message = await message.reply(embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await message.reply(embed=self._embed)
                    else:
                        self.message = await message.reply(embed=self._embed, view=self._view)
                else:
                    raise ValueError
        else:
            if self._embed is None:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await message.reply(content=self.content)
                    else:
                        self.message = await message.reply(content=self.content, view=self._view)
                else:
                    if self._view is None:
                        self.message = await message.reply(content=self.content, embeds=self._embeds)
                    else:
                        self.message = await message.reply(content=self.content, embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await message.reply(content=self.content, embed=self._embed)
                    else:
                        self.message = await message.reply(content=self.content, embed=self._embed, view=self._view)
                else:
                    raise ValueError
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)
        return self

    async def response_send(self, interaction: discord.Interaction, index: enum.IntEnum) -> 'IWindow':
        if self.is_sent():
            raise DuplicatedSendError
        self._prepare_message()
        if self.content is None:
            if self._embed is None:
                if self._embeds is None:
                    raise ValueError
                else:
                    if self._view is None:
                        self.message = await interaction.response.send_message(embeds=self._embeds)
                    else:
                        self.message = await interaction.response.send_message(embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await interaction.response.send_message(embed=self._embed)
                    else:
                        self.message = await interaction.response.send_message(embed=self._embed, view=self._view)
                else:
                    raise ValueError
        else:
            if self._embed is None:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await interaction.response.send_message(content=self.content)
                    else:
                        self.message = await interaction.response.send_message(content=self.content, view=self._view)
                else:
                    if self._view is None:
                        self.message = await interaction.response.send_message(content=self.content, embeds=self._embeds)
                    else:
                        self.message = await interaction.response.send_message(content=self.content, embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await interaction.response.send_message(content=self.content, embed=self._embed)
                    else:
                        self.message = await interaction.response.send_message(content=self.content, embed=self._embed, view=self._view)
                else:
                    raise ValueError
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)
        return self

    async def edit(self, message: discord.Message, index: enum.IntEnum) -> 'IWindow':
        self._prepare_message()
        if self.content is None:
            if self._embed is None:
                if self._embeds is None:
                    raise ValueError
                else:
                    if self._view is None:
                        self.message = await message.edit(embeds=self._embeds)
                    else:
                        self.message = await message.edit(embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await message.edit(embed=self._embed)
                    else:
                        self.message = await message.edit(embed=self._embed, view=self._view)
                else:
                    raise ValueError
        else:
            if self._embed is None:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await message.edit(content=self.content)
                    else:
                        self.message = await message.edit(content=self.content, view=self._view)
                else:
                    if self._view is None:
                        self.message = await message.edit(content=self.content, embeds=self._embeds)
                    else:
                        self.message = await message.edit(content=self.content, embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await message.edit(content=self.content, embed=self._embed)
                    else:
                        self.message = await message.edit(content=self.content, embed=self._embed, view=self._view)
                else:
                    raise ValueError
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)
        return self

    async def response_edit(self, interaction: discord.Interaction, index: enum.IntEnum) -> 'IWindow':
        self._prepare_message()
        if self.content is None:
            if self._embed is None:
                if self._embeds is None:
                    raise ValueError
                else:
                    if self._view is None:
                        self.message = await interaction.response.edit_message(embeds=self._embeds)
                    else:
                        self.message = await interaction.response.edit_message(embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await interaction.response.edit_message(embed=self._embed)
                    else:
                        self.message = await interaction.response.edit_message(embed=self._embed, view=self._view)
                else:
                    raise ValueError
        else:
            if self._embed is None:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await interaction.response.edit_message(content=self.content)
                    else:
                        self.message = await interaction.response.edit_message(content=self.content, view=self._view)
                else:
                    if self._view is None:
                        self.message = await interaction.response.edit_message(content=self.content, embeds=self._embeds)
                    else:
                        self.message = await interaction.response.edit_message(content=self.content, embeds=self._embeds, view=self._view)
            else:
                if self._embeds is None:
                    if self._view is None:
                        self.message = await interaction.response.edit_message(content=self.content, embed=self._embed)
                    else:
                        self.message = await interaction.response.edit_message(content=self.content, embed=self._embed, view=self._view)
                else:
                    raise ValueError
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)
        return self


class ExWindows(IWindow):
    def __init__(self, windows: tuple[IWindow, ...]):
        self.windows = windows
        self.index: Optional[enum.IntEnum] = None

    def destroy(self):
        self.windows[self.index].desctroy()

    def check_index(self, index: enum.IntEnum):
        if index < 0 or len(self.windows) <= index:
            raise IndexError

    def get_embed_dict(self, index: enum.IntEnum) -> Optional[dict]:
        self.check_index(index=index)
        return self.windows[index].get_embed_dict(index=0)

    def get_embeds_dicts(self, index: enum.IntEnum) -> Optional[list]:
        self.check_index(index=index)
        return self.windows[index].get_embeds_dicts(index=0)

    def get_view_items(self, index: enum.IntEnum) -> Optional[dict]:
        self.check_index(index=index)
        return self.windows[index].get_view_items(index=0)

    async def send(self, sender: discord.abc.Messageable, index: enum.IntEnum) -> 'IWindow':
        win = await self.windows[index].send(sender=sender, index=0)
        if isinstance(win, ExWindow):
            self.index = index
            return self
        elif isinstance(win, ExWindows):
            self.windows[self.index].destroy()
            self.index = index
            return win
        else:
            raise TypeError

    async def reply(self, message: discord.Message, index: enum.IntEnum) -> 'IWindow':
        win = await self.windows[index].reply(message=message, index=0)
        if isinstance(win, ExWindow):
            return self
        elif isinstance(win, ExWindows):
            self.windows[self.index].destroy()
            self.index = index
            return win
        else:
            raise TypeError

    async def response_send(self, interaction: discord.Interaction, index: enum.IntEnum) -> 'IWindow':
        self.index = index
        win = await self.windows[index].response_send(interaction=interaction, index=0)
        if isinstance(win, ExWindow):
            return self
        elif isinstance(win, ExWindows):
            self.windows[self.index].destroy()
            self.index = index
            return win
        else:
            raise TypeError

    async def edit(self, message: discord.Message, index: enum.IntEnum) -> 'IWindow':
        self.index = index
        win = await self.windows[index].edit(message=message, index=0)
        if isinstance(win, ExWindow):
            return self
        elif isinstance(win, ExWindows):
            return win
        else:
            raise TypeError

    async def response_edit(self, interaction: discord.Interaction, index: enum.IntEnum) -> 'IWindow':
        self.index = index
        win = await self.windows[index].response_edit(interaction=interaction, index=0)
        if isinstance(win, ExWindow):
            return self
        elif isinstance(win, ExWindows):
            return win
        else:
            raise TypeError


class Window:
    def __init__(self, patterns: int, content_patterns: List[Optional[str]] = None,
                 embed_patterns: List[Optional[Dict]] = None,
                 embeds_patterns: List[Optional[List[Dict]]] = None,
                 view_patterns: List[Optional[List[discord.ui.Item]]] = None,
                 emojis_patterns: List[Optional[List[str]]] = None):
        self.message: Optional[discord.Message] = None
        self.content: Optional[str] = None
        self.embed_dict: Optional[dict] = None
        self.embed: Optional[discord.Embed] = None
        self.embeds_dict: Optional[List[dict]] = None
        self.embeds: Optional[List[discord.Embed]] = None
        self.view: Optional[discord.ui.View] = None
        self.emojis: Optional[List[str]] = None
        self._patterns = patterns
        self._pattern_id = 0
        self._is_set_pattern = False

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
        self.set_pattern(pattern_id=self._pattern_id)

    def set_pattern(self, pattern_id: int):
        self._is_set_pattern = True
        if self._patterns <= pattern_id:
            raise ValueError(pattern_id)
        else:
            self._pattern_id = pattern_id
            self.content = self.content_patterns[pattern_id]
            if self.embed_patterns[pattern_id] is None:
                self.embed_dict = None
            else:
                self.embed_dict = self.embed_patterns[pattern_id].copy()
            if self.embeds_patterns[pattern_id] is None:
                self.embeds_dict = None
            else:
                self.embeds_dict = self.embeds_patterns[pattern_id].copy()
            self.view = discord.ui.View()
            if self.view_patterns[pattern_id] is not None:
                for item in self.view_patterns[pattern_id]:
                    self.view.add_item(item=item)
            if self.emojis_patterns[pattern_id] is None:
                self.emojis = None
            else:
                self.emojis = self.emojis_patterns[pattern_id].copy()

    def _prepare_message(self):
        assert self._is_set_pattern
        if self.embed_patterns[self._pattern_id] is None:
            self.embed = None
        else:
            self.embed = discord.Embed.from_dict(self.embed_dict)
        if self.embeds_patterns[self._pattern_id] is None:
            self.embeds = None
        else:
            self.embeds = [discord.Embed.from_dict(i) for i in self.embeds_dict]

    async def destroy(self):
        self.view.stop()

    async def send(self, sender: discord.abc.Messageable) -> discord.Message:
        self._prepare_message()
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    if self.view is None:
                        self.message = await sender.send(embeds=self.embeds)
                    else:
                        self.message = await sender.send(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        self.message = await sender.send(embed=self.embed)
                    else:
                        self.message = await sender.send(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    if self.view is None:
                        self.message = await sender.send(content=self.content)
                    else:
                        self.message = await sender.send(content=self.content, view=self.view)
                else:
                    if self.view is None:
                        self.message = await sender.send(content=self.content, embeds=self.embeds)
                    else:
                        self.message = await sender.send(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        self.message = await sender.send(content=self.content, embed=self.embed)
                    else:
                        self.message = await sender.send(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)

        return self.message

    async def reply(self, sender: discord.Message) -> discord.Message:
        self._prepare_message()
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    if self.view is None:
                        self.message = await sender.reply(embeds=self.embeds)
                    else:
                        self.message = await sender.reply(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        self.message = await sender.reply(embed=self.embed)
                    else:
                        self.message = await sender.reply(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    if self.view is None:
                        self.message = await sender.reply(content=self.content)
                    else:
                        self.message = await sender.reply(content=self.content, view=self.view)
                else:
                    if self.view is None:
                        self.message = await sender.reply(content=self.content, embeds=self.embeds)
                    else:
                        self.message = await sender.reply(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    if self.view is None:
                        self.message = await sender.reply(content=self.content, embed=self.embed)
                    else:
                        self.message = await sender.reply(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)

        return self.message

    async def edit(self, sender: discord.Message) -> discord.Message:
        self._prepare_message()
        if self.content is None:
            if self.embed is None:
                if self.embeds is None:
                    raise ValueError
                else:
                    self.message = await sender.edit(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    self.message = await sender.edit(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    self.message = await sender.edit(content=self.content, view=self.view)
                else:
                    self.message = await sender.edit(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    self.message = await sender.edit(content=self.content, embed=self.embed, view=self.view)
                else:
                    raise ValueError

        await sender.clear_reactions()
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)

        return self.message

    async def response_send(self, interaction: discord.Interaction) -> discord.Message:
        self._prepare_message()
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

        self.message = await interaction.original_response()
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)

        return self.message

    async def response_edit(self, interaction: discord.Interaction) -> discord.Message:
        self._prepare_message()
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

        self.message = await interaction.original_response()
        await self.message.clear_reactions()
        if self.emojis is not None:
            for emoji in self.emojis:
                await self.message.add_reaction(emoji)

        return self.message

    def is_sent(self) -> bool:
        return self.message is not None

    async def delete(self):
        if self.is_sent():
            await self.message.delete()


class Runner(commands.Cog):
    def __init__(self, channel: discord.TextChannel, timeout: float = 3.0):
        self.channel = channel
        self.timeout = timeout

    async def run(self):
        pass

    async def destroy(self):
        pass

    async def timeout_check(self, minutes: float) -> bool:
        self.timeout -= minutes
        if self.timeout <= 0:
            await self.destroy()
            return True
        else:
            return False


class Command(commands.Cog):
    MINUTES = 3.0

    def __init__(self, bot: discord.ext.commands.Bot, allow_duplicated=False):
        self.bot = bot
        self.allow_duplicated = allow_duplicated
        self.parser = commandparser.CommandParser()
        self.runners: List[Runner] = []

    @tasks.loop(minutes=MINUTES)
    async def timeout_check(self):
        self.runners = [runner for runner in self.runners if await runner.timeout_check(minutes=Command.MINUTES)]


class Button(discord.ui.Button):
    def __init__(self, runner: Runner, style: discord.ButtonStyle = None, label: Optional[str] = None, disabled=False,
                 custom_id: Optional[str] = None, url: Optional[str] = None,
                 emoji: Optional[Union[discord.PartialEmoji, discord.Emoji, str]] = None, row: Optional[int] = None):
        super().__init__(style=style, label=label, disabled=disabled,
                         custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.runner = runner


class View(discord.ui.View):
    def __init__(self, runner: Runner):
        super().__init__(timeout=None)
        self.runner = runner

    async def on_timeout(self) -> None:
        await self.runner.destroy()


class Emoji(NamedTuple):
    discord: str
    text: str
    url: str


