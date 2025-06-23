import logging
from typing import Optional, Any, Dict

import asyncpg

from config import database


class Database:
    def __init__(self):
        """Initialize database connection parameters."""
        self.connection_params = {
            "user": database['user'],
            "password": database['password'],
            "database": database['database'],
            "host": database['host'],
            "port": database['port']
        }
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def __aenter__(self) -> "Database":
        """Async context manager entry point."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Async context manager exit point."""
        await self.close()

    async def connect(self) -> None:
        """Establish database connection pool and create tables."""
        try:
            self.pool = await asyncpg.create_pool(
                **self.connection_params,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            await self.create_tables()
            await self.create_indexes()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise

    async def create_tables(self) -> None:
        """Create required tables if they don't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    guild_id        BIGINT PRIMARY KEY,
                    log_channel_id  BIGINT NOT NULL DEFAULT 0,
                    logging_enabled BOOLEAN DEFAULT FALSE,
                    log_types       TEXT DEFAULT 'message:0,invite:0,server:0,voice:0,automod:0,user:0',
                    language        TEXT DEFAULT 'en'
                );
            """)

    async def create_indexes(self) -> None:
        """Create database indexes for optimization."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE tablename = 'log_settings' AND indexname = 'log_settings_guild_idx'
                    ) THEN
                        CREATE INDEX log_settings_guild_idx ON log_settings (log_channel_id, guild_id);
                    END IF;
                END
                $$;
            """)

    async def close(self) -> None:
        """Close the database connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def _ensure_connection(self) -> None:
        """Ensure database connection is active."""
        if self.pool is None:
            await self.connect()

    async def set_log_channel(self, guild_id: int, channel_id: int) -> None:
        """Set or update the log channel for a guild."""
        await self._ensure_connection()
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO bot_settings (guild_id, log_channel_id)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id) DO UPDATE SET log_channel_id = EXCLUDED.log_channel_id
                    """,
                    guild_id, channel_id
                )
            except Exception as e:
                logging.error(f"Failed to set log channel: {e}")
                raise

    async def set_logging_enabled(self, guild_id: int, enabled: bool) -> None:
        """Enable or disable logging for a guild."""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            if enabled:
                await conn.execute(
                    """
                    INSERT INTO bot_settings (guild_id, logging_enabled, log_types)
                    VALUES ($1, TRUE, 'message:1,invite:1,server:1,voice:1,automod:1,user:1')
                    ON CONFLICT (guild_id) DO UPDATE
                        SET logging_enabled = TRUE,
                            log_types = 'message:1,invite:1,server:1,voice:1,automod:1,user:1'
                    """,
                    guild_id
                )
            else:
                await conn.execute(
                    """
                    UPDATE bot_settings
                    SET logging_enabled = FALSE
                    WHERE guild_id = $1
                    """,
                    guild_id
                )

    async def set_log_types(self, guild_id: int, types_str: str) -> None:
        """Update logging types for a guild."""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE bot_settings
                SET log_types = $2
                WHERE guild_id = $1
                """,
                guild_id, types_str
            )

    async def update_log_type(self, guild_id: int, log_type: str, enabled: bool) -> None:
        """Enable/disable specific log type for a guild."""
        settings = await self.get_log_settings(guild_id)
        if not settings:
            return

        log_types = {}
        for item in settings['log_types'].split(','):
            if ':' in item:
                typ, val = item.split(':')
                log_types[typ.strip()] = val.strip()

        log_types[log_type] = '1' if enabled else '0'
        types_str = ','.join(f"{k}:{v}" for k, v in log_types.items())
        await self.set_log_types(guild_id, types_str)

    async def get_log_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve logging settings for a guild."""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT log_channel_id, logging_enabled, log_types FROM bot_settings WHERE guild_id = $1",
                guild_id
            )
            return dict(row) if row else None

    async def get_language(self, guild_id: int) -> str:
        """Get language setting for a guild (default: 'en')."""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT language FROM bot_settings WHERE guild_id = $1",
                guild_id
            ) or "en"

    async def set_language(self, guild_id: int, language: str) -> None:
        """Set language for a guild."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO bot_settings (guild_id, language)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE SET language = EXCLUDED.language
            ''', guild_id, language)