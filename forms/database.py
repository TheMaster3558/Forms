from __future__ import annotations

import asyncpg
import discord
from typing import TYPE_CHECKING, AsyncGenerator, Iterable

if TYPE_CHECKING:
    import datetime
    from ._types import Item


def get_form_id(name: str, guild: discord.abc.Snowflake) -> str:
    return f'{guild.id}{name}'


async def init_db(pool: asyncpg.Pool) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS forms (form_name text, form_id text, guild_id bigint, response_channel_id bigint, creator_id bigint, finishes_at timestamp with time zone)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS questions (form_id text, question_id text, item_type smallint)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS textinputs (question_id text, input_name text, input_type smallint)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS selects (question_id text, labels text[], descriptions text[])
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS responses (question_id text, response_time timestamp with time zone, response text, username text)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS permissions (form_id text, users bigint[], roles bigint[], everyone bool)
                '''
            )


async def create_form(
    pool: asyncpg.Pool,
    *,
    name: str,
    form_id: str,
    guild_id: int,
    response_channel_id: int | None,
    creator_id: int,
    finishes_at: datetime.datetime,
    questions: Iterable[Item],
    allowed_users: list[int],
    allowed_roles: list[int],
    allow_everyone: bool,
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
                guild_id,
                response_channel_id,
                creator_id,
                finishes_at,
            )
            for number, question in enumerate(questions):
                number = str(number)
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
                    input_type,
                )
            await conn.execute(
                '''
                INSERT INTO permissions VALUES ($1, $2, $3, $4)
                ''',
                form_id,
                allowed_users,
                allowed_roles,
                allow_everyone,
            )


async def insert_responses(
    pool: asyncpg.Pool,
    *,
    response_time: datetime.datetime,
    user: str,
    question_ids: Iterable[str],
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


async def get_responses_channel(pool: asyncpg.Pool, *, form_id: str) -> int | None:
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
            SELECT form_name, guild_id, response_channel_id, creator_id FROM forms WHERE $1 > finishes_at
            ''',
            discord.utils.utcnow(),
        )


async def get_forms(
    pool: asyncpg.Pool, *, guild_id: int | None = None
) -> Iterable[asyncpg.Record]:
    conn: asyncpg.Connection

    sql = 'SELECT form_name, form_id, finishes_at FROM forms'
    args = []

    if guild_id:
        sql += ' WHERE guild_id = $1'
        args.append(guild_id)

    async with pool.acquire() as conn:
        return await conn.fetch(sql, *args)


async def get_questions(
    pool: asyncpg.Pool, *, form_id: str
) -> AsyncGenerator[tuple[str, Item], None]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        questions = await conn.fetch(
            '''
            SELECT question_id, item_type FROM questions WHERE form_id = $1 ORDER BY question_id DESC
            ''',
            form_id,
        )
        for question in questions:
            if question['item_type'] == 0:
                row = await conn.fetchrow(
                    '''
                    SELECT input_name, input_type FROM textinputs WHERE question_id = $1
                    ''',
                    question['question_id'],
                )
                item = discord.ui.TextInput(
                    label=row['input_name'], style=discord.TextStyle(row['input_type'])
                )
            elif question['item_tyoe'] == 1:
                row = await conn.fetchrow(
                    '''
                    SELECT labels, descriptions FROM selects WHERE question_id = $1
                    ''',
                    question['question_id'],
                )
                item = discord.ui.Select(
                    options=[
                        discord.SelectOption(label=label, description=description)
                        for label, description in zip(
                            row['labels'], row['descriptions']
                        )
                    ]
                )
            else:
                continue
            yield question['question_id'], item


async def get_responses(
    pool: asyncpg.Pool, *, question_id: str
) -> list[asyncpg.Record]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetch(
            '''
            SELECT question_id, response_time, response, username FROM responses WHERE question_id = $1
            ''',
            question_id,
        )


async def get_form_data(pool: asyncpg.Pool, *, form_id: str) -> asyncpg.Record:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetchrow(
            '''
            SELECT form_name, creator_id FROM forms WHERE form_id = $1
            ''',
            form_id,
        )


async def delete_form(pool: asyncpg.Pool, *, form_id: str) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        async with conn.transaction():
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


async def get_permissions(
    pool: asyncpg.Pool, *, form_id: str
) -> tuple[list[int], list[int], bool]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            '''
            SELECT users, roles, everyone FROM permissions WHERE form_id = $1
            ''',
            form_id,
        )
        return row['users'], row['roles'], row['everyone']


async def can_take_form(
    pool: asyncpg.Pool, *, member: discord.Member, form_id: str
) -> bool:
    users, roles, everyone = await get_permissions(pool, form_id=form_id)
    return (
        member.id in users or any(role.id in roles for role in member.roles) or everyone
    )
