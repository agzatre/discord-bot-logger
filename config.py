import os
from dotenv import load_dotenv

load_dotenv()

bot_settings = {
    'token': (os.getenv('TOKEN')),
    'prefix': ['!'],
}

database = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
}

log_colors = {
    "success": 0x43b581,
    "error": 0xf04747,
    "warning": 0xfaa61a,
    "info": 0x7289da,
    "default": 0x2f3136,
}


