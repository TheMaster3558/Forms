from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord import app_commands

from ..constants import COLOR
from ..database import create_form, get_form_data
from ..finish_form import finish_form
from ..views import FormView, QuestionsView

if TYPE_CHECKING:
    from ..bot import FormsBot


def check_channel_permissions(
    channel: discord.TextChannel, me: discord.Member
) -> str | None:
    if not channel.permissions_for(me).send_messages:
        return f'I ned permission to send messages in {channel.mention}.'


@commands.hybrid_command(name='form', description='Create a form!')
@app_commands.describe(
    name='The name of the form',
    finishes_in='The hours to finish the form in',
    anonymous='Whether the form is anonymous',
)
async def form_create_command(
    ctx: commands.Context[FormsBot],
    name: str,
    channel: discord.TextChannel,
    finishes_in: app_commands.Range[float, 0, 168] = 1,
    responses_channel: discord.TextChannel = None,
    anonymous: bool = False,
) -> None:
    if needs_permissions := check_channel_permissions(channel, ctx.me):
        await ctx.send(needs_permissions, ephemeral=True)
    if responses_channel and (
        needs_permissions := check_channel_permissions(responses_channel, ctx.me)
    ):
        await ctx.send(needs_permissions, ephemeral=True)

    embed = discord.Embed(
        title=name, description='**Form questions shown below**', color=COLOR
    )
    view = QuestionsView(ctx.author)
    await ctx.send(embed=embed, view=view)
    await view.wait()

    if not view.items:
        await ctx.send('No questions entered. Cancelling.', ephemeral=True)
        return

    finishes_dt = discord.utils.utcnow() + datetime.timedelta(hours=finishes_in)
    finishes_string = discord.utils.format_dt(finishes_dt, style='R')

    embed = discord.Embed(
        title=name, description=f'Finishes in {finishes_string}', color=COLOR
    )
    if anonymous:
        embed.set_footer(text='This form is anonymous')
    else:
        embed.set_footer(text='This form is not anonymous')

    view = FormView(view.items, finishes_at=finishes_dt.timestamp(), loop=ctx.bot.loop)
    message = await channel.send(embed=embed, view=view)
    view.message = message

    if not responses_channel:
        await ctx.send(
            'Data will be DMed to you. Make sure to turn on DMs!', ephemeral=True
        )

    await create_form(
        ctx.bot.pool,
        name=name,
        form_id=message.id,
        channel_id=channel.id,
        response_channel_id=responses_channel and responses_channel.id,
        creator_id=ctx.author.id,
        finishes_at=finishes_dt,
        questions=view.items,
    )


@commands.hybrid_command(name='finish', description='Finish a form early.')
@app_commands.describe(
    message='The link or ID to the message that you can start the form from',
    send_here='Whether to send the results in this channel or the channel set in /form',
)
async def form_finish_command(
    ctx: commands.Context[FormsBot], message: discord.Message, send_here: bool = False
):
    await ctx.defer(ephemeral=True)
    pool = ctx.bot.pool
    form = await get_form_data(pool, form_id=message.id)

    if form is None:
        await ctx.send('That form could not be found.', ephemeral=True)
        return
    if form['creator_id'] != ctx.author.id:
        await ctx.send('Only the creator of the form can finish it early.')
        return

    channel = ctx.channel if send_here else None
    await finish_form(
        ctx.bot,
        form_id=message.id,
        form_name=form['form_name'],
        creator_id=form['creator_id'],
        channel=channel,
    )
    await ctx.send('Form successfully finished!', ephemeral=True)
