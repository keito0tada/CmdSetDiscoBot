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
TIME = datetime.time(hour=4, minute=12, tzinfo=ZONE_TOKYO)
MAX_HP = 5


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
        self.runner.interval_days = int(self.values[0][0])
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
            {'title': '進捗報告 監視', 'description': '設定したチャンネルに進捗報告があるか監視します。指定した期間内に報告がない場合はメンションが飛びます。また一定回数報告がない場合はこのサーバーからBanされます。'},
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
        self.interval_days: Optional[int] = None
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
            cur.execute('SELECT interval_days, hour, minute, date FROM progress WHERE channel_id = %s',
                        (self.chosen_channel.id,))
            results = cur.fetchall()
            self.database_connector.commit()
        if len(results) == 0:
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.ADD)
            self.progress_window.embed_dict['title'] = '追加 #{}'.format(self.chosen_channel.name)
        elif len(results) == 1:
            self.interval_days = results[0][0]
            self.prev_hour = results[0][1]
            self.hour = self.prev_hour
            self.prev_minute = results[0][2]
            self.minute = self.prev_minute
            self.next_date = results[0][3]
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.EDIT)
            self.progress_window.embed_dict['title'] = '変更 #{}'.format(self.chosen_channel.name)
            self.progress_window.embed_dict['fields'] = [
                {'name': '送信する間隔', 'value': '{}日ごと'.format(self.interval_days)},
                {'name': '送信する時刻', 'value': '{0}時{1}分'.format(self.hour, self.minute)},
                {'name': '次に送信される日付', 'value': str(self.next_date)}
            ]
        await self.progress_window.response_edit(interaction=interaction)

    async def add(self, interaction: discord.Interaction):
        print(self.interval_days)
        print(self.hour)
        print(self.minute)
        print(self.next_date)
        if self.interval_days is None or self.hour is None or self.minute is None or self.next_date is None:
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.ADD)
            self.progress_window.embed_dict['color'] = 0x8b0000
            self.progress_window.embed_dict['fields'] = [{'name': 'エラー', 'value': '要素をすべて選択してください。'}]
        else:
            with self.database_connector.cursor() as cur:
                cur.execute('SELECT channel_id FROM progress WHERE channel_id = %s', (self.chosen_channel.id,))
                results = cur.fetchall()
                if len(results) == 0:
                    cur.execute(
                        'INSERT INTO progress (channel_id, interval_days, hour, minute, date) VALUES (%s, %s, %s, %s, %s)',
                        (self.chosen_channel.id, self.interval_days, self.hour, self.minute, self.next_date))
                else:
                    cur.execute(
                        'UPDATE progress SET interval_days = %s, hour = %s, minute = %s, date = %s WHERE channel_id = %s',
                        (self.interval_days, self.hour, self.minute, self.next_date, self.chosen_channel.id))
                self.database_connector.commit()
            self.command.add_interval(hour=self.hour, minute=self.minute)
            print(self.command.printer.is_running())
            print(self.command.printer.next_iteration)
            self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.ADDED)
            self.progress_window.embed_dict['fields'] = [
                {'name': '送信する間隔', 'value': '{}日ごと'.format(self.interval_days)},
                {'name': '送信する時刻', 'value': '{0}時{1}分'.format(self.hour, self.minute)},
                {'name': '次に送信される日付', 'value': str(self.next_date)}
            ]
        await self.progress_window.response_edit(interaction=interaction)

    async def edit(self, interaction: discord.Interaction):
        with self.database_connector.cursor() as cur:
            cur.execute('SELECT channel_id FROM progress WHERE channel_id = %s', (self.chosen_channel.id,))
            results = cur.fetchall()
            if len(results) == 0:
                cur.execute(
                    'INSERT INTO progress (channel_id, interval_days, hour, minute, date) VALUES (%s, %s, %s, %s, %s)',
                    (self.chosen_channel.id, self.interval_days, self.hour, self.minute, self.next_date))
            else:
                cur.execute(
                    'UPDATE progress SET interval_days = %s, hour = %s, minute = %s, date = %s WHERE channel_id = %s',
                    (self.interval_days, self.hour, self.minute, self.next_date, self.chosen_channel.id))
            self.database_connector.commit()
        self.command.delete_interval(hour=self.prev_hour, minute=self.prev_minute)
        self.command.add_interval(hour=self.hour, minute=self.minute)
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.EDITED)
        self.progress_window.embed_dict['fields'] = [
            {'name': '送信する間隔', 'value': '{}日ごと'.format(self.interval_days)},
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
            cur.execute('SELECT total, streak, escape, hp, ban FROM progress_members WHERE user_id = %s', (values[0].id,))
            results = cur.fetchall()
            self.database_connector.commit()
        total = 0
        streak = 0
        escape = 0
        hp = MAX_HP
        ban = 0
        if len(results) == 0:
            with self.database_connector.cursor() as cur:
                cur.execute('INSERT INTO progress_members (user_id, total, streak, escape, hp, ban) VALUES (%s, %s, %s, %s, %s, %s)',
                            (values[0].id, total, streak, escape, hp, ban))
                self.database_connector.commit()
        elif len(results) == 1:
            total, streak, escape, hp, ban = results[0]
        self.progress_window.set_pattern(pattern_id=ProgressWindow.WindowID.MEMBER)
        self.progress_window.embed_dict['title'] = '*{}*'.format(values[0].name)
        self.progress_window.embed_dict['thumbnail'] = {'url': values[0].display_avatar.url}
        self.progress_window.embed_dict['fields'] = [
            {'name': '報告回数', 'value': '{}回'.format(total)},
            {'name': '現在の連続回数', 'value': '{}回'.format(streak)},
            {'name': '報告忘れ回数', 'value': '{}回'.format(escape)},
            {'name': 'Banされるまでの残り回数', 'value': '{}回'.format(hp)},
            {'name': 'Banされた回数', 'value': '{}回'.format(ban)}
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

        self.database_connector = psycopg2.connect(DATABASE_URL)
        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS progress (channel_id BIGINT, interval_days SMALLINT, hour SMALLINT, minute SMALLINT, date DATE)')
            self.database_connector.commit()
        with self.database_connector.cursor() as cur:
            cur.execute('SELECT hour, minute FROM progress')
            results = cur.fetchall()
            self.database_connector.commit()
        new_times = [TIME]
        for hour, minute in results:
            new_times.append(datetime.time(hour=hour, minute=minute, tzinfo=ZONE_TOKYO))
        self.printer.change_interval(time=new_times)

        with self.database_connector.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS progress_members (user_id BIGINT, total INTEGER, streak INTEGER, escape INTEGER, hp INTEGER, ban INTEGER)'
            )
            self.database_connector.commit()

    def delete_interval(self, hour: int, minute: int):
        times = []
        for time in self.printer.time:
            if time.hour is not hour or time.minute is not minute:
                times.append(time)
        self.printer.change_interval(time=times)
        print(self.printer.time)

    def add_interval(self, hour: int, minute: int):
        self.printer.change_interval(
            time=self.printer.time + [datetime.time(hour=hour, minute=minute, tzinfo=ZONE_TOKYO)])
        print(self.printer.time)
        self.printer.restart()
        print(self.printer.time)

    @commands.command()
    async def progress(self, ctx: commands.Context):
        print(self.printer.time)
        self.runners.append(Runner(command=self, channel=ctx.channel, database_connector=self.database_connector))
        await self.runners[len(self.runners) - 1].run()

    @tasks.loop(time=TIME)
    async def printer(self):
        with self.database_connector.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute('SELECT channel_id, interval_days, hour, minute, date FROM progress')
            results = cur.fetchall()
            self.database_connector.commit()

        now = datetime.datetime.now(tz=ZONE_TOKYO)
        today = now.date()
        updates: List[tuple] = []
        for channel_id, intervals_days, hour, minute, date in results:
            called_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=ZONE_TOKYO)
            print('////////////////////////')
            print(intervals_days)
            print(hour)
            print(minute)
            print(date)
            print(called_time)
            if today >= date and now >= called_time:
                channel = self.bot.get_channel(channel_id)
                members = channel.members
                start_time = now - datetime.timedelta(days=intervals_days)
                async for message in channel.history(after=start_time):
                    if message.author in members:
                        members.remove(message.author)
                if len(members) > 0:
                    mentions = ''
                    for member in members:
                        mentions = '{0} {1}'.format(mentions, member.mention)
                    await channel.send(embed=discord.Embed(
                        title='進捗どうですか？', description=mentions
                    ))
                updates.append((date + datetime.timedelta(days=intervals_days), channel_id))

        with self.database_connector.cursor() as cur:
            for update in updates:
                cur.execute('UPDATE progress SET date = %s WHERE channel_id = %s', update)
            self.database_connector.commit()


async def setup(bot: discord.ext.commands.Bot):
    await bot.add_cog(Progress(bot=bot))
