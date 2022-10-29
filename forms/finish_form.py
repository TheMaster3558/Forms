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

    async for question_id, question in get_questions(bot.pool, form_id=form_id):
        if isinstance(question, discord.ui.TextInput):
            questions[question_id] = question.label
        elif isinstance(question, discord.ui.Select):
            assert question.placeholder is not None
            questions[question_id] = question.placeholder
        for response in await get_responses(bot.pool, question_id=question_id):
            timestamp = response['response_time'].timestamp()
            responses.setdefault(timestamp, [])
            responses[timestamp].append(response)

    data = []
    for timestamp, records in responses.items():
        full_form_response = {}

        record = {}
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
                channel = await bot.getch(bot.fetch_user, creator_id)
            except discord.HTTPException:
                return
        else:
            try:
                channel = await bot.getch(bot.fetch_channel, response_channel_id)
            except discord.HTTPException:
                return

    await channel.send(embed=embed, file=file)

    try:
        message_id, channel_id = await get_origin_message(bot.pool, form_id=form_id)
        message_channel: discord.abc.Messageable = await bot.getch(bot.fetch_channel, channel_id)
        message = await message_channel.fetch_message(message_id)

        view = discord.ui.View.from_message(message)
        view.children[0].disabled = True  # type: ignore
        await message.edit(view=view)
    except discord.HTTPException:
        pass
    await delete_form(bot.pool, form_id=form_id)


@tasks.loop(seconds=5)
async def check_database(bot: FormsBot):
    for form in await get_finished(bot.pool):
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
