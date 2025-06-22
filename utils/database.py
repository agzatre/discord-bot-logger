import logging
from typing import Optional, Any, Dict

import asyncpg

from config import database


class Database:
    def __init__(self):
        self.connection_params = {
            "user": database['user'],
            "password": database['password'],
            "database": database['database'],
            "host": database['host'],
            "port": database['port']
        }
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def __aenter__(self) -> "Database":
        """
        Асинхронный вход в контекстный менеджер.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Асинхронный выход из контекстного менеджера.
        """
        await self.close()

    async def connect(self) -> None:
        """
        Создаёт пул соединений к базе данных и необходимые таблицы/индексы.
        """
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
            logging.error(f"Ошибка подключения к базе данных: {e}")
            raise

    async def create_tables(self):
        """
        Создаёт необходимые таблицы в базе данных.
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS log_settings
                               (
                                   guild_id        BIGINT PRIMARY KEY,
                                   log_channel_id  BIGINT NOT NULL DEFAULT 0,
                                   logging_enabled BOOLEAN         DEFAULT FALSE,
                                   log_types       TEXT            DEFAULT 'message:0,invite:0,server:0,voice:0,automod:0,user:0'
                               );
                               """)

    async def create_indexes(self):
        """
        Создаёт необходимые индексы в базе данных.
        """
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
        """
        Закрывает пул соединений с базой данных.
        """
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def _ensure_connection(self):
        """
        Проверяет подключение и переподключается при необходимости.
        """
        if self.pool is None:
            await self.connect()

    async def set_log_channel(self, guild_id: int, channel_id: int) -> None:
        await self._ensure_connection()
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO log_settings (guild_id, log_channel_id)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id) DO UPDATE SET log_channel_id = EXCLUDED.log_channel_id
                    """,
                    guild_id, channel_id
                )
            except Exception as e:
                logging.error(f"Ошибка установки лог-канала: {e}")
                raise

    async def set_logging_enabled(self, guild_id: int, enabled: bool) -> None:
        """
        Включает или отключает логирование для сервера.

        :param guild_id: ID сервера Discord.
        :param enabled: Включить (True) или выключить (False) логирование.
        """
        async with self.pool.acquire() as conn:
            if enabled:
                await conn.execute(
                    """
                    INSERT INTO log_settings (guild_id, log_channel_id, logging_enabled, log_types)
                    VALUES (
                        $1,
                        COALESCE((SELECT log_channel_id FROM log_settings WHERE guild_id = $1), 0),
                        TRUE,
                        'message:1,invite:1,server:1,voice:1,automod:1,user:1'
                    )
                    ON CONFLICT (guild_id) DO UPDATE
                    SET logging_enabled = TRUE, log_types = 'message:1,invite:1,server:1,voice:1,automod:1,user:1'
                    """,
                    guild_id
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO log_settings (guild_id, log_channel_id, logging_enabled)
                    VALUES (
                        $1,
                        COALESCE((SELECT log_channel_id FROM log_settings WHERE guild_id = $1), 0),
                        FALSE
                    )
                    ON CONFLICT (guild_id) DO UPDATE SET logging_enabled = FALSE
                    """,
                    guild_id
                )

    async def set_log_types(self, guild_id: int, types_str: str) -> None:
        """
        Устанавливает типы логирования для сервера.

        :param guild_id: ID сервера Discord.
        :param types_str: Строка с типами логирования.
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO log_settings (guild_id, log_channel_id, log_types)
                VALUES (
                    $1,
                    COALESCE((SELECT log_channel_id FROM log_settings WHERE guild_id = $1), 0),
                    $2
                )
                ON CONFLICT (guild_id) DO UPDATE SET log_types = EXCLUDED.log_types
                """,
                guild_id, types_str
            )

    async def get_log_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает настройки логирования для сервера.

        :param guild_id: ID сервера Discord.
        :return: Словарь с настройками или None, если не найдено.
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT log_channel_id, logging_enabled, log_types FROM log_settings WHERE guild_id = $1",
                guild_id
            )
            if row:
                return dict(row)
            return None

