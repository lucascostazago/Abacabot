import logging

import discord

import services.message_store as store

logger = logging.getLogger(__name__)

RESOLVED_EMOJIS = {"✅", "☑️", "✔️"}


async def handle(reaction: discord.Reaction, user: discord.User | discord.Member) -> None:
    if user.bot:
        return

    if str(reaction.emoji) not in RESOLVED_EMOJIS:
        return

    is_staff = False
    if isinstance(user, discord.Member):
        staff_role_names = {"Time da Abacatepay","Admin"}
        is_staff = any(r.name.lower() in staff_role_names for r in user.roles)

    if not is_staff:
        return

    message = reaction.message
    await store.mark_answered(str(message.id), str(user.id))
    logger.info(
        "Mensagem %s marcada como respondida por %s via reação.",
        message.id,
        user.name,
    )
