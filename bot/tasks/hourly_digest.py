import logging
from datetime import datetime, timedelta, timezone

from discord.ext import tasks

import services.slack_notifier as slack
from db.client import get_db

logger = logging.getLogger(__name__)


@tasks.loop(hours=1)
async def send():
    logger.info("Digest: coletando dados da última hora...")
    db = get_db()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    new_cursor = db.messages.find(
        {"ingested_at": {"$gte": one_hour_ago}, "classification.status": "done"},
    )
    new_messages = await new_cursor.to_list(length=1000)

    by_category: dict[str, int] = {}
    by_urgency: dict[str, int] = {}
    for msg in new_messages:
        cat = msg.get("classification", {}).get("category", "unknown")
        urg = msg.get("classification", {}).get("urgency", "low")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_urgency[urg] = by_urgency.get(urg, 0) + 1

    unanswered_cursor = db.messages.find(
        {
            "response_status.is_answered": False,
            "classification.category": {"$in": ["bug", "question"]},
        },
        sort=[("classification.urgency", -1), ("created_at", 1)],
    )
    unanswered = await unanswered_cursor.to_list(length=100)

    slack.send_hourly_digest(
        new_messages=len(new_messages),
        unanswered_total=len(unanswered),
        by_category=by_category,
        by_urgency=by_urgency,
        top_unanswered=unanswered[:5],
    )

    logger.info(
        "Digest enviado: %d novas mensagens, %d sem resposta.",
        len(new_messages),
        len(unanswered),
    )
