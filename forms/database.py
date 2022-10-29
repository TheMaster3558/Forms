from __future__ import annotations

import asyncpg
import discord
from typing import TYPE_CHECKING, AsyncGenerator, Iterable

if TYPE_CHECKING:
    import datetime
    from ._types import Item


async def init_db(pool: asyncpg.Pool) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS forms (form_name text, form_id bigint, channel_id bigint, response_channel_id bigint, creator_id bigint, finishes_at timestamp with time zone)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS questions (form_id bigint, question_id bigint, item_type smallint)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS textinputs (question_id bigint, input_name text, input_type smallint)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS selects (question_id bigint, labels text, descriptions text)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS responses (question_id bigint, response_time timestamp with time zone, response text, username text)
                '''
            )


async def create_form(
    pool: asyncpg.Pool,
    *,
    name: str,
    form_id: int,
    channel_id: int,
    response_channel_id: int | None,
    creator_id: int,
    finishes_at: datetime.datetime,
    questions: list[Item],
) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                '''
                INSERT INTO forms VALUES ($1, $2, $3, $4, $5, $6)
                ''',
                name,
                form_id,
                channel_id,
                response_channel_id,
                creator_id,
                finishes_at,
            )
            for number, question in enumerate(questions):
                if isinstance(question, discord.ui.TextInput):
                    await conn.execute(
                        '''
                        INSERT INTO textinputs VALUES ($1, $2, $3)
                        ''',
                        form_id + number,
                        question.label,
                        int(question.style),
                    )
                    input_type = 0
                elif isinstance(question, discord.ui.Select):
                    await conn.execute(
                        '''
                        INSERT INTO selects VALUES ($1, $2, $3, $4)
                        ''',
                        form_id + number,
                        [option.label for option in question.options],
                        [option.description for option in question.options],
                    )
                    input_type = 1
                else:
                    continue
                await conn.execute(
                    '''
                    INSERT INTO questions VALUES ($1, $2, $3)
                    ''',
                    form_id,
                    form_id + number,
                    input_type
                )


async def get_origin_message(pool: asyncpg.Pool, *, form_id: int) -> tuple[int, int]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        record = await conn.fetchrow(
            '''
            SELECT channel_id FROM forms WHERE form_id = $1
            ''',
            form_id
        )
        return form_id, record['channel_id']


async def insert_responses(
    pool: asyncpg.Pool,
    *,
    response_time: datetime.datetime,
    user: str,
    question_ids: Iterable[int],
    responses: Iterable[str],
) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        data = [
            (question_id, response_time, response, user)
            for question_id, response in zip(question_ids, responses)
        ]
        await conn.executemany(
            '''
            INSERT INTO responses VALUES ($1, $2, $3, $4)
            ''',
            data,
        )


async def get_responses_channel(pool: asyncpg.Pool, *, form_id: int) -> int | None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            '''
            SELECT response_channel_id FROM forms WHERE form_id = $1
            ''',
            form_id,
        )
        return row and row['response_channel_id']


async def get_finished(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetch(
            '''
            SELECT form_name, form_id, response_channel_id, creator_id FROM forms WHERE $1 > finishes_at
            ''',
            discord.utils.utcnow()
        )


async def get_forms(pool: asyncpg.Pool) -> Iterable[asyncpg.Record]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetch(
            '''
            SELECT form_id, finishes_at FROM forms
            '''
        )


async def get_questions(pool: asyncpg.Pool, *, form_id: int) -> AsyncGenerator[tuple[int, Item], None]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        questions = await conn.fetch(
            '''
            SELECT question_id, item_type FROM questions WHERE form_id = $1 ORDER BY question_id DESC
            ''',
            form_id,
        )
        for question in questions:
            match question['item_type']:
                case 0:
                    record = await conn.fetchrow(
                        '''
                        SELECT input_name, input_type FROM textinputs WHERE question_id = $1
                        ''',
                        question['question_id']
                    )
                    item = discord.ui.TextInput(label=record['input_name'], style=discord.TextStyle(record['input_type']))
                case 1:
                    record = await conn.fetchrow(
                        '''
                        SELECT labels, descriptions FROM selects WHERE question_id = $1
                        ''',
                        question['question_id']
                    )
                    item = discord.ui.Select(
                        options=[
                            discord.SelectOption(label=label, description=description) for label, description in zip(record['labels'], record['descriptions'])
                        ]
                    )
                case _:
                    continue
            yield question['question_id'], item


async def get_responses(
    pool: asyncpg.Pool, *, question_id: int
) -> list[asyncpg.Record]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetch(
            '''
            SELECT question_id, response_time, response, username FROM responses WHERE question_id = $1
            ''',
            question_id,
        )


async def get_form_data(pool: asyncpg.Pool, *, form_id: int) -> asyncpg.Record:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            '''
            SELECT form_name, creator_id FROM forms WHERE form_id = $1
            ''',
            form_id,
        )


async def delete_form(pool: asyncpg.Pool, *, form_id: int) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        questions = await conn.fetch(
            '''
            SELECT question_id FROM questions WHERE form_id = $1
            ''',
            form_id,
        )
        await conn.executemany(
            '''
            DELETE FROM responses WHERE question_id = $1
            ''',
            [(question['question_id'],) for question in questions],
        )
        await conn.execute(
            '''
            DELETE FROM questions WHERE form_id = $1
            ''',
            form_id,
        )
        await conn.execute(
            '''
            DELETE FROM forms WHERE form_id = $1
            ''',
            form_id,
        )
