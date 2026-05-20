import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from db.client import get_db
import services.slack_notifier as slack

logger = logging.getLogger(__name__)

WINDOW_DAYS = 5
MIN_REPORTS = 3


async def check(message_id: str, category: str, tags: list[str]) -> None:
    if category in ("off_topic", "unknown", "praise") or not tags:
        return

    similar = await _find_similar(category, tags)

    if len(similar) < MIN_REPORTS:
        return

    all_ids = list({doc["discord_message_id"] for doc in similar} | {message_id})
    is_new = await _upsert_alert(category, tags, all_ids)

    logger.warning(
        "ALERTA DE PADRÃO: %d relatos de '%s' com tags %s nos últimos %d dias.",
        len(all_ids),
        category,
        tags,
        WINDOW_DAYS,
    )

    if is_new:
        slack.send_pattern_alert(
            category=category,
            tags=tags,
            count=len(all_ids),
            window_days=WINDOW_DAYS,
        )


async def _find_similar(category: str, tags: list[str]) -> list[dict[str, Any]]:
    db = get_db()
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)

    cursor = db.messages.find(
        {
            "classification.category": category,
            "classification.tags": {"$in": tags},
            "created_at": {"$gte": cutoff},
            "classification.status": "done",
        },
        {"discord_message_id": 1, "classification.tags": 1},
    )
    return await cursor.to_list(length=200)


async def _upsert_alert(category: str, tags: list[str], message_ids: list[str]) -> bool:
    """Retorna True se o alerta é novo (primeira vez que atinge o threshold)."""
    db = get_db()
    now = datetime.now(timezone.utc)

    existing = await db.alerts.find_one(
        {"category": category, "tags": {"$in": tags}, "status": "open"}
    )

    if existing:
        merged_ids = list(set(existing.get("message_ids", []) + message_ids))
        await db.alerts.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "message_ids": merged_ids,
                    "count": len(merged_ids),
                    "last_seen": now,
                }
            },
        )
        return False
    else:
        await db.alerts.insert_one(
            {
                "category": category,
                "tags": tags,
                "message_ids": message_ids,
                "count": len(message_ids),
                "status": "open",
                "first_seen": now,
                "last_seen": now,
            }
        )
        return True
