from __future__ import annotations

import json
import traceback
import os
import sys
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

import aiofiles
import aiointeractions
import asyncpg
import discord
from discord.ext import commands

from .app import get_app
from .constants import CONFIG_PATH
from .database import init_db
from .finish_form import check_database
from .commands.help import HelpCommand

if TYPE_CHECKING:
    from ._types import ConfigData


R = TypeVar('R')


async def add_brackets_to_config() -> None:
    async with aiofiles.open(CONFIG_PATH, 'w') as f:
        await f.write('{}')


async def get_config_data() -> ConfigData:
    async with aiofiles.open(CONFIG_PATH, 'r') as f:
        raw = await f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        await add_brackets_to_config()
        return await get_config_data()


async def write_config_data(data: ConfigData) -> None:
    dumped = json.dumps(data, indent=4)
    async with aiofiles.open(CONFIG_PATH, 'w') as f:
        await f.write(dumped)


class FormsBot(commands.Bot):
    error_channel: discord.abc.Messageable
    reports_channel: discord.abc.Messageable

    pool: asyncpg.Pool

    config_data: ConfigData
    app_commands: dict[str, discord.app_commands.AppCommand]

    def __init__(self) -> None:
        intents = discord.Intents(guilds=True, messages=True)
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=HelpCommand(),
            description='**Forms** is a Discord Bot that helps you easily create forms!',
        )
        self.interactions_app = aiointeractions.InteractionsApp(
            self, route='/api/interactions', app=get_app()
        )
        self.interactions_app.app['bot'] = self

    async def setup_hook(self) -> None:
        self.app_commands = {
            command.name: command for command in await self.tree.fetch_commands()
        }

        await self.load_extension('forms.commands')
        await self.load_extension('forms.errors')
        await self.load_extension('forms.finish_form')
        await self.load_extension('forms.views')
        await self.load_extension('jishaku')
        check_database.start(self)

        self.loop.create_task(self.set_channels(self.config_data))  # prevents one api call
        self.pool = await asyncpg.create_pool(
            host=self.config_data['host'], port=self.config_data['port'], user=self.config_data['user'], password=self.config_data['password']
        )
        await init_db(self.pool)

    async def set_channels(self, data: ConfigData) -> None:
        await self.wait_until_ready()

        if channel_id := data.get('error_channel'):
            self.error_channel = await self.getch(self.fetch_channel, channel_id)
        else:
            self.error_channel = self.application.owner

        if channel_id := data.get('reports_channel'):
            self.reports_channel = await self.getch(self.fetch_channel, channel_id)
        else:
            self.reports_channel = self.application.owner

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        try:
            await super().load_extension(name, package=package)
        except commands.ExtensionError as exc:
            print(f'Failed to load extension: {name}', file=sys.stderr)
            traceback.print_exception(exc, file=sys.stderr)

    async def getch(self, fetch: Callable[[int], Awaitable[R]], obj_id: int) -> R:
        get: Callable[[int], R] = getattr(self, fetch.__name__.replace('fetch', 'get'))
        return get(obj_id) or await fetch(obj_id)

    async def login(self, *_: Any) -> None:
        self.config_data = await get_config_data()
        await super().login(self.config_data['token'])

    async def run_with_gateway(self, reconnect: bool = True) -> None:
        async with self:
            await self.login()
            await self.connect(reconnect=reconnect)

    async def run_with_web(self):
        async with self:
            await self.interactions_app.start('')  # token is grabbed from config file

    async def close(self) -> None:
        await self.pool.close()
        await super().close()
