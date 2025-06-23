import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import disnake
from disnake.ext import commands

from config import messages, log_colors
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

    async def get_lang(self, guild_id):
        return await self.db.get_language(guild_id) or "en"

    async def get_log_channel_id(self, guild):
        if guild is None:
            return None
        row = await self.db.get_log_settings(guild.id)
        return row.get("log_channel_id") if row else None

    async def get_log_channel(self, guild):
        log_channel_id = await self.get_log_channel_id(guild)
        if not log_channel_id:
            return None

        channel = self.bot.get_channel(log_channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(log_channel_id)
            except Exception as e:
                listener_log.error("Failed to fetch log channel: %s", e)
                return None
        return channel

    async def is_logging_enabled(self, guild):
        if guild is None:
            return False
        row = await self.db.get_log_settings(guild.id)
        return bool(row.get("logging_enabled", True)) if row else True

    async def is_log_type_enabled(self, guild, log_type):
        if guild is None:
            return False

        row = await self.db.get_log_settings(guild.id)
        if not row or "log_types" not in row or not row["log_types"]:
            return True

        types = {k: v == "1" for pair in row["log_types"].split(",")
                 for k, v in [pair.split(":")]}
        return types.get(log_type, True)

    async def send_log_embed(self, guild, log_type, title_key, description, color="info"):
        if not await self.is_logging_enabled(guild) or not await self.is_log_type_enabled(guild, log_type):
            return

        channel = await self.get_log_channel(guild)
        if not channel:
            return

        lang = await self.get_lang(guild.id)
        title = messages[lang]['log_titles'].get(title_key, title_key.replace('_', ' ').title())

        embed = disnake.Embed(
            title=title,
            description=description,
            color=log_colors[color],
            timestamp=datetime.now()
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        changes = []

        if before.display_name != after.display_name:
            changes.append(f"Ник: {before.display_name} → {after.display_name}")

        if before.roles != after.roles:
            added = [r.name for r in after.roles if r not in before.roles]
            removed = [r.name for r in before.roles if r not in after.roles]
            if added: changes.append(f"Добавлены роли: {', '.join(added)}")
            if removed: changes.append(f"Удалены роли: {', '.join(removed)}")

        if not changes:
            return

        await self.send_log_embed(
            after.guild,
            "user",
            "user_update",
            f"**Участник:** {after.mention}\n" + "\n".join(changes),
            "info"
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if getattr(member, "bot", False):
            return

        lang = await self.get_lang(member.guild.id)

        if before.channel is None and after.channel is not None:
            await self.send_log_embed(
                member.guild,
                'voice',
                'voice_join',
                f"{member.mention} (`{member.id}`) joined {after.channel.mention} (`{after.channel.id}`)",
                "success"
            )
        elif before.channel is not None and after.channel is None:
            await self.send_log_embed(
                member.guild,
                'voice',
                'voice_leave',
                f"{member.mention} (`{member.id}`) left {before.channel.mention} (`{before.channel.id}`)",
                "error"
            )
        elif before.channel != after.channel:
            await self.send_log_embed(
                member.guild,
                'voice',
                'voice_move',
                f"{member.mention} (`{member.id}`) moved from {before.channel.mention} to {after.channel.mention}",
                "info"
            )

        if before.self_mute != after.self_mute:
            action = "muted" if after.self_mute else "unmuted"
            await self.send_log_embed(
                member.guild,
                'voice',
                f'voice_mute_{"on" if after.self_mute else "off"}',
                f"{member.mention} (`{member.id}`) {action} microphone",
                "warning" if after.self_mute else "success"
            )

        if before.self_deaf != after.self_deaf:
            action = "deafened" if after.self_deaf else "undeafened"
            await self.send_log_embed(
                member.guild,
                'voice',
                f'voice_deaf_{"on" if after.self_deaf else "off"}',
                f"{member.mention} (`{member.id}`) {action}",
                "warning" if after.self_deaf else "success"
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if getattr(message.author, "bot", False):
            return

        await self.send_log_embed(
            message.guild,
            'message',
            'message_new',
            f"**Channel:** {message.channel.mention} (`{message.channel.id}`)\n"
            f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
            f"**Content:** {message.content}",
            "success"
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if getattr(before.author, "bot", False):
            return

        await self.send_log_embed(
            before.guild,
            'message',
            'message_edit',
            f"**Channel:** {before.channel.mention} (`{before.channel.id}`)\n"
            f"**Author:** {before.author.mention} (`{before.author.id}`)\n"
            f"**Before:** {before.content}\n"
            f"**After:** {after.content}",
            "warning"
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if getattr(message.author, "bot", False):
            return

        await self.send_log_embed(
            message.guild,
            'message',
            'message_delete',
            f"**Channel:** {message.channel.mention} (`{message.channel.id}`)\n"
            f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
            f"**Content:** {message.content}",
            "error"
        )

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages or getattr(messages[0].author, "bot", False):
            return

        await self.send_log_embed(
            messages[0].guild,
            'message',
            'message_bulk_delete',
            f"**Channel:** {messages[0].channel.mention} (`{messages[0].channel.id}`)\n"
            f"**Count:** {len(messages)}",
            "error"
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        await self.send_log_embed(
            member.guild,
            "user",
            "user_join",
            f"**member:** {member.mention}\n**guild:** {member.guild.name}",
            "success"
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        await self.send_log_embed(
            member.guild,
            "user",
            "user_leave",
            f"**member:** {member.mention}\n**guild:** {member.guild.name}",
            "error"
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if getattr(user, "bot", False):
            return

        await self.send_log_embed(
            guild,
            'user',
            'user_ban',
            f"**User:** {getattr(user, 'mention', user)} (`{getattr(user, 'id', 'N/A')}`)\n"
            f"**Server:** {guild.name} (`{guild.id}`)",
            "error"
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if getattr(user, "bot", False):
            return

        await self.send_log_embed(
            guild,
            'user',
            'user_unban',
            f"**User:** {getattr(user, 'mention', user)} (`{getattr(user, 'id', 'N/A')}`)\n"
            f"**Server:** {guild.name} (`{guild.id}`)",
            "success"
        )

    @commands.Cog.listener()
    async def on_member_timeout(self, member, until):
        if getattr(member, "bot", False):
            return

        await self.send_log_embed(
            member.guild,
            'user',
            'user_timeout',
            f"**User:** {member.mention} (`{member.id}`)\n"
            f"**Server:** {member.guild.name} (`{member.guild.id}`)\n"
            f"**Until:** {until.strftime('%d.%m.%Y %H:%M:%S') if until else 'None'}",
            "warning"
        )

    @commands.Cog.listener()
    async def on_member_timeout_remove(self, member):
        if getattr(member, "bot", False):
            return

        await self.send_log_embed(
            member.guild,
            'user',
            'user_timeout_remove',
            f"**User:** {member.mention} (`{member.id}`)\n"
            f"**Server:** {member.guild.name} (`{member.guild.id}`)",
            "success"
        )

    # Серверные события
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log_embed(
            channel.guild,
            'server',
            'channel_create',
            f"**Channel:** {channel.mention} (`{channel.id}`)\n"
            f"**Server:** {channel.guild.name} (`{channel.guild.id}`)",
            "success"
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log_embed(
            channel.guild,
            'server',
            'channel_delete',
            f"**Channel:** {channel.mention if hasattr(channel, 'mention') else channel.name} (`{channel.id}`)\n"
            f"**Server:** {channel.guild.name} (`{channel.guild.id}`)",
            "error"
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        await self.send_log_embed(
            after.guild,
            'server',
            'channel_update',
            f"**Channel:** {after.mention} (`{after.id}`)\n"
            f"**Server:** {after.guild.name} (`{after.guild.id}`)\n"
            f"**Changes:** {before} → {after}",
            "warning"
        )

    # Треды
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        await self.send_log_embed(
            thread.guild,
            'server',
            'thread_create',
            f"**Thread:** {thread.name} (`{thread.id}`)\n"
            f"**Parent:** {thread.parent.mention if thread.parent else 'N/A'}\n"
            f"**Server:** {thread.guild.name} (`{thread.guild.id}`)",
            "success"
        )

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        await self.send_log_embed(
            thread.guild,
            'server',
            'thread_delete',
            f"**Thread:** {thread.name} (`{thread.id}`)\n"
            f"**Parent:** {thread.parent.mention if thread.parent else 'N/A'}\n"
            f"**Server:** {thread.guild.name} (`{thread.guild.id}`)",
            "error"
        )

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        await self.send_log_embed(
            after,
            'server',
            'guild_update',
            f"**Server:** {after.name} (`{after.id}`)\n"
            f"**Changes:** {before} → {after}",
            "warning"
        )

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        guild = getattr(invite.channel, 'guild', None)
        if guild:
            await self.send_log_embed(
                guild,
                'invite',
                'invite_create',
                f"**Code:** {invite.code}\n"
                f"**Channel:** {invite.channel.mention} (`{invite.channel.id}`)\n"
                f"**Inviter:** {invite.inviter.mention if invite.inviter else 'N/A'}",
                "success"
            )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        guild = getattr(invite.channel, 'guild', None)
        if guild:
            await self.send_log_embed(
                guild,
                'invite',
                'invite_delete',
                f"**Code:** {invite.code}\n"
                f"**Channel:** {invite.channel.mention} (`{invite.channel.id}`)",
                "error"
            )

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        await self.send_log_embed(
            guild,
            'server',
            'emojis_update',
            f"**Server:** {guild.name} (`{guild.id}`)\n"
            f"**Before:** {len(before)} emojis\n"
            f"**After:** {len(after)} emojis",
            "warning"
        )

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        await self.send_log_embed(
            guild,
            'server',
            'stickers_update',
            f"**Server:** {guild.name} (`{guild.id}`)\n"
            f"**Before:** {len(before)} stickers\n"
            f"**After:** {len(after)} stickers",
            "warning"
        )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if getattr(user, "bot", False):
            return

        await self.send_log_embed(
            reaction.message.guild,
            'message',
            'reaction_add',
            f"**Emoji:** {reaction.emoji}\n"
            f"**Channel:** {reaction.message.channel.mention} (`{reaction.message.channel.id}`)\n"
            f"**Message:** [Jump]({reaction.message.jump_url}) (`{reaction.message.id}`)\n"
            f"**User:** {user.mention} (`{user.id}`)",
            "success"
        )

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if getattr(user, "bot", False):
            return

        await self.send_log_embed(
            reaction.message.guild,
            'message',
            'reaction_remove',
            f"**Emoji:** {reaction.emoji}\n"
            f"**Channel:** {reaction.message.channel.mention} (`{reaction.message.channel.id}`)\n"
            f"**Message:** [Jump]({reaction.message.jump_url}) (`{reaction.message.id}`)\n"
            f"**User:** {user.mention} (`{user.id}`)",
            "error"
        )

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        if getattr(message.author, "bot", False):
            return

        await self.send_log_embed(
            message.guild,
            'message',
            'reaction_clear',
            f"**Channel:** {message.channel.mention} (`{message.channel.id}`)\n"
            f"**Message:** [Jump]({message.jump_url}) (`{message.id}`)\n"
            f"**Count:** {len(reactions)}",
            "warning"
        )

    @commands.Cog.listener()
    async def on_reaction_clear_emoji(self, reaction):
        if getattr(reaction.message.author, "bot", False):
            return

        await self.send_log_embed(
            reaction.message.guild,
            'message',
            'reaction_clear_emoji',
            f"**Emoji:** {reaction.emoji}\n"
            f"**Channel:** {reaction.message.channel.mention} (`{reaction.message.channel.id}`)\n"
            f"**Message:** [Jump]({reaction.message.jump_url}) (`{reaction.message.id}`)",
            "warning"
        )

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if getattr(user, "bot", False):
            return

        if hasattr(channel, 'guild'):
            await self.send_log_embed(
                channel.guild,
                'message',
                'typing',
                f"**User:** {user.mention} (`{user.id}`)\n"
                f"**Channel:** {channel.mention} (`{channel.id}`)",
                "info"
            )

    # Авто-модерация
    @commands.Cog.listener()
    async def on_automod_rule_create(self, rule):
        lang = await self.get_lang(rule.guild.id)
        await self.send_log_embed(
            rule.guild,
            'automod',
            'automod_rule_create',
            messages[lang]['logging']['automod']['rule_created'].format(
                rule=rule.name,
                id=rule.id,
                trigger=rule.trigger_type.name,
                actions=len(rule.actions),
                creator=rule.creator.mention if rule.creator else 'System'
            ),
            "success"
        )

    @commands.Cog.listener()
    async def on_automod_rule_update(self, rule):
        lang = await self.get_lang(rule.guild.id)
        await self.send_log_embed(
            rule.guild,
            'automod',
            'automod_rule_update',
            messages[lang]['logging']['automod']['rule_updated'].format(
                rule=rule.name,
                id=rule.id,
                trigger=rule.trigger_type.name,
                actions=len(rule.actions),
                updater=rule.creator.mention if rule.creator else 'System'
            ),
            "warning"
        )

    @commands.Cog.listener()
    async def on_automod_rule_delete(self, rule):
        lang = await self.get_lang(rule.guild.id)
        await self.send_log_embed(
            rule.guild,
            'automod',
            'automod_rule_delete',
            messages[lang]['logging']['automod']['rule_deleted'].format(
                rule=rule.name,
                id=rule.id,
                deleter=rule.creator.mention if rule.creator else 'System'
            ),
            "error"
        )

    @commands.Cog.listener()
    async def on_automod_action(self, execution):
        lang = await self.get_lang(execution.guild.id)

        action_str = "\n".join(
            f"• {action.type.name}: {getattr(action.metadata, 'duration', 'N/A')}"
            for action in execution.actions
        )

        await self.send_log_embed(
            execution.guild,
            'automod',
            'automod_action',
            messages[lang]['logging']['automod']['action_triggered'].format(
                rule=execution.rule_name,
                id=execution.rule_id,
                user=execution.member.mention,
                user_id=execution.member.id,
                channel=execution.channel.mention if execution.channel else 'None',
                content=execution.content or 'None',
                actions=action_str
            ),
            "moderation"
        )

def setup(bot):
    bot.add_cog(Listeners(bot))
    logging.info('Cog Listeners loaded successfully.')