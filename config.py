import os
from dotenv import load_dotenv

load_dotenv()

bot_settings = {
    'token': os.getenv('TOKEN'),
    'prefix': ['!'],
    'bot_version': '1.1.0',
    'bot_author': 'agzatre',
}

database = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
}

messages = {
    'ru': {
        'current_status': 'Текущие настройки',
        'ping': '🏓 Понг! Задержка: {latency}мс',
        'help': {
            'title': '📖 Помощь по командам',
            'description': 'Список доступных команд и их описание',
            'footer': 'Используйте префикс "!" перед командами'
        },
        'language': {
            'success': '🌐 Язык изменен на: {lang}',
            'no_permission': '⛔ Нужны права управлять сервером',
            'current': 'Текущий язык: {lang}',
            'available': 'Доступные языки: {languages}',
            'select': 'Выберите язык'
        },
        'settings': {
            'title': 'Настройки бота',
            'description': 'Здесь вы можете настроить бота для вашего сервера',
            'developer': 'Разработчик',
            'version': 'Версия',
            'footer': 'Настройте бота под свои нужды',
            'support': 'Сервер поддержки'
        },
        'logging': {
            'categories': {
                'message': {
                    'name': 'Сообщения',
                    'description': (
                        '• Создание/удаление сообщений\n'
                        '• Редактирование сообщений\n'
                        '• Удаление сообщений (в т.ч. массовое)\n'
                        '• Реакции на сообщения\n'
                        '• Действия с прикреплёнными файлами'
                    )
                },
                'voice': {
                    'name': 'Голосовые каналы',
                    'description': (
                        '• Вход/выход из голосового канала\n'
                        '• Перемещение между каналами\n'
                        '• Включение/выключение микрофона\n'
                        '• Включение/выключение звука\n'
                        '• Stage-ивенты (создание/изменение/удаление)'
                    )
                },
                'server': {
                    'name': 'Сервер',
                    'description': (
                        '• Изменение сервера\n'
                        '• Создание/удаление каналов\n'
                        '• Изменение каналов\n'
                        '• Обновление эмодзи и стикеров\n'
                        '• Обновление вебхуков\n'
                        '• Изменение ролей и прав'
                    )
                },
                'user': {
                    'name': 'Пользователи',
                    'description': (
                        '• Заход/выход с сервера\n'
                        '• Бан/разбан участников\n'
                        '• Таймауты участников\n'
                        '• Изменение профилей\n'
                        '• Изменение никнеймов и ролей'
                    )
                },
                'invite': {
                    'name': 'Приглашения',
                    'description': (
                        '• Создание приглашений\n'
                        '• Удаление приглашений\n'
                        '• Использование приглашений\n'
                        '• Изменение настроек приглашений'
                    )
                },
                'automod': {
                    'name': 'Авто-модерация',
                    'description': (
                        '• Создано правило авто-модерации\n'
                        '• Обновлено правило авто-модерации\n'
                        '• Удалено правило авто-модерации\n'
                        '• Действие авто-модерации\n'
                    )
                }
            },
            'title': 'Настройки логирования',
            'description': 'Настройте параметры логирования для вашего сервера',
            'status_enabled': 'Включено',
            'status_disabled': 'Выключено',
            'status_changed': 'Статус логирования изменен',
            'status_label': 'Статус логирования',
            'channel_label': 'Канал для логов',
            'channel_not_set': 'Не установлен',
            'channel_not_found': 'Канал не найден',
            'channel_set': 'Канал для логов установлен: {channel}',
            'select_language': 'Выберите язык',
            'select_channel': 'Выберите канал для логов',
            'detailed_title': 'Детальные настройки',
            'detailed_description': 'Включите/выключите определенные типы логов',
            'automod': {
                'rule_created': 'Создано правило авто-модерации: {rule} (ID: {id})\nТип: {trigger}\nДействия: {actions}\nСоздатель: {creator}',
                'rule_updated': 'Обновлено правило авто-модерации: {rule} (ID: {id})\nТип: {trigger}\nДействия: {actions}\nОбновил: {updater}',
                'rule_deleted': 'Удалено правило авто-модерации: {rule} (ID: {id})\nУдалил: {deleter}',
                'action_triggered': 'Сработало правило авто-модерации: {rule} (ID: {id})\nПользователь: {user} (ID: {user_id})\nКанал: {channel}\nСодержимое: {content}\nПримененные действия:\n{actions}'
            }
        },
        'buttons': {
            'settings': 'Настройки',
            'logging_enable': 'Включить логирование',
            'logging_disable': 'Выключить логирование',
            'detailed_settings': 'Детальные настройки',
            'back': 'Назад',
            'save': 'Сохранить',
            'cancel': 'Отмена',
            'confirm': 'Подтвердить',
            'help': 'Помощь'
        },
        'log_categories': {
            'message': 'сообщения',
            'voice': 'голосовые-каналы',
            'server': 'сервер',
            'user': 'пользователи',
            'invite': 'приглашения',
            'automod': 'Авто-модерация'
        },
        'log_titles': {
            'voice_join': 'Пользователь зашёл в голосовой канал',
            'voice_leave': 'Пользователь вышел из голосового канала',
            'voice_move': 'Пользователь перешёл в другой голосовой канал',
            'voice_mute_on': 'Микрофон выключен',
            'voice_mute_off': 'Микрофон включён',
            'voice_deaf_on': 'Звук выключен',
            'voice_deaf_off': 'Звук включён',
            'message_new': 'Новое сообщение',
            'message_edit': 'Сообщение отредактировано',
            'message_delete': 'Сообщение удалено',
            'message_bulk_delete': 'Удалено несколько сообщений',
            'user_join': 'Пользователь присоединился к серверу',
            'user_leave': 'Пользователь покинул сервер',
            'user_ban': 'Пользователь забанен',
            'user_unban': 'Пользователь разбанен',
            'user_timeout': 'Пользователь получил тайм-аут',
            'user_timeout_remove': 'Тайм-аут пользователя снят',
            'channel_create': 'Создан новый канал',
            'channel_delete': 'Удалён канал',
            'channel_update': 'Изменены настройки канала',
            'thread_create': 'Создана новая тема',
            'thread_delete': 'Удалена тема',
            'thread_update': 'Изменена тема',
            'invite_create': 'Создано приглашение',
            'invite_delete': 'Удалено приглашение',
            'reaction_add': 'Добавлена реакция',
            'reaction_remove': 'Удалена реакция',
            'reaction_clear': 'Очищены реакции',
            'reaction_clear_emoji': 'Очищена одна реакция',
            'role_grant': 'Роль выдана',
            'role_revoke': 'Роль отозвана',
            'nickname_change': 'Изменён никнейм',
            'automod_rule_create': 'Создано правило авто-модерации',
            'automod_rule_update': 'Обновлено правило авто-модерации',
            'automod_rule_delete': 'Удалено правило авто-модерации',
            'automod_action': 'Действие авто-модерации',
            'automod_spam': 'Обнаружен спам',
            'automod_invite': 'Заблокировано приглашение',
            'automod_link': 'Заблокирована ссылка',
            'automod_caps': 'Обнаружен капс'
        },
        'errors': {
            'missing_permissions': 'У вас недостаточно прав для выполнения этой команды',
            'bot_missing_permissions': 'У бота недостаточно прав для выполнения этой команды',
            'command_not_found': 'Команда не найдена',
            'cooldown': 'Пожалуйста, подождите {time} секунд перед использованием этой команды снова',
            'generic_error': 'Произошла ошибка при выполнении команды',
            'not_in_guild': 'Эта команда работает только на серверах',
            'user_not_found': 'Пользователь не найден',
            'channel_not_found': 'Канал не найден',
            'role_not_found': 'Роль не найдена'
        }
    },
    'en': {

        'current_status': 'Current Settings',
        'ping': '🏓 Pong! Latency: {latency}ms',
        'help': {
            'title': '📖 Command Help',
            'description': 'List of available commands and their description',
            'footer': 'Use prefix "!" before commands'
        },
        'language': {
            'success': '🌐 Language changed to: {lang}',
            'no_permission': '⛔ Need manage server permission',
            'current': 'Current language: {lang}',
            'available': 'Available languages: {languages}',
            'select': 'Select language'
        },
        'settings': {
            'title': '⚙ Bot Settings',
            'description': 'Here you can configure the bot for your server',
            'developer': 'Developer',
            'version': 'Version',
            'footer': 'Configure the bot to your needs',
            'support': 'Support Server'
        },
        'logging': {
            'categories': {
                'message': {
                    'name': 'Messages',
                    'description': (
                        '• Message creation/deletion\n'
                        '• Message editing\n'
                        '• Bulk message deletion\n'
                        '• Message reactions\n'
                        '• Attachments actions'
                    )
                },
                'voice': {
                    'name': 'Voice Channels',
                    'description': (
                        '• Joining/leaving voice channels\n'
                        '• Moving between channels\n'
                        '• Microphone mute/unmute\n'
                        '• Sound enable/disable\n'
                        '• Stage events'
                    )
                },
                'server': {
                    'name': 'Server',
                    'description': (
                        '• Server updates\n'
                        '• Channel creation/deletion\n'
                        '• Channel updates\n'
                        '• Emoji/stickers updates\n'
                        '• Webhook updates\n'
                        '• Role/permissions changes'
                    )
                },
                'user': {
                    'name': 'Users',
                    'description': (
                        '• Joining/leaving server\n'
                        '• Member bans/unbans\n'
                        '• Member timeouts\n'
                        '• Profile updates\n'
                        '• Nickname/role changes'
                    )
                },
                'invite': {
                    'name': 'Invites',
                    'description': (
                        '• Invite creation\n'
                        '• Invite deletion\n'
                        '• Invite usage\n'
                        '• Invite settings changes'
                    )
                },
                'automod': {
                    'name': 'Automod',
                    'description': (
                        '• Automod rule created\n'
                        '• Automod rule updated\n'
                        '• Automod rule deleted\n'
                        '• Automod action triggered\n'
                    )
                }
            },
            'title': 'Logging Settings',
            'description': 'Configure logging settings for your server',
            'status_enabled': 'Enabled',
            'status_disabled': 'Disabled',
            'status_changed': 'Logging status changed',
            'status_label': 'Logging status',
            'channel_label': 'Log channel',
            'channel_not_set': 'Not set',
            'channel_not_found': 'Channel not found',
            'channel_set': 'Log channel set to: {channel}',
            'select_channel': 'Select log channel',
            'detailed_title': '⚙ Detailed Settings',
            'detailed_description': 'Enable/disable specific log types',
            'automod': {
                'rule_created': 'Automod rule created: {rule} (ID: {id})\nTrigger: {trigger}\nActions: {actions}\nCreator: {creator}',
                'rule_updated': 'Automod rule updated: {rule} (ID: {id})\nTrigger: {trigger}\nActions: {actions}\nUpdated by: {updater}',
                'rule_deleted': 'Automod rule deleted: {rule} (ID: {id})\nDeleted by: {deleter}',
                'action_triggered': 'Automod action triggered: {rule} (ID: {id})\nUser: {user} (ID: {user_id})\nChannel: {channel}\nContent: {content}\nActions taken:\n{actions}'
            }
        },
        'buttons': {
            'settings': 'Settings',
            'logging_enable': 'Enable logging',
            'logging_disable': 'Disable logging',
            'detailed_settings': 'Detailed settings',
            'back': 'Back',
            'save': 'Save',
            'cancel': 'Cancel',
            'confirm': 'Confirm',
            'help': 'Help'
        },
        'log_categories': {
            'message': 'Message',
            'voice': 'Voice',
            'server': 'Server',
            'user': 'User',
            'invite': 'Invite',
            'automod': 'Automod'
        },
        'log_titles': {
            'voice_join': 'User joined voice channel',
            'voice_leave': 'User left voice channel',
            'voice_move': 'User moved to another voice channel',
            'voice_mute_on': 'Microphone muted',
            'voice_mute_off': 'Microphone unmuted',
            'voice_deaf_on': 'Sound disabled',
            'voice_deaf_off': 'Sound enabled',
            'message_new': 'New message',
            'message_edit': 'Message edited',
            'message_delete': 'Message deleted',
            'message_bulk_delete': 'Bulk messages deleted',
            'user_join': 'User joined the server',
            'user_leave': 'User left the server',
            'user_ban': 'User banned',
            'user_unban': 'User unbanned',
            'user_timeout': 'User timed out',
            'user_timeout_remove': 'User timeout removed',
            'channel_create': 'New channel created',
            'channel_delete': 'Channel deleted',
            'channel_update': 'Channel settings updated',
            'thread_create': 'New thread created',
            'thread_delete': 'Thread deleted',
            'thread_update': 'Thread updated',
            'invite_create': 'Invite created',
            'invite_delete': 'Invite deleted',
            'reaction_add': 'Reaction added',
            'reaction_remove': 'Reaction removed',
            'reaction_clear': 'Reactions cleared',
            'reaction_clear_emoji': 'Reaction emoji cleared',
            'role_grant': 'Role granted',
            'role_revoke': 'Role revoked',
            'nickname_change': 'Nickname changed',
            'automod_rule_create': 'Automod rule created',
            'automod_rule_update': 'Automod rule updated',
            'automod_rule_delete': 'Automod rule deleted',
            'automod_action': 'Automod action triggered',
            'automod_spam': 'Spam detected',
            'automod_invite': 'Invite blocked',
            'automod_link': 'Link blocked',
            'automod_caps': 'Excessive caps detected'
        },
        'errors': {
            'missing_permissions': 'You don\'t have permission to use this command',
            'bot_missing_permissions': 'Bot doesn\'t have permission to execute this command',
            'command_not_found': 'Command not found',
            'cooldown': 'Please wait {time} seconds before using this command again',
            'generic_error': 'An error occurred while executing the command',
            'not_in_guild': 'This command only works in servers',
            'user_not_found': 'User not found',
            'channel_not_found': 'Channel not found',
            'role_not_found': 'Role not found'
        }
    }
}

log_colors = {
    "success": 0x43b581,  #
    "error": 0xf04747,
    "warning": 0xfaa61a,
    "info": 0x7289da,
    "default": 0x2f3136,
    "moderation": 0xffd700
}