import asyncio
import logging

import discord

import services.classifier as classifier
import services.message_store as store
from config import MONITORED_CHANNEL_IDS

logger = logging.getLogger(__name__)


async def handle(message: discord.Message) -> None:
    if message.author.bot:
        return

    if not message.guild:
        return

    channel_id = message.channel.id
    logger.info("Mensagem recebida no canal %s (ID: %s)", getattr(message.channel, "name", "?"), channel_id)

    if MONITORED_CHANNEL_IDS and channel_id not in MONITORED_CHANNEL_IDS:
        logger.info("Canal %s não monitorado. Monitorados: %s", channel_id, MONITORED_CHANNEL_IDS)
        return

    mongo_id = await store.save_raw(message)
    if not mongo_id:
        logger.warning("Mensagem %s já existe ou falhou ao salvar.", message.id)
        return

    asyncio.create_task(_classify(message))


async def _classify(message: discord.Message) -> None:
    channel_name = getattr(message.channel, "name", str(message.channel.id))

    recent_context: list[str] = []
    try:
        history = [
            m async for m in message.channel.history(limit=5, before=message)
            if not m.author.bot and m.id != message.id
        ]
        recent_context = [m.content for m in reversed(history) if m.content]
    except discord.Forbidden:
        pass

    result = await classifier.analyze(
        content=message.content,
        channel_name=channel_name,
        recent_context=recent_context,
    )

    await store.update_classification(str(message.id), result)
    logger.info(
        "Classificado [%s] canal=#%s categoria=%s urgência=%s",
        message.id,
        channel_name,
        result["category"],
        result["urgency"],
    )
