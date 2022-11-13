from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord import app_commands

from ..constants import COLOR
from ..database import (
    can_take_form,
    create_form,
    get_forms,
    get_form_data,
    get_questions,
)
from ..finish_form import finish_form
from ..views import FormModal, QuestionsView, PermissionsView

if TYPE_CHECKING:
    from ..bot import FormsBot
    from .._types import CoroOrCommandT, Interaction


def needs_administrator(command: CoroOrCommandT) -> CoroOrCommandT:
    command = app_commands.default_permissions(administrator=True)(command)

    def predicate(ctx: commands.Context[FormsBot]) -> bool:
        if ctx.interaction:
            return True
        return ctx.channel.permissions_for(ctx.author).administrator

    return commands.check(predicate)(command)


def check_channel_permissions(
    channel: discord.TextChannel, me: discord.Member
) -> str | None:
    if not channel.permissions_for(me).send_messages:
        return f'I need permission to send messages in {channel.mention}.'


@app_commands.command(name='form', description='Create a form!')
@app_commands.describe(
    name='The name of the form',
    finishes_in='The hours to finish the form in',
    responses_channel='The channel to send the form responses in, defaults to DMs',
)
@commands.cooldown(1, 300, commands.BucketType.guild)
@needs_administrator
async def form_create_command(
    interaction: Interaction,
    name: str,
    finishes_in: app_commands.Range[float, 0, 168] = 1,
    responses_channel: discord.TextChannel = None,
) -> None:
    if responses_channel and (
        needs_permissions := check_channel_permissions(
            responses_channel, interaction.guild.me
        )
    ):
        await interaction.response.send_messae(needs_permissions, ephemeral=True)
        return

    questions_embed = discord.Embed(
        title=name, description='**Form questions shown below**', color=COLOR
    )
    questions_view = QuestionsView(interaction.user)
    await interaction.response.send_message(embed=questions_embed, view=questions_view)
    await questions_view.wait()

    if not questions_view.items:
        await interaction.followup.send(
            'No questions entered. Cancelling.', ephemeral=True
        )
        return

    permissions_embed = discord.Embed(title='Who can take this form?', color=COLOR)
    permissions_view = PermissionsView()
    await interaction.followup.send(embed=permissions_embed, view=permissions_view)
    await permissions_view.wait()

    finishes_dt = discord.utils.utcnow() + datetime.timedelta(hours=finishes_in)

    if not responses_channel:
        await interaction.followup.send(
            'Data will be DMed to you. Make sure to turn on DMs!', ephemeral=True
        )

    await create_form(
        interaction.client.pool,
        name=name,
        form_id=f'{interaction.guild.id}{name}',
        guild_id=interaction.guild.id,
        response_channel_id=responses_channel and responses_channel.id,
        creator_id=interaction.user.id,
        finishes_at=finishes_dt,
        questions=questions_view.items,
        allowed_users=permissions_view.users,
        allowed_roles=permissions_view.roles,
        allow_everyone=permissions_view.everyone,
    )


@app_commands.command(name='finish', description='Finish a form early.')
@app_commands.describe(
    form_name='The name of the form',
    send_here='Whether to send the results in this channel',
)
async def form_finish_command(
    interaction: Interaction, form_name: str, send_here: bool = False
) -> None:
    row = await get_form_data(
        interaction.client.pool, form_id=f'{interaction.guild.id}{form_name}'
    )
    try:
        creator_id = row['creator_id']
    except TypeError:
        await interaction.response.send_message(
            'That form could not be found.', ephemeral=True
        )
        return

    if interaction.user.id != creator_id:
        await interaction.response.send_message(
            'Only the creator of the form can finish it.', ephemeral=True
        )

    await finish_form(
        interaction.client,
        form_name=row['form_name'],
        guild=interaction.guild,
        creator_id=creator_id,
        channel=interaction.channel if send_here else None,
    )


@app_commands.command(name='takeform', description='Take a form.')
@app_commands.describe(form_name='The name of the form')
async def take_form_command(interaction: Interaction, form_name: str) -> None:
    try:
        if not await can_take_form(
            interaction.client.pool,
            member=interaction.user,
            form_id=f'{interaction.guild.id}{form_name}',
        ):
            await interaction.response.send_message(
                'You do not have permission to take this form.', ephemeral=True
            )
            return
    except TypeError:
        await interaction.response.send_message(
            'That form could not be found.', ephemeral=True
        )
        return

    items = [
        item
        async for _, item in get_questions(
            interaction.client.pool, form_id=f'{interaction.guild.id}{form_name}'
        )
    ]
    modal = FormModal(form_name, items)
    await interaction.response.send_modal(modal)


@take_form_command.autocomplete('form_name')
async def form_name_autocomplete(
    interaction: Interaction, current: str
) -> list[app_commands.Choice[str]]:
    current = current.lower()
    forms = await get_forms(interaction.client.pool, guild_id=interaction.guild.id)
    options: list[app_commands.Choice[str]] = []

    for form in forms:
        form_name = form['form_name']
        if await can_take_form(
            interaction.client.pool,
            member=interaction.user,
            form_id=f'{interaction.guild.id}{form_name}',
        ) and form_name.lower().startswith(current):
            options.append(app_commands.Choice(name=form_name, value=form_name))
    return options
