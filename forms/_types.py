from typing import TYPE_CHECKING, Any, Awaitable, Callable, NotRequired, TypeAlias, TypedDict, TypeVar

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from .bot import FormsBot


Color: TypeAlias = int | discord.Color
Item: TypeAlias = discord.ui.TextInput | discord.ui.Select


CoroOrCommandT = TypeVar(
    'CoroOrCommandT',
    bound=commands.Command[None, ..., Any] | Callable[..., Awaitable[None]],
)


class ConfigData(TypedDict):
    token: str
    host: str
    port: int
    user: str
    password: str
    error_channel: NotRequired[int]
    reports_channel: NotRequired[int]
    invite_url: NotRequired[str]
    website_url: NotRequired[str]


class Interaction(discord.Interaction):
    client: FormsBot
