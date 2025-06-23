import logging
from disnake.ext import commands
import disnake

from utils.database import Database
from utils.view import BotSettingsView
from config import messages, bot_settings


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def cog_load(self):
        await self.db.connect()
        logging.info("Database connected successfully")

    @commands.slash_command(name="ping", description="Check bot latency")
    async def ping(self, inter):
        lang = await self.db.get_language(inter.guild.id)
        latency = round(self.bot.latency * 1000)
        await inter.response.send_message(
            messages[lang]['ping'].format(latency=latency),
            ephemeral=True
        )

    @commands.slash_command(name="settings", description="Show bot settings")
    async def settings(self, inter: disnake.ApplicationCommandInteraction):
        lang = await self.db.get_language(inter.guild.id) or "en"
        view = BotSettingsView(self.bot, self.db, inter.guild)

        embed = disnake.Embed(
            title=messages[lang]['settings']['title'],
            description=messages[lang]['settings']['description'],
            color=0x2b2d31
        )
        embed.add_field(
            name=messages[lang]['settings']['developer'],
            value=f"`{bot_settings['bot_author']}`",
            inline=True
        )
        embed.add_field(
            name=messages[lang]['settings']['version'],
            value=bot_settings['bot_version'],
            inline=True
        )
        embed.set_footer(text=messages[lang]['settings']['footer'])
        embed.set_author(
            icon_url=inter.guild.icon.url if inter.guild.icon else None,
            name=inter.guild.name
        )
        embed.set_thumbnail(
            url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )

        await inter.response.send_message(view=view, embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Commands(bot))
    logging.info("Cog Commands loaded successfully.")
