from __future__ import annotations

import asyncio
import functools
import io
import json
import threading
import os
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    IO,
    Literal,
    Mapping,
    ParamSpec,
    TypeVar,
)

import orjson
import discord
from discord.ext import tasks

import matplotlib

matplotlib.use('Agg')

from matplotlib import pyplot as plt

from .constants import COLOR
from .database import (
    delete_form,
    get_finished,
    get_questions,
    get_responses,
    get_responses_channel,
    get_form_id,
)

if TYPE_CHECKING:
    import asyncpg
    from .bot import FormsBot


P = ParamSpec('P')
R = TypeVar('R')


lock = threading.Lock()


def with_lock_in_thread(func: Callable[P, R]) -> Callable[P, Awaitable[R]]:
    @functools.wraps(func)
    def wrapped_func(*args: P.args, **kwargs: P.args) -> Awaitable[R]:
        with lock:
            return asyncio.get_running_loop().run_in_executor(
                None, functools.partial(func, *args, **kwargs)
            )

    return wrapped_func


@with_lock_in_thread
def create_pie_chart(name: str, responses: dict[str, int]) -> discord.File:
    plt.pie(responses.values(), labels=responses.keys(), autopct='%1.1f%%')
    plt.title(name)

    buffer = io.BytesIO()
    plt.savefig(buffer)
    plt.close()

    buffer.seek(0)
    return discord.File(buffer, filename=f'{name}_pie.png')


@with_lock_in_thread
def create_bar_graph(name: str, responses: dict[str, int]) -> discord.File:
    plt.bar(responses.keys(), responses.values())
    plt.xlabel('Count')
    plt.ylabel('Questions')
    plt.title(name)

    buffer = io.BytesIO()
    plt.savefig(buffer)
    plt.close()

    buffer.seek(0)
    return discord.File(buffer, filename=f'{name}_bar.png')


def get_file_size(file: IO) -> int:
    old_pos = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(old_pos, os.SEEK_SET)
    return size


def get_file_size_limit(premium_tier: Literal[None, 0, 1, 2, 3]) -> int:
    if not premium_tier or premium_tier == 1:
        return 8388608
    elif premium_tier == 2:
        return 52428800
    else:
        return 104857600


async def finish_form(
    bot: FormsBot,
    *,
    guild: discord.abc.Snowflake,
    form_name: str,
    creator_id: int,
    channel: discord.abc.Messageable | None = None,
) -> None:
    form_id = get_form_id(form_name, guild)
    responses: dict[int, list[asyncpg.Record]] = {}
    questions: dict[str, str] = {}
    selects_data: dict[str, dict[str, int]] = {}

    async for question_id, question in get_questions(bot.pool, form_id=form_id):
        if isinstance(question, discord.ui.TextInput):
            questions[question_id] = question.label
        elif isinstance(question, discord.ui.Select):
            questions[question_id] = question.placeholder
            selects_data[question.placeholder] = {}
        for response in await get_responses(bot.pool, question_id=question_id):
            timestamp = response['response_time'].timestamp()
            responses.setdefault(timestamp, [])
            responses[timestamp].append(response)

    data = []
    for timestamp, rows in responses.items():
        full_form_response = {}
        row: Mapping[str, Any] = {}
        for row in rows:
            question_name = questions[row['question_id']]
            full_form_response[question_name] = row['response']
            if question_name in selects_data:
                selects_data[question_name].setdefault(row['response'], 0)
                selects_data[question_name][row['response']] += 1

        data.append(
            {
                'user': row['username'],  # all rows have the same username,
                'timestamp': timestamp,
                'question_responses': full_form_response,
            }
        )

    response_channel_id = await get_responses_channel(bot.pool, form_id=form_id)
    if channel is None:
        try:
            if response_channel_id is None:
                channel = await bot.getch(bot.fetch_user, creator_id)
            else:
                channel = await bot.getch(bot.fetch_channel, response_channel_id)
        except discord.HTTPException:
            pass
        else:
            buffer = io.BytesIO(json.dumps(data).encode())
            if get_file_size(buffer) > get_file_size_limit(
                channel.guild.premium_tier if isinstance(channel, discord.abc.GuildChannel) else None
            ):
                buffer.close()
                buffer = io.BytesIO(orjson.dumps(data))  # orjson takes up less space

            file = discord.File(buffer, filename='form.json')
            embed = discord.Embed(
                title=f'{form_name} has finished!',
                description='The file attached has JSON data for the form.',
                timestamp=discord.utils.utcnow(),
                color=COLOR,
            )
            await channel.send(embed=embed, file=file)

            async with channel.typing():
                for question_name, question_responses in selects_data:
                    pie_file = await create_pie_chart(question_name, question_responses)
                    bar_file = await create_bar_graph(question_name, question_responses)

                    pie_embed = discord.Embed(title=question_name, color=COLOR)
                    pie_embed.set_image(url=f'attachment://{pie_file.filename}')
                    bar_embed = discord.Embed(title=question_name, color=COLOR)
                    bar_embed.set_image(url=f'attachment://{bar_file.filename}')
                    await channel.send(
                        embeds=[pie_embed, bar_embed], files=[pie_file, bar_file]
                    )
    await delete_form(bot.pool, form_id=form_id)


@tasks.loop(minutes=20)
async def check_database(bot: FormsBot) -> None:
    await bot.wait_until_ready()
    for form in await get_finished(bot.pool):
        bot.loop.create_task(
            finish_form(
                bot,
                guild=discord.Object(id=form['guild_id']),
                form_name=form['form_name'],
                creator_id=form['creator_id'],
            )
        )


async def setup(bot: FormsBot) -> None:
    check_database.start(bot)


async def teardown(bot: FormsBot) -> None:
    check_database.cancel()
