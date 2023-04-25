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


class Popups:
    def __init__(self, modal_patterns: List[Optional[discord.ui.Modal]]):
        self.modal_patterns = modal_patterns
        self.modal = modal_patterns[0]

    def set_pattern(self, index: int):
        self.modal = self.modal_patterns[index]

    async def response_send(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)


class Window:
    class Pattern(Enum):
        default = 0
        
    def __init__(self, patterns: int, content_patterns: List[Optional[str]] = None,
                 embed_patterns: List[Optional[Dict]] = None,
                 embeds_patterns: List[Optional[List[Dict]]] = None,
                 view_patterns: List[Optional[List[discord.ui.Item]]] = None,
                 emojis_patterns: List[Optional[List[str]]] = None):
        self.message: Optional[discord.Message] = None
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
            self.embed = discord.Embed.from_dict(self.embed_patterns[pattern_id])
            self.embeds = [discord.Embed.from_dict(i) for i in self.embeds_patterns[pattern_id]]
            self.view = discord.ui.View()
            for item in self.view_patterns[pattern_id]:
                self.view.add_item(item=item)
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
                    message = await sender.edit(embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
                    message = await sender.edit(embed=self.embed, view=self.view)
                else:
                    raise ValueError
        else:
            if self.embed is None:
                if self.embeds is None:
                    message = await sender.edit(content=self.content, view=self.view)
                else:
                    message = await sender.edit(content=self.content, embeds=self.embeds, view=self.view)
            else:
                if self.embeds is None:
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


class Runner(commands.Cog):
    def __init__(self, channel: discord.TextChannel, timeout: float = 3.0):
        self.channel = channel
        self.timeout = timeout

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


