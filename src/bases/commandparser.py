import sys
import typing
from typing import Union
import re
from dataclasses import dataclass
import lark.exceptions
from lark import Lark
from lark import Transformer
import discord
from functools import reduce

from bases import base


class CommandParserError(Exception):
    def __init__(self):
        self.embed: Union[discord.Embed, None] = None

    def send(self, channel: discord.TextChannel):
        channel.send(embed=self.embed)


class SetArgumentError(CommandParserError):
    pass


class SetInvalidArgumentNameError(SetArgumentError):
    pass


class SetDuplicatedArgumentError(SetArgumentError):
    pass


class InputArgumentError(CommandParserError):
    pass


class InputDuplicatedArgumentError(InputArgumentError):
    def __init__(self, arg_name: str):
        super.__init__()
        self.embed = discord.Embed(
            title='エラー', description='同一の引数が複数指定されています。', color=discord.Color.red()
        )
        self.embed.add_field(name='引数名', value=arg_name)


class InputInvalidArgumentNameError(InputArgumentError):
    def __init__(self, arg_name: str):
        super().__init__()
        self.embed = discord.Embed(
            title='エラー', description='不正な引数が指定されています。', color=discord.Color.red()
        )
        self.embed.add_field(name='引数名', value=arg_name)


class InputInsufficientRequiredArgumentError(InputArgumentError):
    def __init__(self, arg_name: str):
        super().__init__()
        self.embed = discord.Embed(
            title='エラー', description='必要な引数が入力されていません。', color=discord.Color.red()
        )
        self.embed.add_field(name='引数名', value=arg_name)


# a class used to parse arguments when commands called
class CommandParser:
    class CommandTransformer(Transformer):
        def statement(self, tree) -> (list, list):
            if len(tree) == 0:
                return [], []
            elif len(tree) == 1:
                if tree[0][0] == 'optionals':
                    return [], tree[0][1]
                else:
                    return tree[0][1], []
            else:
                return tree[0][1], tree[1][1]

        def positionals(self, tree):
            if len(tree) == 1:
                return 'positionals', [tree[0]]
            else:
                tree[0][1].append(tree[1])
                return tree[0]

        def positional(self, tree):
            return tree[0]

        def optionals(self, tree):
            if len(tree) == 1:
                return 'optionals', [tree[0]]
            else:
                tree[0][1].append(tree[1])
                return tree[0]

        def optional(self, tree):
            return [i for i in tree]

        def word(self, tree):
            return tree[0].lower()

        def letter(self, tree):
            return tree[0].lower()

    @dataclass
    class Arg:
        name: str
        required: bool

    @dataclass
    class OptArg(Arg):
        omitted_flag: str

    @dataclass
    class Namespace:
        args: dict

    def __init__(self) -> None:
        self.arguments: dict[str: CommandParser.Arg] = {}
        self.argument_names: list[str] = []
        with open("src/bases/commandparser.lark", encoding="utf-8") as grammar:
            self.parser = Lark(grammar.read())

        self.tree: Union[lark.Tree, None] = None
        self.result = None
        self.namespace: Union[CommandParser.Namespace, None] = None

    @staticmethod
    def _is_arg_name(arg: str) -> bool:
        p = re.compile(r'[a-zA-Z]+')
        return bool(p.fullmatch(arg))

    @staticmethod
    def _is_flag(arg: str) -> bool:
        p = re.compile(r'\-\-[a-zA-Z]+')
        return bool(p.fullmatch(arg))

    @staticmethod
    def _is_omitted_flag(arg: str) -> bool:
        p = re.compile(r'\-[a-zA-Z]')
        return bool(p.fullmatch(arg))

    def _get_positional_arguments(self) -> typing.List[Arg]:
        return [i for i in list(self.arguments.values()) if type(i) is CommandParser.Arg]

    def _get_optional_arguments(self) -> typing.List[OptArg]:
        return [i for i in self.arguments.values() if type(i) is CommandParser.OptArg]

    def add_argument(self, *args: str, required=False):
        assert 1 <= len(args) <= 2
        if len(args) == 1:
            # if add positional argument
            if CommandParser._is_arg_name(args[0]):
                if args[0] in self.argument_names:
                    raise SetDuplicatedArgumentError
                else:
                    self.argument_names.append(args[0])
                    self.arguments[args[0]] = CommandParser.Arg(
                        name=args[0], required=required)

            # if add optional argument without omitted flag
            elif CommandParser._is_flag(args[0]):
                flag = args[0][2:]
                if flag in self.argument_names:
                    raise SetDuplicatedArgumentError
                else:
                    self.argument_names.append(flag)
                    self.arguments[flag] = CommandParser.OptArg(
                        name=flag, omitted_flag='', required=required
                    )
            else:
                raise SetInvalidArgumentNameError

        # if add optional argument with omitted flag
        else:
            if CommandParser._is_flag(args[0]) and CommandParser._is_omitted_flag(args[1]):
                flag = args[0][2:]
                omitted_flag = args[1][1:]
                print(flag)
                print(omitted_flag)
                if flag in self.argument_names or omitted_flag in self.argument_names:
                    raise SetDuplicatedArgumentError
                else:
                    self.argument_names.append(flag)
                    self.argument_names.append(omitted_flag)
                    self.arguments[flag] = CommandParser.OptArg(
                        name=flag, omitted_flag=omitted_flag, required=required
                    )
                    self.arguments[omitted_flag] = self.arguments[flag]

            else:
                raise SetInvalidArgumentNameError

    def analyze_arguments(self):
        self.namespace = CommandParser.Namespace({})
        # analyze positional arguments
        pos_args = self._get_positional_arguments()
        if len(self.result[0]) < len(pos_args):
            raise InputInsufficientRequiredArgumentError(arg_name=pos_args[-1].name)
        else:
            index = 0
            for pos_arg in pos_args:
                if index >= len(pos_args) - 1 and len(self.result[0][index:]) > 1:
                    self.namespace.__dict__[pos_arg.name] = self.result[0][index:]
                    self.namespace.args[pos_arg.name] = self.result[0][index:]
                else:
                    self.namespace.__dict__[pos_arg.name] = self.result[0][index]
                    self.namespace.args[pos_arg.name] = self.result[0][index]
                index += 1

        opt_args = self._get_optional_arguments()
        # check if a user inputted all required args
        for opt_arg in opt_args:
            if opt_arg.required and opt_arg.name not in [i[0] for i in self.result[1]]:
                raise InputInsufficientRequiredArgumentError(arg_name=opt_arg.name)

        # check if a user did not input invalid args
        for inp in self.result[1]:
            if inp[0] not in [i.name for i in opt_args] + [i.omitted_flag for i in opt_args]:
                raise InputInvalidArgumentNameError(arg_name=inp[0])

        # check if a user did not input duplicated args
        for i in self.result[1]:
            if self.result[1].count(i) > 1:
                raise InputDuplicatedArgumentError(arg_name=i[0])

        for inp in self.result[1]:
            self.namespace.__dict__[inp[0]] = inp[1:]
            self.namespace.args[inp[0]] = inp[1:]

    def parse_args(self, args: typing.Tuple[str]) -> Namespace:
        print(args)
        self.tree = self.parser.parse(reduce(lambda x, y: x + ' ' + y, args, ''))
        print(self.tree.pretty())
        self.result = self.CommandTransformer().transform(self.tree)
        print(self.result)
        self.analyze_arguments()
        return self.namespace

    def get_help(self) -> base.Window:
        pass

    def get_help_arg(self, arg: str) -> base.Window:
        pass
