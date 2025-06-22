import logging
from logging.handlers import RotatingFileHandler

import disnake
from disnake.ext import commands

from config import *
from utils.database import Database

bot = commands.InteractionBot(
    intents=disnake.Intents.default(),
    status=disnake.Status.dnd,
    test_guilds=[1385464805736972349])

file_log = RotatingFileHandler('./logs/logs.log', maxBytes=1 * 1024 * 1024 * 1024, backupCount=5)
console_out = logging.StreamHandler()

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s  [%(filename)s: %(funcName)s]',
                    datefmt='%m.%d.%Y %H:%M:%S',
                    level=logging.INFO)

db = Database()


def main():
    @bot.event
    async def on_ready():
        logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')

    bot.load_extensions("cogs")
    logging.info('All cogs are loaded')
    bot.run(bot_settings['token'])


if __name__ == '__main__':
    main()
