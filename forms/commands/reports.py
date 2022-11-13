from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from ..constants import ERROR_COLOR
from ..views import ReportsModal

if TYPE_CHECKING:
    from .._types import Interaction


@app_commands.command(
    name='report', description='Report a bug. This is not a support command.'
)
async def report_command(interaction: Interaction) -> None:
    modal = ReportsModal()
    await interaction.response.send_modal(modal)
    await modal.wait()

    embed = discord.Embed(
        title='A report has been submitted',
        description=modal.text.value,
        timestamp=discord.utils.utcnow(),
        color=ERROR_COLOR,
    )
    embed.set_author(
        name=interaction.user, icon_url=interaction.user.display_avatar.url
    )
    await interaction.client.reports_channel.send(embed=embed)
