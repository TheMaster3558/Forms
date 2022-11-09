from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from ._types import Color


COLOR: Color = 0x2F3136
ERROR_COLOR: Color = discord.Color.red()

CONFIG_PATH: str = './config.json'
