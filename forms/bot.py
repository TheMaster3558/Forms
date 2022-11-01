import json
import traceback
import sys
from typing import Any, Awaitable, Callable, TypeVar

import aiofiles
import aiointeractions
import asyncpg
import discord
from discord.ext import commands

from .database import init_db
from .finish_form import check_database
from .commands.help import HelpCommand


R = TypeVar('R')


async def add_brackets_to_config() -> None:
    async with aiofiles.open('./forms/config.json', 'w') as f:
        await f.write('{}')


async def get_config_data() -> dict[str, Any]:
    async with aiofiles.open('./forms/config.json', 'r') as f:
        raw = await f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        await add_brackets_to_config()
        return await get_config_data()


async def write_config_data(data: dict[str, Any]) -> None:
    dumped = json.dumps(data, indent=4)
    async with aiofiles.open('./forms/config.json', 'w') as f:
        await f.write(dumped)


class FormsBot(commands.Bot):
    pool: asyncpg.Pool

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=HelpCommand(),
            description='Make forms in your server!',
        )

        self.app = aiointeractions.InteractionsApp(self)

    async def setup_hook(self) -> None:
        await self.load_extension('forms.commands')
        await self.load_extension('forms.finish_form')
        await self.load_extension('forms.views')
        await self.load_extension('jishaku')
        check_database.start(self)

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
        try:
            data = await get_config_data()
            token: str = data['token']
            host: str = data['host']
            port: int = data['port']
            user: str = data['user']
            password: str = data['password']
        except KeyError as e:
            raise Exception(f'Missing key in config file: {e.args[0]}') from e

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
