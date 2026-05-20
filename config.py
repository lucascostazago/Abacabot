import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
MONGODB_URI = os.environ["MONGODB_URI"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GUILD_ID = int(os.environ["GUILD_ID"])

_channel_ids = os.getenv("MONITORED_CHANNEL_IDS", "")
MONITORED_CHANNEL_IDS: set[int] = {
    int(cid.strip()) for cid in _channel_ids.split(",") if cid.strip()
}

UNANSWERED_THRESHOLD_HOURS = int(os.getenv("UNANSWERED_THRESHOLD_HOURS", "24"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
