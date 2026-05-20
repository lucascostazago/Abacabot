import asyncio
import logging

import discord

import services.classifier as classifier
import services.message_store as store
import services.pattern_detector as pattern_detector
import services.pre_filter as pre_filter
from config import MONITORED_CHANNEL_IDS

logger = logging.getLogger(__name__)


async def handle(message: discord.Message) -> None:
    if message.author.bot:
        return

    if not message.guild:
        return

    channel_id = message.channel.id
    # Para threads de fórum, verifica o canal pai
    parent_id = getattr(message.channel, "parent_id", None)
    effective_id = parent_id if parent_id is not None else channel_id

    logger.info("Mensagem recebida no canal %s (ID: %s)", getattr(message.channel, "name", "?"), effective_id)

    if MONITORED_CHANNEL_IDS and effective_id not in MONITORED_CHANNEL_IDS:
        logger.info("Canal %s não monitorado. Monitorados: %s", effective_id, MONITORED_CHANNEL_IDS)
        return

    # Ignora o post inicial do fórum — já capturado pelo on_thread_create
    if isinstance(message.channel, discord.Thread) and message.id == message.channel.id:
        return

    # Pré-filtro local: só processa mensagens com sinal de dúvida ou bug
    # (não se aplica a threads de fórum, que são sempre relevantes)
    is_forum_reply = isinstance(message.channel, discord.Thread)
    if not is_forum_reply and not pre_filter.is_relevant(message.content):
        logger.info("Mensagem %s descartada pelo pré-filtro.", message.id)
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

    await pattern_detector.check(
        message_id=str(message.id),
        category=result["category"],
        tags=result.get("tags", []),
    )
