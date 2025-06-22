import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import disnake
from disnake.ext import commands

from config import log_colors
from utils.database import Database

os.makedirs('./logs', exist_ok=True)
listener_log = logging.getLogger("listener_events")
listener_log.setLevel(logging.INFO)
listener_log.handlers.clear()
file_handler = RotatingFileHandler(
    './logs/listener_events.log',
    maxBytes=1 * 1024 * 1024 * 1024,
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s | %(levelname)s]: %(message)s',
    datefmt='%m.%d.%Y %H:%M:%S'
))
listener_log.addHandler(file_handler)
listener_log.propagate = False


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def cog_load(self):
        await self.db.connect()
        logging.info("Database connected successfully")

    async def get_log_channel_id(self, guild):
        if guild is None:
            return None
        guild_id = guild.id
        row = await self.db.get_log_settings(guild_id)
        if row and "log_channel_id" in row:
            return row["log_channel_id"]
        return None

    async def get_log_channel(self, guild):
        log_channel_id = await self.get_log_channel_id(guild)
        if not log_channel_id:
            return None
        channel = self.bot.get_channel(log_channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(log_channel_id)
            except Exception as e:
                listener_log.error("Не удалось найти канал логов: %s", e)
                return None
        return channel

    async def is_logging_enabled(self, guild):
        if guild is None:
            return False
        row = await self.db.get_log_settings(guild.id)
        if row and "logging_enabled" in row:
            return bool(row["logging_enabled"])
        return True

    async def is_log_type_enabled(self, guild, log_type):
        if guild is None:
            return False
        row = await self.db.get_log_settings(guild.id)
        types = {
            "message": True,
            "invite": True,
            "server": True,
            "voice": True,
            "user": True
        }
        if row and "log_types" in row and row["log_types"]:
            for pair in row["log_types"].split(","):
                k, v = pair.split(":")
                types[k] = v == "1"
        return types.get(log_type, True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if getattr(member, "bot", False):
            return
        if not await self.is_logging_enabled(member.guild):
            return
        if not await self.is_log_type_enabled(member.guild, "voice"):
            return
        listener_log.info("on_voice_state_update: member=%s, before=%s, after=%s", member, before, after)
        channel = await self.get_log_channel(member.guild)
        if channel:
            if before.channel is None and after.channel is not None:
                embed = disnake.Embed(
                    title="Пользователь зашёл в голосовой канал",
                    description=f"{member.mention} (`{member.id}`) зашёл в {after.channel.mention} (`{after.channel.id}`)",
                    color=log_colors["success"],
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
            elif before.channel is not None and after.channel is None:
                embed = disnake.Embed(
                    title="Пользователь вышел из голосового канала",
                    description=f"{member.mention} (`{member.id}`) вышел из {before.channel.mention} (`{before.channel.id}`)",
                    color=log_colors["error"],
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)
            elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                embed = disnake.Embed(
                    title="Пользователь перешёл в другой голосовой канал",
                    description=f"{member.mention} (`{member.id}`) перешёл из {before.channel.mention} (`{before.channel.id}`) в {after.channel.mention} (`{after.channel.id}`)",
                    color=log_colors["info"],
                    timestamp=datetime.now()
                )
                await channel.send(embed=embed)

            if before.self_mute != after.self_mute:
                if after.self_mute:
                    embed = disnake.Embed(
                        title="Микрофон выключен",
                        description=f"{member.mention} (`{member.id}`) выключил микрофон",
                        color=log_colors["warning"],
                        timestamp=datetime.now()
                    )
                else:
                    embed = disnake.Embed(
                        title="Микрофон включён",
                        description=f"{member.mention} (`{member.id}`) включил микрофон",
                        color=log_colors["success"],
                        timestamp=datetime.now()
                    )
                await channel.send(embed=embed)

            if before.self_deaf != after.self_deaf:
                if after.self_deaf:
                    embed = disnake.Embed(
                        title="Звук выключен",
                        description=f"{member.mention} (`{member.id}`) выключил звук",
                        color=log_colors["warning"],
                        timestamp=datetime.now()
                    )
                else:
                    embed = disnake.Embed(
                        title="Звук включён",
                        description=f"{member.mention} (`{member.id}`) включил звук",
                        color=log_colors["success"],
                        timestamp=datetime.now()
                    )
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage_instance):
        listener_log.info("on_stage_instance_create: %s", stage_instance)
        channel = await self.get_log_channel(
            getattr(stage_instance.channel.guild, "id", None) and stage_instance.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Создано Stage Instance",
                description=(
                    f"**Тема:** {stage_instance.topic}\n"
                    f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage_instance):
        listener_log.info("on_stage_instance_delete: %s", stage_instance)
        channel = await self.get_log_channel(
            getattr(stage_instance.channel.guild, "id", None) and stage_instance.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Удалён Stage Instance",
                description=(
                    f"**Тема:** {stage_instance.topic}\n"
                    f"**Канал:** {stage_instance.channel.mention} (`{stage_instance.channel.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_stage_instance_update(self, before, after):
        listener_log.info("on_stage_instance_update: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(getattr(after.channel.guild, "id", None) and after.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Изменён Stage Instance",
                description=(
                    f"**Канал:** {after.channel.mention} (`{after.channel.id}`)\n"
                    f"**Тема до:** {before.topic}\n"
                    f"**Тема после:** {after.topic}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    # === СООБЩЕНИЯ ===
    @commands.Cog.listener()
    async def on_message(self, message):
        if getattr(message.author, "bot", False):
            return
        if not await self.is_logging_enabled(message.guild):
            return
        if not await self.is_log_type_enabled(message.guild, "message"):
            return
        listener_log.info("on_message: %s", message)
        channel = await self.get_log_channel(message.guild)
        if channel is None:
            return
        embed = disnake.Embed(
            title="Новое сообщение",
            description=(
                f"**Канал:** {message.channel.mention} (`{message.channel.id}`)\n"
                f"**Автор:** {message.author.mention} (`{message.author.id}`)\n"
                f"**Содержание:** {message.content}"
            ),
            color=log_colors["success"],
            timestamp=datetime.now())
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if getattr(before.author, "bot", False):
            return
        listener_log.info("on_message_edit: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(before.guild)
        if channel:
            embed = disnake.Embed(
                title="Сообщение отредактировано",
                description=(
                    f"**Канал:** {before.channel.mention} (`{before.channel.id}`)\n"
                    f"**Автор:** {before.author.mention} (`{before.author.id}`)\n"
                    f"**До:** {before.content}\n"
                    f"**После:** {after.content}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if getattr(message.author, "bot", False):
            return
        listener_log.info("on_message_delete: %s", message)
        channel = await self.get_log_channel(message.guild)
        if channel:
            embed = disnake.Embed(
                title="Сообщение удалено",
                description=(
                    f"**Канал:** {message.channel.mention} (`{message.channel.id}`)\n"
                    f"**Автор:** {message.author.mention} (`{message.author.id}`)\n"
                    f"**Содержание:** {message.content}"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if getattr(messages[0].author, "bot", False):
            return
        listener_log.info("on_bulk_message_delete: %s", messages)
        channel = await self.get_log_channel(messages[0].guild)
        if channel:
            embed = disnake.Embed(
                title="Удалено несколько сообщений",
                description=(
                    f"**Канал:** {messages[0].channel.mention} (`{messages[0].channel.id}`)\n"
                    f"**Количество:** {len(messages)}"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if getattr(user, "bot", False):
            return
        listener_log.info("on_typing: channel=%s, user=%s, when=%s", channel, user, when)
        log_channel = await self.get_log_channel(channel.guild if hasattr(channel, "guild") else None)
        if log_channel:
            embed = disnake.Embed(
                title="Пользователь печатает",
                description=(
                    f"**Пользователь:** {user.mention} (`{user.id}`)\n"
                    f"**Канал:** {channel.mention} (`{channel.id}`)"
                ),
                color=log_colors["info"],
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if getattr(user, "bot", False):
            return
        listener_log.info("on_reaction_add: reaction=%s, user=%s", reaction, user)
        channel = await self.get_log_channel(reaction.message.guild)
        if channel:
            embed = disnake.Embed(
                title="Добавлена реакция",
                description=(
                    f"**Эмодзи:** {reaction.emoji}\n"
                    f"**Канал:** {reaction.message.channel.mention} (`{reaction.message.channel.id}`)\n"
                    f"**Сообщение:** [Перейти к сообщению]({reaction.message.jump_url}) (`{reaction.message.id}`)\n"
                    f"**Пользователь:** {user.mention} (`{user.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if getattr(user, "bot", False):
            return
        listener_log.info("on_reaction_remove: reaction=%s, user=%s", reaction, user)
        channel = await self.get_log_channel(reaction.message.guild)
        if channel:
            embed = disnake.Embed(
                title="Удалена реакция",
                description=(
                    f"**Эмодзи:** {reaction.emoji}\n"
                    f"**Канал:** {reaction.message.channel.mention} (`{reaction.message.channel.id}`)\n"
                    f"**Сообщение:** [Перейти к сообщению]({reaction.message.jump_url}) (`{reaction.message.id}`)\n"
                    f"**Пользователь:** {user.mention} (`{user.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        if getattr(message.author, "bot", False):
            return
        listener_log.info("on_reaction_clear: message=%s, reactions=%s", message, reactions)
        channel = await self.get_log_channel(message.guild)
        if channel:
            embed = disnake.Embed(
                title="Очищены реакции",
                description=(
                    f"**Канал:** {message.channel.mention} (`{message.channel.id}`)\n"
                    f"**Сообщение:** [Перейти к сообщению]({message.jump_url}) (`{message.id}`)\n"
                    f"**Количество:** {len(reactions)}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_clear_emoji(self, reaction):
        if getattr(reaction.message.author, "bot", False):
            return
        listener_log.info("on_reaction_clear_emoji: reaction=%s", reaction)
        channel = await self.get_log_channel(reaction.message.guild)
        if channel:
            embed = disnake.Embed(
                title="Очищена одна реакция",
                description=(
                    f"**Эмодзи:** {reaction.emoji}\n"
                    f"**Канал:** {reaction.message.channel.mention} (`{reaction.message.channel.id}`)\n"
                    f"**Сообщение:** [Перейти к сообщению]({reaction.message.jump_url}) (`{reaction.message.id}`)"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        listener_log.info("on_guild_emojis_update: guild=%s, before=%s, after=%s", guild, before, after)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Обновлены эмодзи сервера",
                description=(
                    f"**Сервер:** {guild.name} (`{guild.id}`)\n"
                    f"**Количество до:** {len(before)}\n"
                    f"**Количество после:** {len(after)}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        listener_log.info("on_guild_stickers_update: guild=%s, before=%s, after=%s", guild, before, after)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Обновлены стикеры сервера",
                description=(
                    f"**Сервер:** {guild.name} (`{guild.id}`)\n"
                    f"**Количество до:** {len(before)}\n"
                    f"**Количество после:** {len(after)}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    # === СЕРВЕР ===
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        listener_log.info("on_guild_update: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(before)
        if channel:
            embed = disnake.Embed(
                title="Изменены настройки сервера",
                description=(
                    f"**Сервер:** {after.name} (`{after.id}`)\n"
                    f"**До:** {before}\n"
                    f"**После:** {after}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        listener_log.info("on_guild_channel_create: %s", channel)
        log_channel = await self.get_log_channel(channel.guild)
        if log_channel:
            embed = disnake.Embed(
                title="Создан новый канал",
                description=(
                    f"**Канал:** {channel.mention} (`{channel.id}`)\n"
                    f"**Сервер:** {channel.guild.name} (`{channel.guild.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        listener_log.info("on_guild_channel_delete: %s", channel)
        log_channel = await self.get_log_channel(channel.guild)
        if log_channel:
            embed = disnake.Embed(
                title="Удалён канал",
                description=(
                    f"**Канал:** {channel.mention} (`{channel.id}`)\n"
                    f"**Сервер:** {channel.guild.name} (`{channel.guild.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        listener_log.info("on_guild_channel_update: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(after.guild)
        if channel:
            embed = disnake.Embed(
                title="Изменены настройки канала",
                description=(
                    f"**Канал:** {after.mention} (`{after.id}`)\n"
                    f"**Сервер:** {after.guild.name} (`{after.guild.id}`)\n"
                    f"**До:** {before}\n"
                    f"**После:** {after}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        listener_log.info("on_thread_create: %s", thread)
        channel = await self.get_log_channel(thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Создана новая тема",
                description=(
                    f"**Тема:** {thread.name} (`{thread.id}`)\n"
                    f"**Канал:** {thread.parent.mention if thread.parent else 'N/A'}\n"
                    f"**Сервер:** {thread.guild.name} (`{thread.guild.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        listener_log.info("on_thread_delete: %s", thread)
        channel = await self.get_log_channel(thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Удалена тема",
                description=(
                    f"**Тема:** {thread.name} (`{thread.id}`)\n"
                    f"**Канал:** {thread.parent.mention if thread.parent else 'N/A'}\n"
                    f"**Сервер:** {thread.guild.name} (`{thread.guild.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        listener_log.info("on_thread_update: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(after.guild)
        if channel:
            embed = disnake.Embed(
                title="Изменена тема",
                description=(
                    f"**Тема:** {after.name} (`{after.id}`)\n"
                    f"**Канал:** {after.parent.mention if after.parent else 'N/A'}\n"
                    f"**Сервер:** {after.guild.name} (`{after.guild.id}`)"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_thread_member_join: %s", member)
        channel = await self.get_log_channel(member.thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь присоединился к теме",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Тема:** {member.thread.name} (`{member.thread.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_thread_member_remove: %s", member)
        channel = await self.get_log_channel(member.thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь покинул тему",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Тема:** {member.thread.name} (`{member.thread.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_members_update(self, thread, before, after):
        listener_log.info("on_thread_members_update: thread=%s, before=%s, after=%s", thread, before, after)
        channel = await self.get_log_channel(thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Обновлены участники темы",
                description=(
                    f"**Тема:** {thread.name} (`{thread.id}`)\n"
                    f"**Количество участников до:** {len(before)}\n"
                    f"**Количество участников после:** {len(after)}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_auto_moderation_rule_create(self, rule):
        listener_log.info("on_auto_moderation_rule_create: %s", rule)
        guild = getattr(rule, "guild", None)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Создано правило авто-модерации",
                description=(
                    f"**Правило:** {getattr(rule, 'name', str(rule))}\n"
                    f"**Сервер:** {guild.name if guild else 'N/A'} (`{guild.id if guild else 'N/A'}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_auto_moderation_rule_update(self, before, after):
        listener_log.info("on_auto_moderation_rule_update: before=%s, after=%s", before, after)
        guild = getattr(after, "guild", None)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Обновлено правило авто-модерации",
                description=(
                    f"**Правило до:** {getattr(before, 'name', str(before))}\n"
                    f"**Правило после:** {getattr(after, 'name', str(after))}\n"
                    f"**Сервер:** {guild.name if guild else 'N/A'} (`{guild.id if guild else 'N/A'}`)"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_auto_moderation_rule_delete(self, rule):
        listener_log.info("on_auto_moderation_rule_delete: %s", rule)
        guild = getattr(rule, "guild", None)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Удалено правило авто-модерации",
                description=(
                    f"**Правило:** {getattr(rule, 'name', str(rule))}\n"
                    f"**Сервер:** {guild.name if guild else 'N/A'} (`{guild.id if guild else 'N/A'}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_auto_moderation_action_execution(self, execution):
        listener_log.info("on_auto_moderation_action_execution: %s", execution)
        guild = getattr(execution, "guild", None)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Выполнено действие авто-модерации",
                description=(
                    f"**Действие:** {getattr(execution, 'action', str(execution))}\n"
                    f"**Сервер:** {guild.name if guild else 'N/A'} (`{guild.id if guild else 'N/A'}`)"
                ),
                color=log_colors["info"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        listener_log.info("on_webhooks_update: %s", channel)
        log_channel = await self.get_log_channel(channel.guild)
        if log_channel:
            embed = disnake.Embed(
                title="Обновлены вебхуки канала",
                description=(
                    f"**Канал:** {channel.mention} (`{channel.id}`)\n"
                    f"**Сервер:** {channel.guild.name} (`{channel.guild.id}`)"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        listener_log.info("on_invite_create: %s", invite)
        channel = await self.get_log_channel(getattr(invite.channel.guild, "id", None) and invite.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Создано приглашение",
                description=(
                    f"**Код:** {invite.code}\n"
                    f"**Канал:** {invite.channel.mention} (`{invite.channel.id}`)\n"
                    f"**Пригласивший:** {invite.inviter.mention if invite.inviter else 'N/A'}"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        listener_log.info("on_invite_delete: %s", invite)
        channel = await self.get_log_channel(getattr(invite.channel.guild, "id", None) and invite.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Удалено приглашение",
                description=(
                    f"**Код:** {invite.code}\n"
                    f"**Канал:** {invite.channel.mention} (`{invite.channel.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_member_join: %s", member)
        channel = await self.get_log_channel(member.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь присоединился к серверу",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Сервер:** {member.guild.name} (`{member.guild.id}`)\n"
                    f"**Дата создания аккаунта:** {member.created_at.strftime('%d.%m.%Y %H:%M:%S')}"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_member_remove: %s", member)
        channel = await self.get_log_channel(member.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь покинул сервер",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Сервер:** {member.guild.name} (`{member.guild.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if getattr(user, "bot", False):
            return
        listener_log.info("on_member_ban: guild=%s, user=%s", guild, user)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь забанен",
                description=(
                    f"**Пользователь:** {getattr(user, 'mention', user)} (`{getattr(user, 'id', user)}`)\n"
                    f"**Сервер:** {guild.name} (`{guild.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if getattr(user, "bot", False):
            return
        listener_log.info("on_member_unban: guild=%s, user=%s", guild, user)
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь разбанен",
                description=(
                    f"**Пользователь:** {getattr(user, 'mention', user)} (`{getattr(user, 'id', user)}`)\n"
                    f"**Сервер:** {guild.name} (`{guild.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_timeout(self, member, until):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_member_timeout: member=%s, until=%s", member, until)
        channel = await self.get_log_channel(member.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь получил тайм-аут",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Сервер:** {member.guild.name} (`{member.guild.id}`)\n"
                    f"**До:** {until.strftime('%d.%m.%Y %H:%M:%S') if until else 'None'}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_timeout_remove(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_member_timeout_remove: member=%s", member)
        channel = await self.get_log_channel(member.guild)
        if channel:
            embed = disnake.Embed(
                title="Тайм-аут пользователя снят",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Сервер:** {member.guild.name} (`{member.guild.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, before, after):
        if getattr(after, "bot", False):
            return
        listener_log.info("on_member_update: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(after.guild)
        if channel:
            embed = disnake.Embed(
                title="Изменены данные пользователя",
                description=(
                    f"**Пользователь:** {after.mention} (`{after.id}`)\n"
                    f"**До:** {before}\n"
                    f"**После:** {after}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)
        before_timeout = getattr(before, "timed_out_until", None)
        after_timeout = getattr(after, "timed_out_until", None)
        if before_timeout != after_timeout:
            if getattr(after, "bot", False):
                return
            channel = await self.get_log_channel(after.guild)
            if channel:
                if before_timeout is None and after_timeout is not None:
                    embed = disnake.Embed(
                        title="Пользователь замучен",
                        description=(
                            f"**Пользователь:** {after.mention} (`{after.id}`)\n"
                            f"**До:** {before_timeout}\n"
                            f"**После:** {after_timeout}"
                        ),
                        color=log_colors["error"],
                        timestamp=datetime.now()
                    )
                    await channel.send(embed=embed)
                elif before_timeout is not None and after_timeout is None:
                    embed = disnake.Embed(
                        title="Пользователь размучен",
                        description=(
                            f"**Пользователь:** {after.mention} (`{after.id}`)\n"
                            f"**До:** {before_timeout}\n"
                            f"**После:** {after_timeout}"
                        ),
                        color=log_colors["success"],
                        timestamp=datetime.now()
                    )
                    await channel.send(embed=embed)
                else:
                    embed = disnake.Embed(
                        title="Изменён таймаут пользователя",
                        description=(
                            f"**Пользователь:** {after.mention} (`{after}` | `{after.id}`)\n"
                            f"**До:** {before_timeout}\n"
                            f"**После:** {after_timeout}"
                        ),
                        color=log_colors["warning"],
                        timestamp=datetime.now()
                    )
                    await channel.send(embed=embed)

    # === ПРИГЛАШЕНИЯ ===
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        listener_log.info("on_invite_create: %s", invite)
        channel = await self.get_log_channel(getattr(invite.channel.guild, "id", None) and invite.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Создано приглашение",
                description=(
                    f"**Код:** {invite.code}\n"
                    f"**Канал:** {invite.channel.mention} (`{invite.channel.id}`)\n"
                    f"**Пригласивший:** {invite.inviter.mention if invite.inviter else 'N/A'}"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        listener_log.info("on_invite_delete: %s", invite)
        channel = await self.get_log_channel(getattr(invite.channel.guild, "id", None) and invite.channel.guild)
        if channel:
            embed = disnake.Embed(
                title="Удалено приглашение",
                description=(
                    f"**Код:** {invite.code}\n"
                    f"**Канал:** {invite.channel.mention} (`{invite.channel.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_group_join(self, channel, user):
        listener_log.info("on_group_join: channel=%s, user=%s", channel, user)
        log_channel = await self.get_log_channel(channel.guild if hasattr(channel, "guild") else None)
        if log_channel:
            embed = disnake.Embed(
                title="Пользователь присоединился к группе",
                description=(
                    f"**Пользователь:** {user.mention} (`{user.id}`)\n"
                    f"**Канал:** {channel.mention if hasattr(channel, 'mention') else str(channel)}"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_group_remove(self, channel, user):
        listener_log.info("on_group_remove: channel=%s, user=%s", channel, user)
        log_channel = await self.get_log_channel(channel.guild if hasattr(channel, "guild") else None)
        if log_channel:
            embed = disnake.Embed(
                title="Пользователь покинул группу",
                description=(
                    f"**Пользователь:** {user.mention} (`{user.id}`)\n"
                    f"**Канал:** {channel.mention if hasattr(channel, 'mention') else str(channel)}"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await log_channel.send(embed=embed)

    # @commands.Cog.listener()
    # async def on_presence_update(self, before, after):
    #     if getattr(after, "bot", False):
    #         return
    #     listener_log.info("on_presence_update: before=%s, after=%s", before, after)
    #     channel = await self.get_log_channel(after.guild)
    #     if channel:
    #         embed = disnake.Embed(
    #             title="Изменено присутствие",
    #             description=(
    #                 f"**Пользователь:** {after.mention if hasattr(after, 'mention') else after}\n"
    #                 f"**До:** {before.status}\n"
    #                 f"**После:** {after.status}"
    #             ),
    #             color=disnake.Color.blurple(),
    #             timestamp=datetime.now()
    #         )
    #         await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        guild = self.bot.get_guild(getattr(payload, "guild_id", None))
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="RAW: Редактировано сообщение",
                description=f"**Payload:** `{payload}`",
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        guild = self.bot.get_guild(getattr(payload, "guild_id", None))
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="RAW: Удалено сообщение",
                description=f"**Payload:** `{payload}`",
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(getattr(payload, "guild_id", None))
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="RAW: Добавлена реакция",
                description=f"**Payload:** `{payload}`",
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(getattr(payload, "guild_id", None))
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="RAW: Удалена реакция",
                description=f"**Payload:** `{payload}`",
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload):
        guild = self.bot.get_guild(getattr(payload, "guild_id", None))
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="RAW: Очищены реакции",
                description=f"**Payload:** `{payload}`",
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload):
        guild = self.bot.get_guild(getattr(payload, "guild_id", None))
        channel = await self.get_log_channel(guild)
        if channel:
            embed = disnake.Embed(
                title="RAW: Очищена одна реакция",
                description=f"**Payload:** `{payload}`",
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_tread_join(self, thread):
        listener_log.info('on_tread_join: %s', thread)
        channel = await self.get_log_channel(thread.guild)
        embed = disnake.Embed(
            title="Создана новая тема",
            description=(
                f"**Тема:** {thread.name} (`{thread.id}`)\n"
                f"**Канал:** {thread.parent.mention if thread.parent else 'N/A'}\n"
                f"**Сервер:** {thread.guild.name} (`{thread.guild.id}`)"
            ),
            color=log_colors["success"],
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        listener_log.info("on_thread_delete: %s", thread)
        channel = await self.get_log_channel(thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Удалена тема",
                description=(
                    f"**Тема:** {thread.name} (`{thread.id}`)\n"
                    f"**Канал:** {thread.parent.mention if thread.parent else 'N/A'}\n"
                    f"**Сервер:** {thread.guild.name} (`{thread.guild.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        listener_log.info("on_thread_update: before=%s, after=%s", before, after)
        channel = await self.get_log_channel(after.guild)
        if channel:
            embed = disnake.Embed(
                title="Изменена тема",
                description=(
                    f"**Тема:** {after.name} (`{after.id}`)\n"
                    f"**Канал:** {after.parent.mention if after.parent else 'N/A'}\n"
                    f"**Сервер:** {after.guild.name} (`{after.guild.id}`)"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_member_join(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_thread_member_join: %s", member)
        channel = await self.get_log_channel(member.thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь присоединился к теме",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Тема:** {member.thread.name} (`{member.thread.id}`)"
                ),
                color=log_colors["success"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member):
        if getattr(member, "bot", False):
            return
        listener_log.info("on_thread_member_remove: %s", member)
        channel = await self.get_log_channel(member.thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Пользователь покинул тему",
                description=(
                    f"**Пользователь:** {member.mention} (`{member.id}`)\n"
                    f"**Тема:** {member.thread.name} (`{member.thread.id}`)"
                ),
                color=log_colors["error"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_members_update(self, thread, before, after):
        listener_log.info("on_thread_members_update: thread=%s, before=%s, after=%s", thread, before, after)
        channel = await self.get_log_channel(thread.guild)
        if channel:
            embed = disnake.Embed(
                title="Обновлены участники темы",
                description=(
                    f"**Тема:** {thread.name} (`{thread.id}`)\n"
                    f"**Количество участников до:** {len(before)}\n"
                    f"**Количество участников после:** {len(after)}"
                ),
                color=log_colors["warning"],
                timestamp=datetime.now()
            )
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Listeners(bot))
    logging.info('Cog Listeners loaded successfully.')
