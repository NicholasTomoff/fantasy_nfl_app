# file: app/routes/admin.py

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import League, WeeklyScore
from services.scoring import score_week
from services.load_player_game_stats import load_player_stats_for_week
from app.utils.season import get_current_season, get_current_week
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

# --------- Generate weekly scoring from business logic and write to DB ---------
@router.post("/run-weekly")
async def run_weekly_tasks(
    week_number: int | None = Query(None, description="Optional week number, e.g. 1-18"),
    season: int | None = Query(None, description="Optional season year, e.g. 2024"),
    session: AsyncSession = Depends(get_db),
):
    # 🧠 Auto-detect season and week if not provided
    if season is None:
        current_season_obj = await get_current_season(session)
        if current_season_obj is None:
            season = datetime.utcnow().year  # fallback to current year
        else:
            season = current_season_obj.year

    if week_number is None:
        detected_week = await get_current_week(session, season)

        # If we're already in the final week window, lock to previous week
        if detected_week >= 18:
            week_number = 17
        else:
            week_number = detected_week - 1
                    #adding minus one since it pulled the week based on Tues..
        if week_number is None:
            week_number = 1

    if week_number < 1 or week_number > 18:
        raise HTTPException(status_code=400, detail="Invalid week number")

    week_str = f"Week {week_number}"

    # ✅ Launch async background tasks properly
    await load_player_stats_for_week(season, week_str)
    await run_scoring_for_all_leagues(week_number, season)

    return {"message": f"✅ Background tasks running for Week {week_number}, Season {season}"}

async def run_scoring_for_all_leagues(week_number: int, season: int):
    async for db in get_db():
        result = await db.execute(select(League).filter_by(season_year=season))
        leagues = result.scalars().all()

        for league in leagues:
            result = await db.execute(
                select(WeeklyScore).filter_by(
                    league_id=league.id,
                    week=week_number,
                    season=season
                )
            )

            # count users in league
            user_result = await db.execute(
                select(WeeklyScore.user_email)
                .filter_by(league_id=league.id)
                .distinct()
            )
            total_users = len(user_result.scalars().all())

            # count scores for this week
            week_result = await db.execute(
                select(WeeklyScore)
                .filter_by(
                    league_id=league.id,
                    week=week_number,
                    season=season
                )
            )
            scored_users = len(week_result.scalars().all())

            if scored_users >= total_users:
                print(f"⏭️ Week {week_number} fully scored for League {league.id}, skipping.")
                continue

            print(f"✅ Scoring League {league.name} (Week {week_number})")
            await score_week(week_number, season, league.id)
