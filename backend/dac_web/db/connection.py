import os

import asyncpg
from typing import AsyncGenerator

pool = None

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "dac")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


async def init_pool():
    global pool

    pool = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
    )


async def close_pool():
    global pool

    if pool:
        await pool.close()


async def get_db() -> AsyncGenerator[asyncpg.connection.Connection, None]:
    async with pool.acquire() as conn:
        yield conn
