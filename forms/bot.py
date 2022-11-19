from __future__ import annotations

import asyncio
import json
import traceback
import sys
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

import aiofiles
import aiointeractions
import asyncpg
import discord
from discord.ext import commands
from pyngrok import ngrok

from .app import get_app
from .constants import CONFIG_PATH
from .database import init_db
from .finish_form import check_database

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
    port: int
    pool: asyncpg.Pool
    config_data: ConfigData
    app_commands: dict[str, discord.app_commands.AppCommand]
    set_channels_task: asyncio.Task[None]

    def __init__(self) -> None:
        intents = discord.Intents(guilds=True, messages=True)
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            description='**Forms** is a Discord Bot that helps you easily create forms!',
        )
        self.interactions_app: aiointeractions.InteractionsApp = (
            aiointeractions.InteractionsApp(
                self, route='/api/interactions', app=get_app()
            )
        )
        self.interactions_app.app['bot'] = self
        self.use_ngrok: bool = False

    async def setup_hook(self) -> None:
        self.app_commands = {
            command.name: command for command in await self.tree.fetch_commands()
        }

        await self.load_extension('forms.commands')
        await self.load_extension('forms.errors')
        await self.load_extension('forms.finish_form')
        await self.load_extension('jishaku')
        check_database.start(self)

        self.set_channels_task = self.loop.create_task(
            self.set_channels(self.config_data)
        )  # prevents one api call
        self.loop.create_task(self.set_website())
        self.pool = await asyncpg.create_pool(
            host=self.config_data['host'],
            port=self.config_data['port'],
            user=self.config_data['user'],
            password=self.config_data['password'],
        )
        await init_db(self.pool)

    async def set_channels(self, data: ConfigData) -> None:
        await asyncio.sleep(3)
        if not self.interactions_app.is_running():
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

    async def set_website(self) -> None:
        await self.set_channels_task
        if self.use_ngrok:
            ngrok.set_auth_token(self.config_data['ngrok_auth_token'])
            tunnel = ngrok.connect(self.port)
            self.config_data['website_url'] = tunnel.public_url
        await self.error_channel.send(self.config_data['website_url'])

    async def run_with_web(self, port: int = 8080) -> None:
        async with self:
            self.port = port
            await self.interactions_app.start('', port=port)  # token is grabbed from config file

    async def close(self) -> None:
        await self.pool.close()
        await super().close()
