import discord
from discord.ext import commands, tasks
import psycopg2
import psycopg2.extras

import enum, os, datetime, zoneinfo
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from bases import base, commandparser
from cogs.openweathermap import OWM

DATABASE_URL = os.getenv('DATABASE_URL')
ZONE_TOKYO = zoneinfo.ZoneInfo('Asia/Tokyo')
DEFAULT_TIMES = [datetime.time(hour=0, minute=5)]


class Runner(base.Runner):
    def __init__(self):
        pass


class Weather(base.Command):
    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(bot=bot)
        self.owm = OWM()
        self.database_connector = psycopg2.connect(DATABASE_URL)

    @commands.command()
    async def weather(self, ctx: discord.ext.commands.Context):
        weather = await self.owm.get_current_weather(lat=35.689, lon=139.692)
        await ctx.send(embed=discord.Embed.from_dict({
            'title': weather.city.name, 'description': '本日{0}時点での天候は{1}です。'.format(
                weather.time.strftime('%H時%M分'), weather.conditions[0].description),
            'thumbnail': {'url': weather.get_icon_url()},
            'fields': [
                {'name': '気温', 'value': '{}°C'.format(weather.main.temperature), 'inline': True},
                {'name': '最高気温', 'value': '{}°C'.format(weather.main.temperature_max), 'inline': True},
                {'name': '最低気温', 'value': '{}°C'.format(weather.main.temperature_min), 'inline': True},
                {'name': '湿度', 'value': '{}%'.format(weather.main.humidity), 'inline': True},
                {'name': '気圧', 'value': '{}hPa'.format(weather.main.pressure), 'inline': True}
            ],
            'footer': {
                'text': 'OpenWeatherを参照しています。',
                'icon_url': weather.OPEN_WEATHER_ICON_URL
            }
            })
        )

    @commands.command()
    async def forecast(self, ctx: discord.ext.commands.Context):
        weather = (await self.owm.get_forecast(lat=35.689, lon=139.692)).get_forecast_index(39)
        await ctx.send(embed=discord.Embed.from_dict({
            'title': weather.city.name, 'description': '{0}時点での天候は{1}と予測されます。。'.format(
                weather.time.strftime('%Y年%m月%d日%H時%M分'), weather.conditions[0].description),
            'thumbnail': {'url': weather.get_icon_url()},
            'fields': [
                {'name': '気温', 'value': '{}°C'.format(weather.main.temperature), 'inline': True},
                {'name': '最高気温', 'value': '{}°C'.format(weather.main.temperature_max), 'inline': True},
                {'name': '最低気温', 'value': '{}°C'.format(weather.main.temperature_min), 'inline': True},
                {'name': '湿度', 'value': '{}%'.format(weather.main.humidity), 'inline': True},
                {'name': '気圧', 'value': '{}hPa'.format(weather.main.pressure), 'inline': True}
            ],
            'footer': {
                'text': 'OpenWeatherを参照しています。',
                'icon_url': weather.OPEN_WEATHER_ICON_URL
            }
        })
        )

    @tasks.loop(time=DEFAULT_TIMES)
    async def notice(self):
        pass


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(Weather(bot=bot))
