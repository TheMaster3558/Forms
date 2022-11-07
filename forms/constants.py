from __future__ import annotations

from typing import TYPE_CHECKING

import discord

# sphinx doesn't support typing.Final due to python version
if TYPE_CHECKING:
    from typing import Final

COLOR: Final[int] = 0x2F3136
CONFIG_PATH: Final[str] = './config.json'
DOCS_LINK: Final[str] = 'https://formsdiscordbot.readthedocs.io/'
ERROR_COLOR: Final[discord.Color] = discord.Color.red()
INVITE_URL: Final[
    str
] = 'https://discord.com/api/oauth2/authorize?client_id=1032797461342863431&permissions=2048&scope=bot%20applications.commands'
