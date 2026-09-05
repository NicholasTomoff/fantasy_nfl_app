from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.streak_history import StreakSeasonHistory
from app.schemas.streak_history import StreakHistoryOut

router = APIRouter(prefix="/streak-history", tags=["Streak History"])


@router.get("/league/{league_id}", response_model=List[StreakHistoryOut])
async def get_league_history(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StreakSeasonHistory)
        .where(
            StreakSeasonHistory.scope == "league",
            StreakSeasonHistory.league_id == league_id
        )
        .order_by(StreakSeasonHistory.season)
    )
    return result.scalars().all()


@router.get("/global", response_model=List[StreakHistoryOut])
async def get_global_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StreakSeasonHistory)
        .where(StreakSeasonHistory.scope == "global")
        .order_by(StreakSeasonHistory.season)
    )
    return result.scalars().all()
