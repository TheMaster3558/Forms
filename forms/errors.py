from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import discord
from discord import app_commands

from .constants import ERROR_COLOR

if TYPE_CHECKING:
    from ._types import Interaction
    from .bot import FormsBot


async def error_handler(
    interaction: Interaction, error: app_commands.AppCommandError
) -> None:
    embed = discord.Embed(
        title='An unexpected error occurred!',
        description='It has been reported.',
        color=ERROR_COLOR,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

    formatted = '\n'.join(traceback.format_exception(error))
    embed = discord.Embed(
        title='⚠Error⚠', description=f'```py\n{formatted}\n```', color=ERROR_COLOR
    )
    await interaction.client.error_channel.send(embed=embed)


async def setup(bot: FormsBot) -> None:
    bot.tree.error(error_handler)
