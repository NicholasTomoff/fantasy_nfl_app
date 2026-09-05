from datetime import datetime, timedelta, date, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models import Season, NFLGame
from typing import Optional

async def get_current_season(db: AsyncSession) -> Optional[Season]:
    # First try to find manually marked season
    result = await db.execute(select(Season).filter_by(is_current=True).limit(1))
    season = result.scalars().first()
    if season:
        return season

    # Fallback: detect based on current date
    today = datetime.utcnow().date()
    result = await db.execute(
        select(Season)
        .filter(Season.start_date <= today, Season.end_date >= today)
        .limit(1)
    )
    return result.scalars().first()

async def get_current_week(db: AsyncSession, season_year: int) -> int:
    """
    Returns the current week in progress (one week after the finalized week).
    """
    finalized_week = await get_current_finalized_week(db, season_year)
    return finalized_week + 1

async def get_current_finalized_week(db: AsyncSession, season_year: int) -> int:
    """
    Returns the highest week number where the last game has finished
    at least 12 hours ago (UTC), indicating the week is finalized.
    """
    now = datetime.now(timezone.utc)

    stmt = (
        select(
            NFLGame.week,
            func.max(NFLGame.date)
        )
        .where(NFLGame.season == season_year, NFLGame.stage == "Regular Season")
        .group_by(NFLGame.week)
    )

    result = await db.execute(stmt)
    weeks = result.all()

    if not weeks:
        return 0  # No weeks yet

    finalized_weeks = []
    for week_str, last_game_date in weeks:
        try:
            week_num = int(week_str.replace("Week ", ""))
            if last_game_date is None:
                continue

            # Ensure last_game_date is timezone-aware (assume UTC)
            if last_game_date.tzinfo is None:
                last_game_date = last_game_date.replace(tzinfo=timezone.utc)

            # Add 12-hour buffer
            if last_game_date + timedelta(hours=12) < now:
                finalized_weeks.append(week_num)
        except (ValueError, AttributeError) as e:
            print(f"❌ Skipping invalid week entry {week_str}: {e}")
            continue  # skip invalid entries

    if not finalized_weeks:
        return 0

    return max(finalized_weeks)
