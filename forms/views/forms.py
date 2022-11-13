from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import discord

from ..constants import COLOR
from ..database import get_responses_channel, insert_responses

if TYPE_CHECKING:
    from .._types import Interaction, Item


class FormModal(discord.ui.Modal):
    def __init__(self, title: str, items: Iterable[Item]) -> None:
        super().__init__(title=title)
        for item in items:
            self.add_item(item)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.send_message(
            'Your response has been recorded', ephemeral=True
        )

        question_ids: list[str] = []
        responses: list[str] = []

        child: discord.ui.TextInput
        for number, child in enumerate(self.children):
            question_id = f'{interaction.guild.id}{self.title}{number}'
            response = child.value
            question_ids.append(question_id)
            responses.append(response)

        await insert_responses(
            interaction.client.pool,
            response_time=discord.utils.utcnow(),
            user=str(interaction.user),
            question_ids=question_ids,
            responses=responses,
        )

        channel_id = await get_responses_channel(
            interaction.client.pool, form_id=f'{interaction.guild.id}{self.title}'
        )
        if channel_id is not None:
            embed = discord.Embed(timestamp=discord.utils.utcnow(), color=COLOR)
            embed.set_author(
                name=interaction.user, icon_url=interaction.user.display_avatar.url
            )
            for child in self.children:
                embed.add_field(
                    name=child.label, value=discord.utils.escape_markdown(child.value)
                )
            try:
                channel = interaction.guild.get_channel(
                    channel_id
                ) or await interaction.guild.fetch_channel(channel_id)
            except discord.HTTPException:
                return
            await channel.send(embed=embed)
