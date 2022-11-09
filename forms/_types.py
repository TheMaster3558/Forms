from typing import TYPE_CHECKING, NotRequired, TypeAlias, TypedDict

import discord

if TYPE_CHECKING:
    from .bot import FormsBot


Color: TypeAlias = int | discord.Color
Item: TypeAlias = discord.ui.TextInput | discord.ui.Select


class ConfigData(TypedDict):
    token: str
    host: str
    port: int
    user: str
    password: str
    error_channel: NotRequired[int]
    invite_url: NotRequired[str]
    website_url: NotRequired[str]


class Interaction(discord.Interaction):
    if TYPE_CHECKING:
        @property
        def client(self) -> FormsBot:
            ...
