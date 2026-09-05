import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSession, async_engine
from services.streak_history_service import generate_streak_history_for_season

async def main():
    async with AsyncSession(async_engine) as session:
        await generate_streak_history_for_season(2025, session)

if __name__ == "__main__":
    asyncio.run(main())
