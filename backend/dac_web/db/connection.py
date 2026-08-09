import logging
from typing import AsyncGenerator

import asyncpg

from dac_web.config import settings

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None


async def init_pool():
    global pool

    try:
        pool = await asyncpg.create_pool(
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            host=settings.postgres_host,
            port=settings.postgres_port,
            min_size=1,
            max_size=4,
            command_timeout=30.0,
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
