import logging

from utils.view import *


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def cog_load(self):
        await self.db.connect()
        logging.info("Database connected successfully")

    @commands.slash_command(name="ping", description="Проверить задержку бота")
    async def ping(self, inter):
        latency = round(self.bot.latency * 1000)
        await inter.response.send_message(f'Pong! Задержка: {latency}мс', ephemeral=True)

    @commands.slash_command(name="setting", description="Показать настройки бота")
    async def settings(self, inter: disnake.AppCmdInter):
        view = BotSettingsView(self.bot, self.db, inter.guild)
        embed = disnake.Embed(
            title="Настройки бота",
            description='Основные настройки логирования и мониторинга событий на сервере',
            color=0x2b2d31
        )
        embed.add_field(name="Разработчик", value="`agzatre`", inline=True)
        embed.add_field(name="Версия", value="1.0.0", inline=True)
        embed.set_footer(text="agzatre © Copyright 2025  ・  Все права защищены")
        embed.set_author(icon_url=inter.guild.icon.url if inter.guild.icon else None, name=inter.guild.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        await inter.response.send_message(view=view, embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Commands(bot))
    logging.info("Cog Commands loaded successfully.")