from __future__ import annotations

from typing import TYPE_CHECKING, Self

import discord

if TYPE_CHECKING:
    from .._types import Interaction


class ReportsModal(discord.ui.Modal, title='Bug Report'):
    text = discord.ui.TextInput(
        label='Enter your report', style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            'Your report has been submitted.', ephemeral=True
        )
