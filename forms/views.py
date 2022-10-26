from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Self

import discord

from .constants import COLOR
from .database import get_forms, get_responses_channel, get_questions, insert_responses

if TYPE_CHECKING:
    from .bot import FormsBot


class QuestionsModal(discord.ui.Modal, title='Create a Question'):
    form_title = discord.ui.TextInput(label='Enter the name of the question')

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class QuestionRemoveSelect(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.view.stop()


class QuestionsView(discord.ui.View):
    def __init__(self, creator: discord.abc.Snowflake):
        super().__init__(timeout=600)
        self.data: dict[str, int] = {}
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
        self.data[modal.form_title.value] = int(discord.TextStyle.short)
        embed = interaction.message.embeds[0].add_field(
            name=modal.form_title.value, value=f'Type: short'
        )
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label='Add Paragraph Question', style=discord.ButtonStyle.gray)
    async def long_answer_question(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        modal = await self.send_question_create_modal(interaction)
        self.data[modal.form_title.value] = int(discord.TextStyle.long)
        embed = interaction.message.embeds[0].add_field(
            name=modal.form_title.value, value=f'Type: paragraph'
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
        options = [
            discord.SelectOption(label=name, description=f'Type: {discord.TextStyle(input_type).name}')  # type: ignore
            for name, input_type in self.data.items()
        ]
        select = QuestionRemoveSelect(options=options)
        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        question = select.values[0]
        del self.data[question]

        embed = interaction.message.embeds[0]
        for index, field in enumerate(embed.fields):
            if field.name == question:
                embed.remove_field(index)
                break
        await interaction.message.edit(embed=embed)


class FormModal(discord.ui.Modal):
    def __init__(self, title: str, data: dict[str, int], form_id: int):
        super().__init__(title=title)
        for question, input_type in data.items():
            text_input = discord.ui.TextInput(
                label=question, style=discord.TextStyle(input_type)  # type: ignore
            )
            self.add_item(text_input)
        self.form_id = form_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            'Your response has been recorded', ephemeral=True
        )

        pool = interaction.client.pool  # type: ignore
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
            pool,
            response_time=int(discord.utils.utcnow().timestamp()),
            user=str(interaction.user) if not anonymous else None,
            question_ids=question_ids,
            responses=responses,
        )

        channel_id = await get_responses_channel(pool, form_id=interaction.message.id)
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
            except discord.NotFound:
                return
            await channel.send(embed=embed)


class FormView(discord.ui.View):
    message: discord.Message

    def __init__(
        self, data: dict[str, int], *, finishes_at: int, loop: asyncio.AbstractEventLoop
    ):
        super().__init__(timeout=None)
        self.data = data
        loop.call_at(finishes_at, loop.create_task, self.disable())

    async def disable(self) -> None:
        self.start_form.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(label='Start Form', style=discord.ButtonStyle.gray, custom_id='start_form')
    async def start_form(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ) -> None:
        title = interaction.message.embeds[0].title
        modal = FormModal(title, self.data, interaction.message.id)
        await interaction.response.send_modal(modal)


async def add_persistent_views(bot: FormsBot) -> None:
    pool = bot.pool

    for form in await get_forms(pool):
        form = form['form_id']
        data: dict[str, int] = {question['question_name']: question['input_type'] for question in await get_questions(pool, form_id=form['form_id'])}
        view = FormView(data, finishes_at=form['finishes_at'], loop=bot.loop)
        bot.add_view(view, message_id=form['form_id'])


async def setup(bot: FormsBot) -> None:
    await add_persistent_views(bot)

