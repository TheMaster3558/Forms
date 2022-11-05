from __future__ import annotations

from typing import TYPE_CHECKING, Self

import discord

if TYPE_CHECKING:
    from .._types import Item


class QuestionsModal(discord.ui.Modal, title='Create a Question'):
    question_name = discord.ui.TextInput(label='Enter the name of the question')

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class QuestionRemoveSelect(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.view.stop()


class QuestionsView(discord.ui.View):
    def __init__(self, creator: discord.abc.Snowflake) -> None:
        super().__init__(timeout=600)
        self.items: list[Item] = []
        self.creator = creator

    @staticmethod
    async def send_question_create_modal(
        interaction: discord.Interaction,
    ) -> QuestionsModal:
        modal = QuestionsModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        return modal

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.creator == interaction.user

    @discord.ui.button(
        label='Add Short Answer Question', style=discord.ButtonStyle.gray
    )
    async def short_answer_question(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        modal = await self.send_question_create_modal(interaction)
        self.items.append(
            discord.ui.TextInput(
                label=modal.question_name.value, style=discord.TextStyle.short
            )
        )
        embed = interaction.message.embeds[0].add_field(
            name=modal.question_name.value, value=f'Type: short'
        )
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label='Add Paragraph Question', style=discord.ButtonStyle.gray)
    async def long_answer_question(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        modal = await self.send_question_create_modal(interaction)
        self.items.append(
            discord.ui.TextInput(
                label=modal.question_name.value, style=discord.TextStyle.long
            )
        )
        embed = interaction.message.embeds[0].add_field(
            name=modal.question_name.value, value=f'Type: paragraph'
        )
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label='Finish', style=discord.ButtonStyle.green)
    async def finish_questions(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        await interaction.response.defer()
        self.stop()

        child: discord.ui.Button
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label='Remove Question', style=discord.ButtonStyle.red)
    async def remove_question(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        options: list[discord.SelectOption] = []
        for item in self.items:
            if isinstance(item, discord.ui.TextInput):
                options.append(discord.SelectOption(label=item.label))  # type: ignore
            elif isinstance(item, discord.ui.Select):
                options.append(discord.SelectOption(label=item.placeholder))

        select = QuestionRemoveSelect(options=options)
        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        question = select.values[0]
        for index, item in enumerate(self.items):
            if isinstance(item, discord.ui.TextInput) and item.label == question:
                del self.items[index]
            elif isinstance(item, discord.ui.Select) and item.placeholder == question:
                del self.items[index]
            else:
                continue
            break

        embed = interaction.message.embeds[0]
        for index, field in enumerate(embed.fields):
            if field.name == question:
                embed.remove_field(index)
                break
        await interaction.message.edit(embed=embed)
