from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import MONGODB_URI

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client().get_default_database()


async def close():
    global _client
    if _client:
        _client.close()
        _client = None


async def setup_indexes():
    db = get_db()
    await db.messages.create_index("discord_message_id", unique=True)
    await db.messages.create_index("channel_id")
    await db.messages.create_index("created_at")
    await db.messages.create_index([("response_status.is_answered", 1), ("created_at", 1)])
    await db.messages.create_index("classification.category")
    await db.messages.create_index("classification.tags")
    await db.channels_config.create_index(
        [("guild_id", 1), ("channel_id", 1)], unique=True
    )
    await db.alerts.create_index([("category", 1), ("status", 1)])
    await db.alerts.create_index("last_seen")
