from typing import NotRequired, TypeAlias, TypedDict

import discord


Item: TypeAlias = discord.ui.TextInput | discord.ui.Select


class ConfigData(TypedDict):
    token: str
    host: str
    port: int
    user: str
    password: str
    error_channel: NotRequired[int]
