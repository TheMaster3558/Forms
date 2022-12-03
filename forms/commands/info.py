from __future__ import annotations

import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands

from ..constants import COLOR
from ..views import LinksView

if TYPE_CHECKING:
    from .._types import Interaction


@app_commands.command(name='info', description='Get information about the bot.')
async def info_command(interaction: Interaction) -> None:
    embed = discord.Embed(
        title=f'{interaction.client.user.name}',
        description=interaction.client.description,
        timestamp=discord.utils.utcnow(),
        color=COLOR,
    )
    embed.set_thumbnail(url=interaction.client.user.avatar.url)
    embed.add_field(name='Creator', value=interaction.client.application.owner.name)
    embed.add_field(
        name='Bot Created',
        value=discord.utils.format_dt(interaction.client.user.created_at, style='R'),
    )

    view = LinksView(interaction.client)
    await interaction.response.send_message(
        embed=embed, view=view if view.children else None
    )


@app_commands.command(name='ping', description='Pong!')
async def ping_command(interaction: Interaction) -> None:
    embed = discord.Embed(title='Pong!', color=COLOR)
    if latency := interaction.client.latency:
        rounded = int(latency * 1000)
        embed.add_field(name='Gateway', value=f'{rounded}ms')

    embed.add_field(name='HTTP', value='Pending...')

    start = time.time()
    await interaction.response.send_message(embed=embed)
    end = int((time.time() - start) * 1000)

    embed.remove_field(1)
    embed.add_field(name='HTTP', value=f'{end}ms')
    await interaction.edit_original_response(embed=embed)
