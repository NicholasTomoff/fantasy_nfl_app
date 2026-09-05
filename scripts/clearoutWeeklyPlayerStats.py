import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select, delete
from app.database import async_session
from app.models import PlayerGameStat, NFLGame

async def cleanup_player_game_stats(target_week="Week 18", stage="Regular Season"):
    async with async_session() as db:
        try:
            # Find all game IDs for the specified week and stage
            result = await db.execute(
                select(NFLGame).filter_by(week=target_week, stage=stage)
            )
            games = result.scalars().all()
            game_ids = [g.id for g in games]

            if not game_ids:
                print(f"No games found for {target_week} {stage}. Nothing to delete.")
                return

            # Delete PlayerGameStat rows linked to these game IDs
            delete_stmt = delete(PlayerGameStat).where(PlayerGameStat.game_id.in_(game_ids))
            result = await db.execute(delete_stmt)
            await db.commit()

            print(f"🧹 Deleted {result.rowcount} player stat rows for {target_week} {stage}")

        except Exception as e:
            await db.rollback()
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup_player_game_stats())
