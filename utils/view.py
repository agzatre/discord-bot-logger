from typing import Optional, Dict

import disnake
from disnake.ext import commands

from utils.database import Database


class BotSettingsView(disnake.ui.View):
    def __init__(self, bot: commands.Bot, db: Database, guild: disnake.Guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.guild = guild
        self.current_settings: Optional[Dict] = None

    async def get_settings(self) -> Dict:
        if not self.current_settings:
            self.current_settings = await self.db.get_log_settings(self.guild.id) or {
                "log_channel_id": 0,
                "logging_enabled": False,
                "log_types": "message:0,invite:0,server:0,voice:0,user:0"
            }
        return self.current_settings

    @disnake.ui.button(label="Настройки", style=disnake.ButtonStyle.blurple, row=0)
    async def settings_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        settings = await self.get_settings()

        embed = disnake.Embed(
            title="Настройки логирования",
            description="Управление параметрами логирования на сервере",
            color=0x2b2d31
        )

        status = "Включено" if settings.get("logging_enabled", False) else "Выключено"
        embed.add_field(name="Статус логирования", value=status, inline=False)

        log_channel = "Не установлен"
        if settings.get("log_channel_id", 0):
            channel = self.guild.get_channel(settings["log_channel_id"])
            log_channel = channel.mention if channel else "Канал не найден"
        embed.add_field(name="Лог-канал", value=log_channel, inline=False)

        view = disnake.ui.View()
        view.add_item(LogChannelSelect(self.db, self.guild))

        logging_enabled = settings.get("logging_enabled", False)
        toggle_button = ToggleLoggingButton(self.db, self.guild, logging_enabled)
        view.add_item(toggle_button)

        if logging_enabled:
            view.add_item(DetailedSettingsButton(self.db, self.guild))

        view.add_item(BackButton(self.db, self.guild))

        await inter.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(label="GitHub", style=disnake.ButtonStyle.link, row=0,
                       url="https://github.com/agzatre/discord-logger-bot")
    async def github_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass


class LogChannelSelect(disnake.ui.ChannelSelect):
    def __init__(self, db: Database, guild: disnake.Guild):
        super().__init__(
            placeholder="Выберите канал для логов",
            channel_types=[disnake.ChannelType.text],
            min_values=1,
            max_values=1
        )
        self.db = db
        self.guild = guild

    async def callback(self, inter: disnake.MessageInteraction):
        channel_id = self.values[0].id
        await self.db.set_log_channel(self.guild.id, channel_id)

        embed = disnake.Embed(
            title="Лог-канал установлен",
            description=f"Канал {self.values[0].mention} теперь будет использоваться для логов",
            color=0x2b2d31
        )

        await inter.response.edit_message(embed=embed)


class ToggleLoggingButton(disnake.ui.Button):
    def __init__(self, db: Database, guild: disnake.Guild, is_enabled: bool):
        self.db = db
        self.guild = guild

        if is_enabled:
            super().__init__(
                label="Выключить логирование",
                style=disnake.ButtonStyle.red
            )
        else:
            super().__init__(
                label="Включить логирование",
                style=disnake.ButtonStyle.green
            )

    async def callback(self, inter: disnake.MessageInteraction):
        settings = await self.db.get_log_settings(self.guild.id) or {}
        current_status = settings.get("logging_enabled", False)
        new_status = not current_status

        await self.db.set_logging_enabled(self.guild.id, new_status)

        if new_status:
            self.label = "Выключить логирование"
            self.style = disnake.ButtonStyle.red
        else:
            self.label = "Включить логирование"
            self.style = disnake.ButtonStyle.green

        embed = disnake.Embed(
            title="Статус логирования изменён",
            description=f"Логирование теперь {'включено' if new_status else 'выключено'}",
            color=0x2b2d31
        )

        view = disnake.ui.View()
        view.add_item(LogChannelSelect(self.db, self.guild))
        view.add_item(self)

        if new_status:
            view.add_item(DetailedSettingsButton(self.db, self.guild))

        view.add_item(BackButton(self.db, self.guild))

        await inter.response.edit_message(embed=embed, view=view)


class DetailedSettingsButton(disnake.ui.Button):
    def __init__(self, db: Database, guild: disnake.Guild):
        super().__init__(
            label="Детальные настройки",
            style=disnake.ButtonStyle.grey
        )
        self.db = db
        self.guild = guild

    async def callback(self, inter: disnake.MessageInteraction):
        settings = await self.db.get_log_settings(self.guild.id) or {}
        log_types = settings.get("log_types", "message:0,invite:0,server:0,voice:0,user:0")

        types = {}
        for pair in log_types.split(","):
            k, v = pair.split(":")
            types[k] = v == "1"

        embed = disnake.Embed(
            title="Детальные настройки логирования",
            description="Выберите какие события должны логироваться:",
            color=0x2b2d31
        )

        categories = {
            "message": {
                "name": "📝 Сообщения",
                "description": (
                    "• Создание/удаление сообщений\n"
                    "• Редактирование сообщений\n"
                    "• Удаление сообщений (в т.ч. массовое)\n"
                    "• Реакции на сообщения\n"
                    "• Действия с прикреплёнными файлами"
                )
            },
            "voice": {
                "name": "🎤 Голосовые каналы",
                "description": (
                    "• Вход/выход из голосового канала\n"
                    "• Перемещение между каналами\n"
                    "• Включение/выключение микрофона\n"
                    "• Включение/выключение звука\n"
                    "• Stage-ивенты (создание/изменение/удаление)"
                )
            },
            "server": {
                "name": "🏰 Сервер",
                "description": (
                    "• Изменение сервера\n"
                    "• Создание/удаление каналов\n"
                    "• Изменение каналов\n"
                    "• Обновление эмодзи и стикеров\n"
                    "• Обновление вебхуков\n"
                    "• Изменение ролей и прав"
                )
            },
            "user": {
                "name": "👥 Пользователи",
                "description": (
                    "• Заход/выход с сервера\n"
                    "• Бан/разбан участников\n"
                    "• Таймауты участников\n"
                    "• Изменение профилей\n"
                    "• Изменение никнеймов и ролей"
                )
            },
            "invite": {
                "name": "📩 Приглашения",
                "description": (
                    "• Создание приглашений\n"
                    "• Удаление приглашений\n"
                    "• Использование приглашений\n"
                    "• Изменение настроек приглашений"
                )
            }
        }

        for log_type, data in categories.items():
            embed.add_field(
                name=data["name"],
                value=f"```{data['description']}```",
                inline=False
            )

        view = disnake.ui.View()

        for log_type, data in categories.items():
            view.add_item(LogTypeToggleButton(
                data["name"].split(" ")[1],  # Берем только название без эмодзи
                log_type,
                types.get(log_type, False),
                self.db,
                self.guild
            ))

        view.add_item(BackButton(self.db, self.guild, back_to="settings"))

        await inter.response.edit_message(embed=embed, view=view)


class LogTypeToggleButton(disnake.ui.Button):
    def __init__(self, label: str, log_type: str, is_enabled: bool, db: Database, guild: disnake.Guild):
        self.log_type = log_type
        self.db = db
        self.guild = guild

        super().__init__(
            label=label,
            style=disnake.ButtonStyle.green if is_enabled else disnake.ButtonStyle.red
        )

    async def callback(self, inter: disnake.MessageInteraction):
        settings = await self.db.get_log_settings(self.guild.id) or {}
        log_types = settings.get("log_types", "message:0,invite:0,server:0,voice:0,user:0")

        types = {}
        for pair in log_types.split(","):
            k, v = pair.split(":")
            types[k] = v

        current_value = types.get(self.log_type, "0")
        types[self.log_type] = "1" if current_value == "0" else "0"

        new_types = ",".join([f"{k}:{v}" for k, v in types.items()])
        await self.db.set_log_types(self.guild.id, new_types)

        self.style = disnake.ButtonStyle.green if types[self.log_type] == "1" else disnake.ButtonStyle.red
        await inter.response.edit_message(view=self.view)


class BackButton(disnake.ui.Button):
    def __init__(self, db: Database, guild: disnake.Guild, back_to: str = "main"):
        self.db = db
        self.guild = guild
        self.back_to = back_to
        super().__init__(
            label="Назад",
            style=disnake.ButtonStyle.grey
        )

    async def callback(self, inter: disnake.MessageInteraction):
        if self.back_to == "main":
            embed = disnake.Embed(
                title="Настройки бота",
                description='Основные настройки логирования и мониторинга событий на сервере',
                color=0x2b2d31
            )
            embed.add_field(name="Разработчик", value="`agzatre`", inline=True)
            embed.add_field(name="Версия", value="1.0.0", inline=True)
            embed.set_footer(text="© 2024 agzatre")
            embed.set_author(icon_url=inter.guild.icon.url if inter.guild.icon else None, name=inter.guild.name)
            embed.set_thumbnail(url=inter.bot.user.avatar.url if inter.bot.user.avatar else None)

            view = BotSettingsView(inter.bot, self.db, inter.guild)
            await inter.response.edit_message(embed=embed, view=view)
        else:
            settings = await self.db.get_log_settings(inter.guild.id) or {}

            embed = disnake.Embed(
                title="Настройки логирования",
                description="Управление параметрами логирования на сервере",
                color=0x2b2d31
            )

            status = "Включено" if settings.get("logging_enabled", False) else "Выключено"
            embed.add_field(name="Статус логирования", value=status, inline=False)

            log_channel = "Не установлен"
            if settings.get("log_channel_id", 0):
                channel = inter.guild.get_channel(settings["log_channel_id"])
                log_channel = channel.mention if channel else "Канал не найден"
            embed.add_field(name="Лог-канал", value=log_channel, inline=False)

            view = disnake.ui.View()
            view.add_item(LogChannelSelect(self.db, inter.guild))

            toggle_button = ToggleLoggingButton(self.db, inter.guild, settings.get("logging_enabled", False))
            view.add_item(toggle_button)

            if settings.get("logging_enabled", False):
                view.add_item(DetailedSettingsButton(self.db, inter.guild))

            view.add_item(BackButton(self.db, inter.guild))

            await inter.response.edit_message(embed=embed, view=view)
