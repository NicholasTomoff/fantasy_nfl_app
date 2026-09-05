from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import WeeklyScore, WeeklyPick, PositionStreak, League
from app.db import get_db
from app.scoring import score_week_with_session  # your existing scoring function

async def reset_and_rerun_week(week: int, season: int):
    async for db in get_db():
        # 1️⃣ Delete existing Week 1 WeeklyScore entries
        await db.execute(delete(WeeklyScore).where(WeeklyScore.week == week, WeeklyScore.season == season))
        
        # 2️⃣ Delete PositionStreak entries for this week (optional but safe)
        await db.execute(delete(PositionStreak).where(PositionStreak.week == week, PositionStreak.season == season))
        
        # 3️⃣ Delete any All-Position Bonus entries if separate table
        # await db.execute(delete(AllPositionBonus).where(AllPositionBonus.week == week, AllPositionBonus.season == season))

        # Commit deletions
        await db.commit()

        # 4️⃣ Fetch all leagues for this season
        result = await db.execute(select(League).filter_by(season_year=season))
        leagues = result.scalars().all()

        # 5️⃣ Rerun scoring for each league
        for league in leagues:
            await score_week_with_session(db=db, week=week, league_id=league.id, season=season)
        
        await db.commit()
        print(f"✅ Week {week} scoring reset and rerun for season {season}.")

if __name__ == "__main__":
    asyncio.run(reset_and_rerun_week())

