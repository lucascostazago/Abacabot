import asyncio
import logging

import discord

import services.classifier as classifier
import services.message_store as store
import services.pattern_detector as pattern_detector
from config import MONITORED_CHANNEL_IDS

logger = logging.getLogger(__name__)


async def handle(thread: discord.Thread) -> None:
    if not isinstance(thread.parent, discord.ForumChannel):
        return

    if MONITORED_CHANNEL_IDS and thread.parent_id not in MONITORED_CHANNEL_IDS:
        return

    # O primeiro post do fórum fica no starter_message da thread
    try:
        message = await thread.fetch_message(thread.id)
    except (discord.NotFound, discord.Forbidden):
        return

    if message.author.bot:
        return

    mongo_id = await store.save_raw(message)
    if not mongo_id:
        return

    asyncio.create_task(_classify(message, thread.name))
    logger.info("Novo post no fórum [%s] thread='%s'", message.id, thread.name)


async def _classify(message: discord.Message, thread_title: str) -> None:
    channel_name = getattr(message.channel, "name", str(message.channel.id))

    result = await classifier.analyze(
        content=f"{thread_title}\n\n{message.content}",
        channel_name=channel_name,
    )

    await store.update_classification(str(message.id), result)
    logger.info(
        "Classificado post [%s] categoria=%s urgência=%s",
        message.id,
        result["category"],
        result["urgency"],
    )

    await pattern_detector.check(
        message_id=str(message.id),
        category=result["category"],
        tags=result.get("tags", []),
    )
