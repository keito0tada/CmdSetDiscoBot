import re
import typing
import os
import psycopg2
import discord
from discord.ext import commands, tasks
from bases import base
from bases import commandparser
import heapq
import datetime

DATABASE_URL = os.getenv('DATABASE_URL')


class InputValueError(base.CmdSetException):
    pass


class Schedule(base.Command):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot=bot)
        self.parser.add_argument('sentence')
        self.parser.add_argument('date')
        self.scheduled_messages: typing.List[typing.Tuple[datetime.datetime, base.Window, discord.TextChannel]] = []
        self.database_connector = psycopg2.connect(DATABASE_URL)
        self.table_name = 'schedule'
        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS {0} (userid INT, title TEXT, description TEXT, date TIMESTAMP)'.format(
                    self.table_name))
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
            print(namespace.sentence)
            print(namespace.date)
            try:
                p = re.compile(
                    r'[0-9]{4}[/;:\-_,]+(0?[0-9]|1[0-2])[/;:\-_,]+[0-3]?[0-9][/;:\-_,][0-2]?[0-9][/;:\-_,][0-5]?[0-9]')
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
                    cur.execute('SELECT COUNT(userid) FROM {table}'.format(table=self.table_name))
                    print(cur.fetchone())
                    cur.execute('SELECT * FROM {table}'.format(table=self.table_name))
                    print(cur.fetchall())

                with self.database_connector.cursor() as cur:
                    cur.execute('INSERT INTO {table} (userid, description, date) VALUES {data}'.format(
                        table=self.table_name, data=(ctx.author.id, namespace.sentence, str(date))))

                heapq.heappush(self.scheduled_messages, (datetime.datetime.strptime(namespace.date, '%Y/%m/%d/%H:%M'),
                                                         base.Window(
                                                             embed=discord.Embed(description=namespace.sentence)),
                                                         ctx.channel))
                await base.Window(embed=discord.Embed(
                    title="予約完了", description=namespace.date + 'に予約しました。'
                )).send(ctx.channel)

    @tasks.loop(seconds=60)
    async def printer(self):
        now = datetime.datetime.now()
        print(now)
        while len(self.scheduled_messages) > 0 and self.scheduled_messages[0][0] <= now:
            window = self.scheduled_messages[0][1]
            channel = self.scheduled_messages[0][2]
            heapq.heappop(self.scheduled_messages)
            await window.send(channel=channel)


async def setup(bot: commands.Bot):
    await bot.add_cog(Schedule(bot=bot))
