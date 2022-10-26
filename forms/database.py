import asyncpg
from typing import Iterable


async def init_db(pool: asyncpg.Pool) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS forms (form_name text, form_id bigint, response_channel_id bigint, creator_id bigint, finishes_at int)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS questions (form_id bigint, question_id bigint, question_name text, input_type int)
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS responses (question_id bigint, response_time int, response text, username text)
                '''
            )


async def create_form(
    pool: asyncpg.Pool,
    *,
    name: str,
    form_id: int,
    response_channel_id: int | None,
    creator_id: int,
    finishes_at: int,
    questions: dict[str, int],
) -> None:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                '''
                INSERT INTO forms VALUES ($1, $2, $3, $4, $5)
                ''',
                name,
                form_id,
                response_channel_id,
                creator_id,
                finishes_at,
            )
            data = [
                (form_id, form_id + number, question_name, input_type)
                for number, (question_name, input_type) in enumerate(questions.items())
            ]
            await conn.executemany(
                '''
                INSERT INTO questions VALUES ($1, $2, $3, $4)
                ''',
                data,
            )


async def insert_responses(
    pool: asyncpg.Pool,
    *,
    response_time: int,
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


async def get_finished(pool: asyncpg.Pool, *, now: int) -> list[asyncpg.Record]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetch(
            '''
            SELECT form_name, form_id, response_channel_id, creator_id FROM forms WHERE $1 > finishes_at
            ''',
            now,
        )


async def get_questions(pool: asyncpg.Pool, *, form_id: int) -> list[asyncpg.Record]:
    conn: asyncpg.Connection

    async with pool.acquire() as conn:
        return await conn.fetch(
            '''
            SELECT question_id, question_name FROM questions WHERE form_id = $1
            ''',
            form_id,
        )


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
