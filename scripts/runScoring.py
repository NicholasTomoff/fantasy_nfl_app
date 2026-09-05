import os
import sys
import logging
import asyncio

# Ensure test DB path is set before imports (if testing)
os.environ.setdefault("FANTASY_DB", "test_fantasy.db")

# Allow imports from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import async_session
from app.models import League, WeeklyScore
from services.scoring import score_week
from sqlalchemy.future import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_scoring_for_weeks(season: int, weeks: list[int]):
    async with async_session() as db:
        result = await db.execute(
            select(League).filter(League.season_year == season)
        )
        leagues = result.scalars().all()
        logger.info(f"🔍 Found {len(leagues)} leagues for season {season}")

        for league in leagues:
            logger.info(f"\n🏈 Scoring League: {league.name} (ID {league.id})")

            for week in weeks:
                result = await db.execute(
                    select(WeeklyScore).filter_by(
                        league_id=league.id,
                        week=week,
                        season=season
                    )
                )
                existing_score = result.scalars().first()

                if existing_score:
                    logger.info(f"⏭️  Week {week} already scored for League {league.id}, skipping.")
                    continue

                logger.info(f"✅ Scoring Week {week} for League {league.id}")
                await score_week(week, season, league.id)

# CLI entry point
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True, help="Target season year (e.g. 2024)")
    parser.add_argument("--weeks", type=int, nargs="+", required=True, help="List of weeks to score (e.g. 1 2 3)")
    args = parser.parse_args()

    asyncio.run(run_scoring_for_weeks(season=args.season, weeks=args.weeks))
