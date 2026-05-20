from datetime import datetime, timezone
from typing import Any

import discord
from pymongo import ReturnDocument

from db.client import get_db


def _build_raw_doc(message: discord.Message) -> dict[str, Any]:
    roles = []
    if isinstance(message.author, discord.Member):
        roles = [r.name for r in message.author.roles if r.name != "@everyone"]

    return {
        "discord_message_id": str(message.id),
        "guild_id": str(message.guild.id) if message.guild else None,
        "channel_id": str(message.channel.id),
        "channel_name": getattr(message.channel, "name", str(message.channel.id)),
        "thread_id": str(message.channel.id) if isinstance(message.channel, discord.Thread) else None,
        "author_id": str(message.author.id),
        "author_username": message.author.name,
        "author_roles": roles,
        "content": message.content,
        "created_at": message.created_at.replace(tzinfo=timezone.utc) if message.created_at.tzinfo is None else message.created_at,
        "ingested_at": datetime.now(timezone.utc),
        "has_attachments": len(message.attachments) > 0,
        "attachment_urls": [a.url for a in message.attachments],
        "reply_to_message_id": str(message.reference.message_id) if message.reference else None,
        "classification": {
            "status": "pending",
            "category": None,
            "urgency": None,
            "sentiment": None,
            "summary": None,
            "tags": [],
            "confidence": None,
            "classified_at": None,
            "model_used": None,
        },
        "response_status": {
            "is_answered": False,
            "answered_at": None,
            "answered_by_id": None,
            "hours_without_reply": 0.0,
            "urgency_escalated": False,
        },
    }


async def save_raw(message: discord.Message) -> str | None:
    doc = _build_raw_doc(message)
    db = get_db()
    try:
        result = await db.messages.insert_one(doc)
        return str(result.inserted_id)
    except Exception:
        return None


async def update_classification(discord_message_id: str, classification: dict[str, Any]) -> None:
    db = get_db()
    await db.messages.update_one(
        {"discord_message_id": discord_message_id},
        {"$set": {"classification": {**classification, "status": "done"}}},
    )


async def mark_answered(discord_message_id: str, answered_by_id: str) -> None:
    db = get_db()
    await db.messages.update_one(
        {"discord_message_id": discord_message_id},
        {
            "$set": {
                "response_status.is_answered": True,
                "response_status.answered_at": datetime.now(timezone.utc),
                "response_status.answered_by_id": answered_by_id,
            }
        },
    )


async def find_unanswered(threshold_hours: float) -> list[dict[str, Any]]:
    db = get_db()
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
    cursor = db.messages.find(
        {
            "response_status.is_answered": False,
            "created_at": {"$lte": cutoff},
            "classification.category": {"$in": ["bug", "question"]},
        },
        sort=[("created_at", 1)],
    )
    return await cursor.to_list(length=500)


async def update_hours_without_reply(discord_message_id: str, hours: float, escalated: bool) -> None:
    db = get_db()
    await db.messages.update_one(
        {"discord_message_id": discord_message_id},
        {
            "$set": {
                "response_status.hours_without_reply": hours,
                "response_status.urgency_escalated": escalated,
            }
        },
    )
