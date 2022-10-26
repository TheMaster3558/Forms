import json
import traceback
import sys

import aiofiles
import asyncpg
import discord
from discord.ext import commands

from .database import init_db
from .finish_form import check_database
from .help import HelpCommand


async def add_brackets_to_config() -> None:
    async with aiofiles.open('./forms/config.json', 'w') as f:
        await f.write('{}')


async def get_config_data() -> dict[str, str | int]:
    async with aiofiles.open('./forms/config.json', 'r') as f:
        raw = await f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        await add_brackets_to_config()
        return await get_config_data()


async def write_config_data(data: dict[str, str | int]) -> None:
    dumped = json.dumps(data, indent=4)
    async with aiofiles.open('./forms/config.json', 'w') as f:
        await f.write(dumped)


def get_individual_data(
    name: str, data: dict[str, str | int], default: str | int | None
) -> str | int:
    if name not in data and default is None:
        raise TypeError(f'No {name} provided, add it in the config file')
    elif default:
        return default
    return data[name]


class FormsBot(commands.Bot):
    pool: asyncpg.Pool

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=HelpCommand(),
        )

    async def setup_hook(self) -> None:
        await self.load_extension('forms.commands')
        await self.load_extension('jishaku')
        check_database.start(self)

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        try:
            await super().load_extension(name, package=package)
        except commands.ExtensionError as exc:
            print(f'Failed to load extension: {name}', file=sys.stderr)
            traceback.print_exception(exc, file=sys.stderr)

    async def login(
        self,
        token: str | None = None,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        data = await get_config_data()
        token = get_individual_data('token', data, token)
        host = get_individual_data('host', data, host)
        port = get_individual_data('port', data, port)
        user = get_individual_data('user', data, user)
        password = get_individual_data('password', data, password)

        self.pool = await asyncpg.create_pool(
            host=host, port=port, user=user, password=password
        )
        await init_db(self.pool)

        await super().login(token)

    async def start(self, token: str | None = None, *, reconnect: bool = True) -> None:
        await self.login(token)
        await self.connect(reconnect=reconnect)

    async def close(self) -> None:
        await self.pool.close()
        await super().close()
