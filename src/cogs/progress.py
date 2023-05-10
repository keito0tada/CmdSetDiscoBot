import time
import zoneinfo

import discord
from discord.ext import commands, tasks
from typing import Dict, List, Optional, Union
import psycopg2
import psycopg2.extras
import datetime
import zoneinfo

from bases import base
import enum
import os

DATABASE_URL = os.getenv('DATABASE_URL')
ZONE_TOKYO = zoneinfo.ZoneInfo('Asia/Tokyo')
DEFAULT_TIMES = [
    datetime.time(hour=0, minute=0, tzinfo=ZONE_TOKYO),
    datetime.time(hour=6, minute=0, tzinfo=ZONE_TOKYO),
    datetime.time(hour=12, minute=0, tzinfo=ZONE_TOKYO),
    datetime.time(hour=18, minute=0, tzinfo=ZONE_TOKYO),
    datetime.time(hour=16, minute=52, tzinfo=ZONE_TOKYO)
]
MAX_HP = 3
HEAL_HP_PER_STREAK = 3
THINKING_FACE = base.Emoji(
    discord=':thinking_face:',
    text='\N{thinking face}',
    url=''
)


class SettingChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, runner: 'Runner'):
        super().__init__(channel_types=[discord.ChannelType.text])
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.select_channel(values=self.values, interaction=interaction)


class IntervalDaysSelect(discord.ui.Select):
    FORMAT = '{}.interval_days_select'

    def __init__(self, runner: 'Runner'):
        options = [discord.SelectOption(label='毎日', value=self.FORMAT.format(1))] + \
                  [discord.SelectOption(label='{}日ごと'.format(i), value=self.FORMAT.format(i)) for i in range(2, 7)] + \
                  [discord.SelectOption(label='1週間ごと', value=self.FORMAT.format(7))]
        super().__init__(placeholder='送信する間隔', options=options)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        assert len(self.values) == 1
        self.runner.interval = datetime.timedelta(days=int(self.values[0][0]))
        await interaction.response.defer()


class HourSelect(discord.ui.Select):
    FORMAT = '{:0=2}.hour_select'

    def __init__(self, runner: 'Runner'):
        super().__init__(placeholder='時', options=[
            discord.SelectOption(label='{}時'.format(i), value=self.FORMAT.format(i)) for i in range(24)
        ])
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        assert len(self.values) == 1
        self.runner.hour = int(self.values[0][0:2])
        await interaction.response.defer()


class MinuteSelect(discord.ui.Select):
    FORMAT = '{:0=2}.minute_select'

    def __init__(self, runner: 'Runner'):
        super().__init__(placeholder='分', options=[
            discord.SelectOption(label='{}分'.format(i), value=self.FORMAT.format(i)) for i in range(0, 60, 5)
        ])
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        assert len(self.values) == 1
        self.runner.minute = int(self.values[0][0:2])
        await interaction.response.defer()


class NextDaySelect(discord.ui.Select):
    def __init__(self, runner: 'Runner'):
        now = datetime.datetime.now(tz=ZONE_TOKYO)
        super().__init__(placeholder='最初に送信される日', options=[
            discord.SelectOption(label='{}'.format((now + datetime.timedelta(days=i)).date()),
                                 value=(now + datetime.timedelta(days=i)).date().strftime('%Y:%m:%d')) for i in range(7)
        ])
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        assert len(self.values) == 1
        self.runner.next_date = datetime.datetime.strptime(self.values[0], '%Y:%m:%d').date()
        await interaction.response.defer()


class AddButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='追加', style=discord.ButtonStyle.primary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.add(interaction=interaction)


class EditButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='変更', style=discord.ButtonStyle.primary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.edit(interaction=interaction)


class BackButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='戻る', style=discord.ButtonStyle.secondary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.back(interaction=interaction)


class DeleteButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='削除', style=discord.ButtonStyle.danger)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.delete(interaction=interaction)


class MembersButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='報告状況', style=discord.ButtonStyle.primary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.member(interaction=interaction)


class SettingButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='設定', style=discord.ButtonStyle.primary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.setting(interaction=interaction)


class BackMenuButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='戻る', style=discord.ButtonStyle.secondary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.back_menu(interaction=interaction)


class BackMembersButton(discord.ui.Button):
    def __init__(self, runner: 'Runner'):
        super().__init__(label='戻る', style=discord.ButtonStyle.secondary)
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.back_members(interaction=interaction)


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, runner: 'Runner'):
        super().__init__(placeholder='メンバー')
        self.runner = runner

    async def callback(self, interaction: discord.Interaction):
        await self.runner.select_member(values=self.values, interaction=interaction)


class ProgressWindow(base.Window):
    class WindowID(enum.IntEnum):
        SETTING = 0
        ADD = 1
        EDIT = 2
        ADDED = 3
        EDITED = 4
        DELETED = 5
        MENU = 6
        MEMBERS = 7
        MEMBER = 8

    def __init__(self, runner: 'Runner'):
        super().__init__(patterns=9, embed_patterns=[
            {'title': '進捗報告チャンネル　設定',
             'description': '進捗報告用のチャンネルを設定できます。進捗報告がないメンバーには催促のメンションが飛びます。'},
            {'title': '追加', 'description': '時間を指定して追加できます。'},
            {'title': '変更', 'description': '時間を変更できます。'},
            {'title': '追加 完了'},
            {'title': '変更 完了'},
            {'title': '削除 完了'},
            {'title': '進捗報告 監視',
             'description': '設定したチャンネルに進捗報告があるか監視します。指定した期間内に報告がない場合はメンションが飛びます。また一定回数報告がない場合はこのサーバーからKickされます。'},
            {'title': '進捗報告　状況', 'description': 'メンバーの進捗報告状況が確認できます。'},
            {'title': 'member name'}
        ], view_patterns=[
            [SettingChannelSelect(runner=runner), BackMenuButton(runner=runner)],
            [IntervalDaysSelect(runner=runner), HourSelect(runner=runner), MinuteSelect(runner=runner),
             NextDaySelect(runner=runner), AddButton(runner=runner), BackButton(runner=runner)],
            [IntervalDaysSelect(runner=runner), HourSelect(runner=runner), MinuteSelect(runner=runner),
             NextDaySelect(runner=runner), EditButton(runner=runner), BackButton(runner=runner),
             DeleteButton(runner=runner)],
            [BackButton(runner=runner)], [BackButton(runner=runner)], [BackButton(runner=runner)],
            [MembersButton(runner=runner), SettingButton(runner=runner)],
            [MemberSelect(runner=runner), BackMenuButton(runner=runner)],
            [BackMembersButton(runner=runner)]
        ])


class Runner(base.Runner):
    def __init__(self, command: 'Progress', channel: discord.TextChannel, database_connector):
        super().__init__(channel=channel)
        self.command = command
        self.progress_window = ProgressWindow(runner=self)
        self.database_connector = database_connector
        self.chosen_channel: Optional[discord.TextChannel] = None
        self.interval: Optional[datetime.timedelta] = None
        self.prev_hour: Optional[int] = None
        self.hour: Optional[int] = None
        self.prev_minute: Optional[int] = None
        self.minute: Optional[int] = None
        self.next_date: Optional[datetime.date] = None

    async def run(self):
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.MENU)
        await self.progress_window.send(sender=self.channel)

    async def select_channel(self, values: List[discord.app_commands.AppCommandChannel],
                             interaction: discord.Interaction):
        assert len(values) == 1
        self.chosen_channel = values[0].resolve()
        with self.database_connector.cursor() as cur:
            cur.execute('SELECT interval, time, timestamp FROM progress WHERE channel_id = %s',
                        (self.chosen_channel.id,))
            results = cur.fetchall()
            self.database_connector.commit()
        if len(results) == 0:
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.ADD)
            self.progress_window.embed_dict['title'] = '追加 #{}'.format(self.chosen_channel.name)
        elif len(results) == 1:
            self.interval = results[0][0]
            self.prev_hour = results[0][1].hour
            self.hour = self.prev_hour
            self.prev_minute = results[0][1].minute
            self.minute = results[0][1].minute
            self.next_date = results[0][2].astimezone(tz=ZONE_TOKYO).date()
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.EDIT)
            self.progress_window.embed_dict['title'] = '変更 #{}'.format(self.chosen_channel.name)
            self.progress_window.embed_dict['fields'] = [
                {'name': '送信する間隔', 'value': '{}日ごと'.format(self.interval.days)},
                {'name': '送信する時刻', 'value': '{0}時{1}分'.format(self.hour, self.minute)},
                {'name': '次に送信される日付', 'value': str(self.next_date)}
            ]
        else:
            raise ValueError
        await self.progress_window.response_edit(interaction=interaction)

    async def add(self, interaction: discord.Interaction):
        if self.interval is None or self.hour is None or self.minute is None or self.next_date is None:
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.ADD)
            self.progress_window.embed_dict['color'] = 0x8b0000
            self.progress_window.embed_dict['fields'] = [{'name': 'エラー', 'value': '要素をすべて選択してください。'}]
        else:
            with self.database_connector.cursor() as cur:
                cur.execute('SELECT channel_id FROM progress WHERE channel_id = %s', (self.chosen_channel.id,))
                results = cur.fetchall()
                _time = datetime.time(hour=self.hour, minute=self.minute, tzinfo=ZONE_TOKYO)
                _next_date = datetime.datetime.combine(date=self.next_date, time=_time, tzinfo=ZONE_TOKYO)
                if len(results) == 0:
                    cur.execute(
                        'INSERT INTO progress (channel_id, interval, time, timestamp, prev_timestamp, prev_prev_timestamp, member_ids) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (self.chosen_channel.id, self.interval, _time,
                         _next_date, _next_date - self.interval, _next_date - self.interval * 2,
                         [member.id for member in interaction.message.channel.members])
                    )
                    self.database_connector.commit()
                else:
                    cur.execute(
                        'UPDATE progress SET interval = %s, time = %s, timestamp = %s WHERE channel_id = %s',
                        (self.interval, _time, _next_date,
                         self.chosen_channel.id)
                    )
                    self.database_connector.commit()
            self.command.change_printer_interval()
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.ADDED)
            self.progress_window.embed_dict['fields'] = [
                {'name': '送信する間隔', 'value': '{}日ごと'.format(self.interval.days)},
                {'name': '送信する時刻', 'value': '{0}時{1}分'.format(self.hour, self.minute)},
                {'name': '次に送信される日付', 'value': str(self.next_date)}
            ]
        await self.progress_window.response_edit(interaction=interaction)

    async def edit(self, interaction: discord.Interaction):
        if datetime.datetime.now(tz=ZONE_TOKYO) >= datetime.datetime.combine(
                date=self.next_date, time=datetime.time(hour=self.hour, minute=self.minute), tzinfo=ZONE_TOKYO):
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.EDIT)
            self.progress_window.embed_dict['color'] = 0x8b0000
            self.progress_window.embed_dict['fields'] = [{'name': 'エラー', 'value': '次回の時刻は現在以降の時刻を設定してください。'}]
        else:
            with self.database_connector.cursor() as cur:
                cur.execute('SELECT channel_id FROM progress WHERE channel_id = %s', (self.chosen_channel.id,))
                results = cur.fetchall()
                _time = datetime.time(hour=self.hour, minute=self.minute, tzinfo=ZONE_TOKYO)
                _next_date = datetime.datetime.combine(date=self.next_date, time=_time, tzinfo=ZONE_TOKYO)
                if len(results) == 0:
                    cur.execute(
                        'INSERT INTO progress (channel_id, interval, time, timestamp, prev_timestamp, prev_prev_timestamp, member_ids) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (self.chosen_channel.id, self.interval, _time,
                         _next_date, _next_date - self.interval, _next_date - self.interval * 2,
                         [member.id for member in interaction.message.channel.members])
                    )
                    self.database_connector.commit()
                else:
                    cur.execute(
                        'UPDATE progress SET interval = %s, time = %s, timestamp = %s WHERE channel_id = %s',
                        (self.interval, _time, _next_date, self.chosen_channel.id)
                    )
                 self.database_connector.commit()
            self.command.change_printer_interval()
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.EDITED)
            self.progress_window.embed_dict['fields'] = [
                {'name': '送信する間隔', 'value': '{}日ごと'.format(self.interval.days)},
                {'name': '送信する時刻', 'value': '{0}時{1}分'.format(self.hour, self.minute)},
                {'name': '次に送信される日付', 'value': str(self.next_date)}
            ]
        await self.progress_window.response_edit(interaction=interaction)

    async def back(self, interaction: discord.Interaction):
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.SETTING)
        await self.progress_window.response_edit(interaction=interaction)

    async def delete(self, interaction: discord.Interaction):
        with self.database_connector.cursor() as cur:
            cur.execute('DELETE FROM progress WHERE channel_id = %s', (self.chosen_channel.id,))
            self.database_connector.commit()
        self.command.change_printer_interval()
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.DELETED)
        await self.progress_window.response_edit(interaction=interaction)

    async def member(self, interaction: discord.Interaction):
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.MEMBERS)
        await self.progress_window.response_edit(interaction=interaction)

    async def setting(self, interaction: discord.Interaction):
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.SETTING)
        await self.progress_window.response_edit(interaction=interaction)

    async def back_menu(self, interaction: discord.Interaction):
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.MENU)
        await self.progress_window.response_edit(interaction=interaction)

    async def select_member(self, values: List[Union[discord.Member, discord.User]], interaction: discord.Interaction):
        assert len(values) == 1
        with self.database_connector.cursor() as cur:
            cur.execute('SELECT total, streak, escape, denied, hp, kick FROM progress_members WHERE user_id = %s',
                        (values[0].id,))
            results = cur.fetchall()
            self.database_connector.commit()
        total = 0
        streak = 0
        escape = 0
        denied = 0
        hp = MAX_HP
        kick = 0
        if len(results) == 0:
            with self.database_connector.cursor() as cur:
                cur.execute(
                    'INSERT INTO progress_members (user_id, total, streak, escape, denied, hp, kick) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (values[0].id, total, streak, escape, denied, hp, kick))
                self.database_connector.commit()
        elif len(results) == 1:
            total, streak, escape, denied, hp, kick = results[0]
        else:
            raise ValueError
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.MEMBER)
        self.progress_window.embed_dict['title'] = '*{}*'.format(values[0].name)
        self.progress_window.embed_dict['thumbnail'] = {'url': values[0].display_avatar.url}
        self.progress_window.embed_dict['fields'] = [
            {'name': '報告回数', 'value': '{}回'.format(total)},
            {'name': '現在の連続日数', 'value': '{}日'.format(streak)},
            {'name': '報告忘れ回数', 'value': '{}回'.format(escape)},
            {'name': '却下された回数', 'value': '{}回'.format(denied)},
            {'name': 'Kickされるまでの残り回数', 'value': '{}回'.format(hp)},
            {'name': 'Kickされた回数', 'value': '{}回'.format(kick)}
        ]
        await self.progress_window.response_edit(interaction=interaction)

    async def back_members(self, interaction: discord.Interaction):
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.MEMBERS)
        await self.progress_window.response_edit(interaction=interaction)


class Progress(base.Command):
    def __init__(self, bot: discord.ext.commands.Bot):
        super().__init__(bot=bot)
        self.printer.start()
        print(self.printer.next_iteration)
        self.parser.add_argument('comment')

        self.database_connector = psycopg2.connect(DATABASE_URL)
        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS progress (channel_id BIGINT, interval INTERVAL, time TIME, timestamp TIMESTAMP, prev_timestamp TIMESTAMP, prev_prev_timestamp TIMESTAMP, member_ids BIGINT[])')
            self.database_connector.commit()
        self.change_printer_interval()

        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS progress_members (guild_id BIGINT, user_id BIGINT, total INTEGER, streak INTEGER, escape INTEGER, denied INTEGER, hp INTEGER, kick INTEGER)'
            )
            self.database_connector.commit()

        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS progress_reports (channel_id BIGINT, message_id BIGINT, timestamp TIMESTAMP)'
            )
            self.database_connector.commit()

    def change_printer_interval(self):
        print('changed printer interval.')
        with self.database_connector.cursor() as cur:
            cur.execute('SELECT time FROM progress')
            results = cur.fetchall()
        new_time = DEFAULT_TIMES + [_time.replace(tzinfo=ZONE_TOKYO) for _time, in results]
        self.printer.change_interval(time=new_time)
        print(self.printer.time)
        self.printer.restart()

    def calc_status(self, member: discord.Member):
        with self.database_connector.cursor() as cur:
            cur.execute(
                'SELECT channel_id, timestamp, prev_timestamp, prev_prev_timestamp FROM progress WHERE %s IN member_ids',
                (member.id,)
            )

    @commands.command()
    async def progress(self, ctx: commands.Context, *args):
        print('progress was called.')
        print('printer next iteration is {}'.format(self.printer.next_iteration))
        print(self.printer.time)
        try:
            namespace = self.parser.parse_args(args=args)
        except base.commandparser.InputInsufficientRequiredArgumentError:
            self.runners.append(Runner(command=self, channel=ctx.channel, database_connector=self.database_connector))
            await self.runners[len(self.runners) - 1].run()
        else:
            embed = discord.Embed(
                title=namespace.comment, timestamp=datetime.datetime.now(tz=ZONE_TOKYO),
                colour=discord.Colour.green()
            )
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
            embed.set_footer(text='進捗報告')
            message = await ctx.send(embed=embed)
            await message.add_reaction('\N{thinking face}')
            with self.database_connector.cursor() as cur:
                cur.execute(
                    'INSERT INTO progress_reports (channel_id, message_id, timestamp) VALUES (%s, %s, %s)',
                    (ctx.channel.id, message.id, message.created_at)
                )
                self.database_connector.commit()

    @tasks.loop(time=DEFAULT_TIMES)
    async def printer(self):
        print('printer was called.')
        now = datetime.datetime.now(tz=ZONE_TOKYO)
        with self.database_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute('SELECT channel_id, interval, time, timestamp, prev_timestamp, prev_prev_timestamp, member_ids FROM progress')
            results = cur.fetchall()
            self.database_connector.commit()

        for channel_id, interval, _time, timestamp, prev_timestamp, prev_prev_timestamp, member_ids in results:
            if now + datetime.timedelta(minutes=1) < timestamp:
                continue
            print(datetime.datetime.now(tz=ZONE_TOKYO))
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue

            print(channel.name)

            members = [member for member in channel.members if member.id in member_ids and member.id is not self.bot.user.id]
            print([member.name for member in members])

            # 前回のreportの検証
            approved: dict[discord.Member, int] = {member: 0 for member in members}
            denied: dict[discord.Member, int] = {member: 0 for member in members}
            kick_members = []
            with self.database_connector.cursor() as cur:
                cur.execute(
                    'SELECT message_id FROM progress_reports WHERE channel_id = %s AND %s <= timestamp AND timestamp < %s', (
                        channel_id,
                        prev_timestamp,
                        prev_prev_timestamp
                    )
                )
                message_ids = cur.fetchall()
                self.database_connector.commit()
            for message_id, in message_ids:
                try:
                    message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    continue
                else:
                    if message.author in members:
                        reactions = [
                            reaction for reaction in message.reactions if type(
                                reaction.emoji) == str and reaction.emoji == THINKING_FACE.text]
                        if len(reactions) == 1:
                            if reactions[0].count < len(members) / 2:
                                approved[message.author] += 1
                            else:
                                denied[message.author] += 1
                        else:
                            raise ValueError
            with self.database_connector.cursor() as cur:
                for member in members:
                    cur.execute(
                        'SELECT streak, hp FROM progress_members WHERE guild_id = %s AND user_id = %s',
                        (channel.guild.id, member.id)
                    )
                    result = cur.fetchone()
                    if result is None:
                        continue
                    else:
                        streak, hp = result
                    if approved[member] > 0:
                        cur.execute(
                            'UPDATE progress_members SET total = total + %s, streak = streak + 1, denied = denied + %s, hp = hp + %s WHERE guild_id = %s AND user_id = %s', (
                                approved[member], denied[member], 1 if (streak + 1) % HEAL_HP_PER_STREAK == 0 else 0,
                                channel.guild.id, member.id
                            )
                        )
                        self.database_connector.commit()
                    else:
                        if hp - 1 <= 0:
                            kick_members.append(member)
                            next_hp = MAX_HP
                            next_kick = 1
                        else:
                            next_hp = hp - 1
                            next_kick = 0
                        if denied[member] > 0:
                            cur.execute(
                                'UPDATE progress_members SET streak = 0, denied = denied + %s, hp = %s, kick = kick + %s WHERE guild_id = %s AND user_id = %s',
                                (denied[member], next_hp, next_kick, channel.guild.id, member.id)
                            )
                            self.database_connector.commit()
                        else:
                            cur.execute(
                                'UPDATE progress_members SET streak = 0, escape = escape + 1, hp = %s, kick = kick + %s WHERE guild_id = %s AND user_id = %s',
                                (next_hp, next_kick, channel.guild.id, member.id)
                            )
                            self.database_connector.commit()

            # 今回のreportの検証
            reports: dict[discord.Member, int] = {member: 0 for member in members}
            with self.database_connector.cursor() as cur:
                cur.execute(
                    'SELECT message_id FROM progress_reports WHERE channel_id = %s AND %s <= timestamp AND timestamp < %s', (
                        channel_id,
                        datetime.datetime.combine(date=prev_timestamp, time=_time, tzinfo=ZONE_TOKYO),
                        datetime.datetime.combine(date=timestamp, time=_time, tzinfo=ZONE_TOKYO)
                    )
                )
                results = cur.fetchall()
                message_ids = [result[0] for result in results]
                self.database_connector.commit()
            for message_id in message_ids:
                try:
                    message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    print('Not Found')
                    continue
                else:
                    print(message.embeds[0].author)
                    if message.embeds[0].author in members:
                        reports[message.embeds[0].author] += 1

            embeds = []
            # kick
            if len(kick_members) > 0:
                invite = await channel.create_invite(reason='進捗報告を怠ったためにKickしたため。')
                member_names = ''
                failed = []
                for member in kick_members:
                    print(member.name)
                    member_names = '{0} {1}'.format(member_names, member.name)
                    try:
                        await member.kick(reason='進捗報告を怠ったため。')
                    except discord.Forbidden:
                        failed.append(member)
                    else:
                        await member.send(content=invite.url)
                embed = discord.Embed(title='Good Bye!!', description=member_names, colour=discord.Colour.red())
                embed.set_thumbnail(
                    url='https://em-content.zobj.net/thumbs/240/twitter/322/rolling-on-the-floor-laughing_1f923.png'
                )
                if len(failed) > 0:
                    failed_names = failed[0].name
                    for i in range(1, len(failed)):
                        failed_names = '{0}, {1}'.format(failed_names, failed[i])
                    embed.add_field(name='権限不足でKickできなかったメンバー', value=failed_names)
                embeds.append(embed)


            next_timestamp = datetime.datetime.combine(date=datetime.datetime.now(tz=ZONE_TOKYO).date(),
                                                       )



            # 進捗催促
            print(reports)
            if 0 in reports.values():
                mentions = ''
                for member in [member for member in reports.keys() if reports[member] == 0]:
                    mentions = '{0} {1}'.format(mentions, member.name)
                embed = discord.Embed(title='進捗どうですか??', description=mentions, colour=discord.Colour.orange())
                embed.set_footer(text='次回は{}です。'.format(
                    datetime.datetime.combine(date=(date + interval), time=_time).strftime('%Y年%m月%d日%H時%M分'))
                )
                embeds.append(embed)
            else:
                embed = discord.Embed(title='全員報告済み!!', colour=discord.Colour.blue())
                embeds.append(embed)

            await channel.send(embeds=embeds)

            # channelの情報の更新
            with self.database_connector.cursor() as cur:
                cur.execute(
                    'UPDATE progress SET date = %s, prev_date = %s, prev_prev_date = %s WHERE channel_id = %s',
                    (date + interval, date, prev_date, channel_id)
                )
                self.database_connector.commit()


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(Progress(bot=bot))
