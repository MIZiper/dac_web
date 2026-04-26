import logging
import os
from typing import AsyncGenerator

import asyncpg

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "dac")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


async def init_pool():
    global pool

    try:
        pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
        )
    except Exception as e:
        logger.warning("Database connection failed, falling back to file storage: %s", e)
        pool = None


async def close_pool():
    global pool

    if pool:
        await pool.close()
        pool = None


async def get_db() -> AsyncGenerator[asyncpg.connection.Connection | None, None]:
    if pool is None:
        yield None
        return
    async with pool.acquire() as conn:
        yield conn
