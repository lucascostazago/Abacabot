import logging
from datetime import datetime, timezone

import discord
from discord.ext import tasks

import services.message_store as store
from config import UNANSWERED_THRESHOLD_HOURS

logger = logging.getLogger(__name__)

ESCALATION_HOURS = UNANSWERED_THRESHOLD_HOURS * 2


@tasks.loop(minutes=30)
async def scan():
    logger.info("Scanner: verificando mensagens sem resposta...")
    unanswered = await store.find_unanswered(threshold_hours=1)

    now = datetime.now(timezone.utc)
    escalated_count = 0

    for doc in unanswered:
        created_at = doc["response_status"].get("answered_at") or doc["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        hours = (now - created_at).total_seconds() / 3600
        escalated = hours >= ESCALATION_HOURS

        if escalated and not doc["response_status"].get("urgency_escalated"):
            escalated_count += 1

        await store.update_hours_without_reply(
            doc["discord_message_id"],
            round(hours, 1),
            escalated,
        )

    logger.info(
        "Scanner: %d mensagens sem resposta encontradas, %d escaladas.",
        len(unanswered),
        escalated_count,
    )


@scan.before_loop
async def before_scan():
    await discord.utils.sleep_until(discord.utils.utcnow())
