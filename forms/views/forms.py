from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Iterable, Self

import discord

from ..constants import COLOR
from ..database import get_responses_channel, get_permissions, insert_responses

if TYPE_CHECKING:
    from .._types import Interaction, Item


class FormModal(discord.ui.Modal):
    def __init__(self, title: str, items: Iterable[Item], form_id: int) -> None:
        super().__init__(title=title)
        for item in items:
            self.add_item(item)
        self.form_id = form_id

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.send_message(
            'Your response has been recorded', ephemeral=True
        )

        question_ids: list[int] = []
        responses: list[str] = []

        child: discord.ui.TextInput
        for number, child in enumerate(self.children):
            question_id = interaction.message.id + number
            response = child.value
            question_ids.append(question_id)
            responses.append(response)

        anonymous = 'not' not in interaction.message.embeds[0].footer.text
        await insert_responses(
            interaction.client.pool,
            response_time=discord.utils.utcnow(),
            user=str(interaction.user) if not anonymous else None,
            question_ids=question_ids,
            responses=responses,
        )

        channel_id = await get_responses_channel(interaction.client.pool, form_id=interaction.message.id)
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


class FormView(discord.ui.View):
    message: discord.Message

    def __init__(
        self,
        items: Iterable[Item],
        *,
        finishes_at: float,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__(timeout=None)
        self.items = items
        loop.call_at(finishes_at, loop.create_task, self.disable())

    async def disable(self) -> None:
        self.start_form.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(
        label='Start Form', style=discord.ButtonStyle.gray, custom_id='start_form'
    )
    async def start_form(
        self, interaction: Interaction, button: discord.ui.Button[Self]
    ) -> None:
        users, roles, everyone = await get_permissions(
            interaction.client.pool, form_id=interaction.message.id
        )

        if (
            not everyone
            and interaction.user.id not in users
            and not any(role in roles for role in interaction.user._roles)
        ):
            await interaction.response.defer()

        title = interaction.message.embeds[0].title
        modal = FormModal(title, self.items, interaction.message.id)
        await interaction.response.send_modal(modal)
