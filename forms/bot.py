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


def assert_config_exists() -> None:
    if not os.path.exists(CONFIG_PATH):
        raise Exception(f'Missing config file {CONFIG_PATH}')


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
    pool: asyncpg.Pool
        
    invite_url: str
    website_url: str

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=HelpCommand(),
            description='**Forms** is a Discord Bot that helps you easily create forms!',
        )
        self.app = aiointeractions.InteractionsApp(
            self, route='/api/interactions', app=get_app()
        )

    async def setup_hook(self) -> None:
        await self.load_extension('forms.commands')
        await self.load_extension('forms.errors')
        await self.load_extension('forms.finish_form')
        await self.load_extension('forms.views')
        await self.load_extension('jishaku')
        check_database.start(self)

    async def set_error_channel(self, data: ConfigData) -> None:
        await self.wait_until_ready()

        if channel_id := data.get('error_channel'):
            self.error_channel = await self.getch(self.fetch_channel, channel_id)
        else:
            self.error_channel = self.application.owner

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
        assert_config_exists()
        try:
            data = await get_config_data()
            token: str = data['token']
            host: str = data['host']
            port: int = data['port']
            user: str = data['user']
            password: str = data['password']
        except KeyError as e:
            raise Exception(f'Missing key in config file: {e.args[0]}') from e
            
        self.invite_url = data.get('invite_url', '')
        self.website_url = data.get('website_url', '')

        self.loop.create_task(self.set_error_channel(data))
        self.pool = await asyncpg.create_pool(
            host=host, port=port, user=user, password=password
        )
        await init_db(self.pool)

        await super().login(token)

    async def run_with_gateway(self, reconnect: bool = True) -> None:
        async with self:
            await self.login()
            await self.connect(reconnect=reconnect)

    async def run_with_web(self):
        async with self:
            await self.app.start('')  # token is grabbed from config file

    async def close(self) -> None:
        await self.pool.close()
        await super().close()
