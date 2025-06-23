import disnake
from disnake.ext import commands
from disnake.ui import StringSelect, ChannelSelect, View

from config import messages, log_colors, bot_settings
from utils.database import Database


class BaseButton(disnake.ui.Button):
    def __init__(self, db: Database, guild: disnake.Guild):
        self.db = db
        self.guild = guild
        self.lang = "en"
        super().__init__()

    async def initialize(self):
        self.lang = await self.db.get_language(self.guild.id) or "en"
        self._update_labels()

    def _update_labels(self):
        pass


class BaseSelect:
    def __init__(self, db: Database, guild: disnake.Guild):
        self.db = db
        self.guild = guild
        self.lang = "en"

    async def initialize(self):
        self.lang = await self.db.get_language(self.guild.id) or "en"
        self._update_labels()

    def _update_labels(self):
        pass


class ToggleLoggingButton(BaseButton):
    def __init__(self, db: Database, guild: disnake.Guild, is_enabled: bool):
        self.is_enabled = is_enabled
        super().__init__(db, guild)

    def _update_labels(self):
        self.label = messages[self.lang]['buttons']['logging_disable'] if self.is_enabled else \
            messages[self.lang]['buttons']['logging_enable']
        self.style = disnake.ButtonStyle.red if self.is_enabled else disnake.ButtonStyle.green

    async def callback(self, inter: disnake.MessageInteraction):
        await self.initialize()
        new_status = not self.is_enabled
        await self.db.set_logging_enabled(self.guild.id, new_status)

        embed = disnake.Embed(
            title=messages[self.lang]['logging']['status_changed'],
            color=log_colors["success"]
        )

        view = View()

        channel_select = LogChannelSelect(self.db, self.guild)
        toggle_btn = ToggleLoggingButton(self.db, inter.guild, new_status)
        back_btn = BackButton(self.db, self.guild)

        await channel_select.initialize()
        await toggle_btn.initialize()
        await back_btn.initialize()

        view.add_item(channel_select)
        view.add_item(toggle_btn)

        if new_status:
            detailed_btn = DetailedSettingsButton(self.db, inter.guild)
            await detailed_btn.initialize()
            view.add_item(detailed_btn)

        view.add_item(back_btn)
        await inter.response.edit_message(embed=embed, view=view)


class DetailedSettingsButton(BaseButton):
    def _update_labels(self):
        self.label = messages[self.lang]['buttons']['detailed_settings']
        self.style = disnake.ButtonStyle.grey

    async def callback(self, inter: disnake.MessageInteraction):
        await self.initialize()
        settings = await self.db.get_log_settings(inter.guild.id) or {}

        log_types = {}
        if settings.get("log_types"):
            for item in settings["log_types"].split(','):
                if ':' in item:
                    typ, val = item.split(':')
                    log_types[typ.strip()] = val.strip() == '1'

        embed = disnake.Embed(
            title=messages[self.lang]['logging']['detailed_title'],
            description=messages[self.lang]['logging']['detailed_description'],
            color=log_colors["info"]
        )

        for log_type, data in messages[self.lang]['logging']['categories'].items():
            status = messages[self.lang]['logging']['status_enabled'] if log_types.get(log_type, False) else \
                messages[self.lang]['logging']['status_disabled']

            embed.add_field(
                name=f"{data['name']} ({status})",
                value=data['description'],
                inline=True
            )

        view = View()
        for log_type in messages[self.lang]['logging']['categories'].keys():
            is_enabled = log_types.get(log_type, False)
            btn = LogTypeToggleButton(
                messages[self.lang]['log_categories'][log_type],
                log_type,
                is_enabled,
                self.db,
                self.guild
            )
            await btn.initialize()
            view.add_item(btn)

        back_btn = BackButton(self.db, self.guild, back_to="settings")
        await back_btn.initialize()
        view.add_item(back_btn)

        await inter.response.edit_message(embed=embed, view=view)


class LogTypeToggleButton(BaseButton):
    def __init__(self, label: str, log_type: str, is_enabled: bool, db: Database, guild: disnake.Guild):
        self.label_text = label
        self.log_type = log_type
        self.is_enabled = is_enabled
        super().__init__(db, guild)

    def _update_labels(self):
        self.label = f"{self.label_text}"
        self.style = disnake.ButtonStyle.green if self.is_enabled else disnake.ButtonStyle.red

    async def callback(self, inter: disnake.MessageInteraction):
        await self.initialize()
        settings = await self.db.get_log_settings(inter.guild.id) or {}

        log_types = {}
        if settings.get("log_types"):
            for item in settings["log_types"].split(','):
                if ':' in item:
                    typ, val = item.split(':')
                    log_types[typ.strip()] = val.strip() == '1'

        current_value = log_types.get(self.log_type, False)
        new_value = not current_value

        await self.db.update_log_type(inter.guild.id, self.log_type, new_value)

        self.is_enabled = new_value
        self._update_labels()
        await inter.response.edit_message(view=self.view)


class LanguageSelect(StringSelect):
    def __init__(self, db: Database, guild: disnake.Guild):
        self.db = db
        self.guild = guild
        self.lang = "en"

        options = [
            disnake.SelectOption(label="English", emoji="🇬🇧", value="en"),
            disnake.SelectOption(label="Русский", emoji="🇷🇺", value="ru")
        ]
        super().__init__(
            placeholder="Select language",
            min_values=1,
            max_values=1,
            options=options
        )

    async def initialize(self):
        self.lang = await self.db.get_language(self.guild.id) or "en"
        self._update_labels()

    def _update_labels(self):
        """Обновляет текст селектора согласно текущему языку"""
        self.placeholder = messages[self.lang]['language']['select']

    async def callback(self, inter: disnake.MessageInteraction):
        lang = self.values[0]
        await self.db.set_language(self.guild.id, lang)

        embed = disnake.Embed(
            title=messages[lang]['language']['success'].format(lang=lang.upper()),
            description=messages[lang]['language']['success'].format(lang=lang),
            color=log_colors["success"]
        )

        view = View()
        back_btn = BackButton(self.db, self.guild)
        await back_btn.initialize()
        view.add_item(back_btn)

        await inter.response.edit_message(embed=embed, view=view)


class LogChannelSelect(ChannelSelect):
    def __init__(self, db: Database, guild: disnake.Guild):
        self.db = db
        self.guild = guild
        self.lang = "en"
        super().__init__(
            placeholder="Select channel",
            channel_types=[disnake.ChannelType.text],
            min_values=1,
            max_values=1
        )

    async def initialize(self):
        """Инициализирует селектор с актуальным языком из БД"""
        self.lang = await self.db.get_language(self.guild.id) or "en"
        self._update_labels()

    def _update_labels(self):
        """Обновляет текст селектора согласно текущему языку"""
        self.placeholder = messages[self.lang]['logging']['select_channel']

    async def callback(self, inter: disnake.MessageInteraction):
        await self.initialize()
        channel_id = self.values[0].id
        await self.db.set_log_channel(self.guild.id, channel_id)

        embed = disnake.Embed(
            # title=messages[self.lang]['logging']['channel_set'].format(channel=self.values[0].mention),
            description=messages[self.lang]['logging']['channel_set'].format(channel=self.values[0].mention),
            color=log_colors["success"]
        )

        await inter.response.edit_message(embed=embed)


class BackButton(BaseButton):
    def __init__(self, db: Database, guild: disnake.Guild, back_to: str = "main"):
        self.back_to = back_to
        super().__init__(db, guild)

    def _update_labels(self):
        # self.label = messages[self.lang]['buttons']['back']
        self.emoji = "⬅️"
        self.style = disnake.ButtonStyle.grey

    async def callback(self, inter: disnake.MessageInteraction):
        await self.initialize()

        if self.back_to == "main":
            embed = disnake.Embed(
                title=messages[self.lang]['settings']['title'],
                description=messages[self.lang]['settings']['description'],
                color=log_colors["info"]
            )
            embed.add_field(
                name=messages[self.lang]['settings']['developer'],
                value=f"`{bot_settings['bot_author']}`",
                inline=True
            )
            embed.add_field(
                name=messages[self.lang]['settings']['version'],
                value=bot_settings['bot_version'],
                inline=True
            )
            embed.set_author(
                icon_url=inter.guild.icon.url if inter.guild.icon else None,
                name=inter.guild.name
            )

            view = BotSettingsView(inter.bot, self.db, inter.guild)
            await inter.response.edit_message(embed=embed, view=view)

        elif self.back_to == "settings":
            settings = await self.db.get_log_settings(inter.guild.id) or {}
            lang = await self.db.get_language(inter.guild.id) or "en"

            embed = disnake.Embed(
                title=messages[lang]['logging']['title'],
                description=messages[lang]['logging']['description'],
                color=log_colors["info"]
            )

            status = messages[lang]['logging']['status_enabled'] if settings.get("logging_enabled", False) else \
                messages[lang]['logging']['status_disabled']
            embed.add_field(
                name=messages[lang]['logging']['status_label'],
                value=status,
                inline=False
            )

            log_channel = messages[lang]['logging']['channel_not_set']
            if settings.get("log_channel_id"):
                channel = inter.guild.get_channel(settings["log_channel_id"])
                log_channel = channel.mention if channel else messages[lang]['logging']['channel_not_found']
            embed.add_field(
                name=messages[lang]['logging']['channel_label'],
                value=log_channel,
                inline=False
            )

            view = View()
            channel_select = LogChannelSelect(self.db, inter.guild)
            toggle_btn = ToggleLoggingButton(self.db, inter.guild, settings.get("logging_enabled", False))
            back_btn = BackButton(self.db, inter.guild)

            await channel_select.initialize()
            await toggle_btn.initialize()
            await back_btn.initialize()

            view.add_item(channel_select)
            view.add_item(toggle_btn)

            if settings.get("logging_enabled", False):
                detailed_btn = DetailedSettingsButton(self.db, inter.guild)
                await detailed_btn.initialize()
                view.add_item(detailed_btn)

            view.add_item(back_btn)
            await inter.response.edit_message(embed=embed, view=view)


class BotSettingsView(View):
    def __init__(self, bot: commands.Bot, db: Database, guild: disnake.Guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.guild = guild

    async def create_button(self, button_class, *args):
        btn = button_class(self.db, self.guild, *args)
        if isinstance(btn, BaseButton):
            await btn.initialize()
        return btn

    @disnake.ui.button(emoji="⚙️", style=disnake.ButtonStyle.grey, row=0)
    async def settings_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        settings = await self.db.get_log_settings(inter.guild.id) or {}
        lang = await self.db.get_language(inter.guild.id) or "en"

        embed = disnake.Embed(
            title=messages[lang]['logging']['title'],
            description=messages[lang]['logging']['description'],
            color=log_colors["info"]
        )

        status = messages[lang]['logging']['status_enabled'] if settings.get("logging_enabled", False) else \
            messages[lang]['logging']['status_disabled']
        embed.add_field(
            name=messages[lang]['logging']['status_label'],
            value=status,
            inline=False
        )

        log_channel = messages[lang]['logging']['channel_not_set']
        if settings.get("log_channel_id"):
            channel = inter.guild.get_channel(settings["log_channel_id"])
            log_channel = channel.mention if channel else messages[lang]['logging']['channel_not_found']
        embed.add_field(
            name=messages[lang]['logging']['channel_label'],
            value=log_channel,
            inline=False
        )

        view = View()
        channel_select = LogChannelSelect(self.db, inter.guild)
        toggle_btn = await self.create_button(ToggleLoggingButton, settings.get("logging_enabled", False))
        back_btn = await self.create_button(BackButton)

        await channel_select.initialize()
        view.add_item(channel_select)
        view.add_item(toggle_btn)

        if settings.get("logging_enabled", False):
            detailed_btn = await self.create_button(DetailedSettingsButton)
            view.add_item(detailed_btn)

        view.add_item(back_btn)
        await inter.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(emoji="🌐", style=disnake.ButtonStyle.grey, row=0)
    async def language_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        lang = await self.db.get_language(inter.guild.id) or "en"

        embed = disnake.Embed(
            title=messages[lang]['language']['current'].format(lang=lang.upper()),
            description=messages[lang]['language']['available'].format(languages="🇬🇧 English, 🇷🇺 Русский"),
            color=log_colors["info"]
        )

        view = View()
        lang_select = LanguageSelect(self.db, inter.guild)
        back_btn = await self.create_button(BackButton)

        await lang_select.initialize()
        view.add_item(lang_select)
        view.add_item(back_btn)

        await inter.response.edit_message(embed=embed, view=view)

    @disnake.ui.button(label="GitHub", style=disnake.ButtonStyle.link, row=0,
                       url="https://github.com/agzatre/discord-logger-bot")
    async def github_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass
