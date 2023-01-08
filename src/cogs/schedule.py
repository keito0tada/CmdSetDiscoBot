import re
import typing
import os
import psycopg2
import psycopg2.extras
import discord
from discord.ext import commands, tasks
from bases import base
from bases import commandparser
import heapq
import datetime
import zoneinfo 

DATABASE_URL = os.getenv('DATABASE_URL')


class InputValueError(base.CmdSetException):
    pass


class Schedule(base.Command):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot=bot)
        self.parser.add_argument('title')
        self.parser.add_argument('description')
        self.parser.add_argument('date')
        self.scheduled_messages: typing.List[typing.Tuple[datetime.datetime, base.Window, discord.TextChannel]] = []
        self.printer.start()
        self.database_connector = psycopg2.connect(DATABASE_URL)
        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS schedule (channelid BIGINT, userid BIGINT, title TEXT, description TEXT, date TIMESTAMP)')
            self.database_connector.commit()

    @commands.command()
    async def schedule(self, ctx: commands.Context, *args):
        if not self.printer.is_running():
            self.printer.start()
        try:
            namespace = self.parser.parse_args(args=args)
        except commandparser.InputArgumentError as e:
            await ctx.channel.send(embed=e.embed)
        else:
            try:
                p = re.compile(r'([0-9]+[^0-9]+){4}[0-9]+')
                if p.fullmatch(namespace.date):
                    date_lst = re.split(r'[/;:\-_,]+', namespace.date)
                    date = datetime.datetime(
                        year=int(date_lst[0]), month=int(date_lst[1]), day=int(date_lst[2]), hour=int(date_lst[3]), minute=int(date_lst[4]))
                else:
                    raise InputValueError

            except (ValueError, InputValueError):
                print('value error')

            else:
                with self.database_connector.cursor() as cur:
                    cur.execute('INSERT INTO schedule (channelid, userid, title, description, date) VALUES {data}'.format(
                        data=(ctx.channel.id, ctx.author.id, namespace.title, namespace.description, str(date))))
                    self.database_connector.commit()
                await base.Window(embed=discord.Embed(
                    title="予約完了", description=namespace.date + 'に予約しました。'
                )).send(ctx.channel)

    @tasks.loop(seconds=60)
    async def printer(self):
        now = datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Tokyo'))
        print(now)
        with self.database_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute('SELECT channelid, userid, title, description, date FROM schedule WHERE date <= \'{}\''.format(str(now)))
            results = cur.fetchall()
            cur.execute('DELETE FROM schedule WHERE date <= \'{}\''.format(str(now)))
            self.database_connector.commit()

        for result in results:
            channel = self.bot.get_channel(result[0])
            user = channel.guild.get_member(result[1])
            embed = discord.Embed(title=result[2], description=result[3])
            embed.set_footer(text='scheduled {}'.format(result[4]))
            if user is not None:
                embed.set_author(name=user.name)
            await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Schedule(bot=bot))
