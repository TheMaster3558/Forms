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


class ReportsView(discord.ui.View):
    text: str

    def __init__(self, creator: discord.abc.Snowflake):
        super().__init__(timeout=None)
        self.creator = creator

    async def interaction_check(self, interaction: Interaction) -> bool:
        return self.creator == interaction.user

    @discord.ui.button(label='Start')
    async def start_modal(
        self, interaction: Interaction, button: discord.ui.Button[Self]
    ) -> None:
        modal = ReportsModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.text = modal.text.value

        self.start_modal.disabled = True
        await interaction.message.edit(view=self)
        self.stop()
