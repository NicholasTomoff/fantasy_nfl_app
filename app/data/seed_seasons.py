# data/seed_seasons.py

import sys, os, asyncio
from datetime import date
from sqlalchemy import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database import async_session
from app.models import Season


async def seed_seasons():
    async with async_session() as db:
        seasons_data = [
            {
                "year": 2024,
                "start_date": date(2024, 7, 1),
                "end_date": date(2025, 2, 10),
                "is_current": False,
            },
            {
                "year": 2025,
                "start_date": date(2025, 7, 1),
                "end_date": date(2026, 2, 10),
                "is_current": True,
            }
        ]

        for data in seasons_data:
            result = await db.execute(select(Season).filter_by(year=data["year"]))
            existing = result.scalar_one_or_none()

            if not existing:
                db.add(Season(**data))

        await db.commit()
        print("✅ Seeded seasons.")


if __name__ == "__main__":
    asyncio.run(seed_seasons())
