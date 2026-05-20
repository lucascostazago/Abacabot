import asyncio
import logging

from config import DISCORD_TOKEN, LOG_LEVEL
from bot.client import CommunityBot, intents

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    bot = CommunityBot(intents=intents)
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
