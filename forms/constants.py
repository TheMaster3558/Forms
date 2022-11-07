from __future__ import annotations

from typing import TYPE_CHECKING

import discord

# sphinx doesn't support typing.Final due to python version
if TYPE_CHECKING:
    from typing import Final

COLOR: Final[int] = 0x2F3136
CONFIG_PATH: Final[str] = './config.json'
ERROR_COLOR: Final[discord.Color] = discord.Color.red()
