from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING

import discord
from discord.ext import tasks

from .constants import COLOR
from .database import (
    delete_form,
    get_finished,
    get_questions,
    get_responses,
    get_responses_channel,
    get_origin_message
)

if TYPE_CHECKING:
    import asyncpg
    from .bot import FormsBot


async def finish_form(
    bot: FormsBot,
    *,
    form_id: int,
    form_name: str,
    creator_id: int,
    channel: discord.abc.Messageable | None = None,
) -> None:
    responses: dict[int, list[asyncpg.Record]] = {}
    questions: dict[int, str] = {}

    for question in await get_questions(bot.pool, form_id=form_id):
        questions[question['question_id']] = question['question_name']
        for response in await get_responses(bot.pool, question_id=question['question_id']):
            timestamp = response['response_time']
            responses.setdefault(timestamp, [])
            responses[timestamp].append(response)

    data = []
    for timestamp, records in responses.items():
        full_form_response = {}
        for record in records:
            question_name = questions[record['question_id']]
            full_form_response[question_name] = record['response']

        data.append(
            {
                'user': record['username'],  # all records have the same username,
                'timestamp': timestamp,
                'question_responses': full_form_response,
            }
        )

    buffer = io.BytesIO(json.dumps(data).encode())
    file = discord.File(buffer, filename='form.json')
    embed = discord.Embed(
        title=f'{form_name} has finished!',
        description='The file attached has JSON data for the form.',
        timestamp=discord.utils.utcnow(),
        color=COLOR,
    )

    response_channel_id = await get_responses_channel(bot.pool, form_id=form_id)

    if channel is None:
        if response_channel_id is None:
            try:
                channel = bot.get_user(creator_id) or await bot.fetch_user(creator_id)
            except discord.NotFound:
                return
        else:
            try:
                channel = bot.get_channel(
                    response_channel_id
                ) or await bot.fetch_channel(response_channel_id)
            except discord.NotFound:
                return
    await channel.send(embed=embed, file=file)
    await delete_form(bot.pool, form_id=form_id)

    message_id, channel_id = await get_origin_message(bot.pool, form_id=form_id)
    channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    message = await channel.fetch_message(message_id)

    view = discord.ui.View.from_message(message)
    view.children[0].disabled = True  # type: ignore
    await message.edit(view=view)


@tasks.loop(seconds=5)
async def check_database(bot: FormsBot):
    now = int(discord.utils.utcnow().timestamp())

    for form in await get_finished(bot.pool, now=now):
        bot.loop.create_task(
            finish_form(
                bot,
                form_id=form['form_id'],
                form_name=form['form_name'],
                creator_id=form['creator_id'],
            )
        )


async def wait_until_ready(bot: FormsBot):
    await bot.wait_until_ready()


async def setup(bot: FormsBot) -> None:
    check_database.start(bot)


async def teardown(bot: FormsBot) -> None:
    check_database.cancel()
