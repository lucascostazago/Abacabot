import logging

import discord

import bot.events.on_message as on_message_handler
import bot.events.on_reaction as on_reaction_handler
import bot.events.on_thread_create as on_thread_create_handler
from bot.tasks.unanswered_scanner import scan as unanswered_scan
from bot.tasks.hourly_digest import send as hourly_digest
from db.client import setup_indexes

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guilds = True


class CommunityBot(discord.Client):
    async def setup_hook(self) -> None:
        await setup_indexes()
        unanswered_scan.start()
        hourly_digest.start()
        logger.info("Bot pronto. Índices criados, scanner e digest iniciados.")

    async def on_ready(self) -> None:
        logger.info("Conectado como %s (ID: %s)", self.user, self.user.id)
        guilds = [f"{g.name} (ID: {g.id})" for g in self.guilds]
        if guilds:
            logger.info("Servidores: %s", ", ".join(guilds))
        else:
            logger.warning("Bot não está em nenhum servidor! Adicione o bot ao seu servidor Discord.")

    async def on_message(self, message: discord.Message) -> None:
        await on_message_handler.handle(message)

    async def on_thread_create(self, thread: discord.Thread) -> None:
        await on_thread_create_handler.handle(thread)

    async def on_reaction_add(
        self, reaction: discord.Reaction, user: discord.User | discord.Member
    ) -> None:
        await on_reaction_handler.handle(reaction, user)

    async def close(self) -> None:
        unanswered_scan.cancel()
        hourly_digest.cancel()
        from db.client import close as db_close
        await db_close()
        await super().close()
