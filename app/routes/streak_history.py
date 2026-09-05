from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import StreakSeasonHistory, User
from app.schemas import StreakHistoryOut

router = APIRouter(prefix="/streak-history", tags=["Streak History"])


async def _with_names(rows, db: AsyncSession) -> List[StreakHistoryOut]:
    """
    Attach champion/runner-up/third names. The table stores user ids; the page
    displays names, so resolve them here in a single lookup rather than per row.
    """
    ids = {
        uid
        for r in rows
        for uid in (r.champion_id, r.runner_up_id, r.third_place_id)
        if uid is not None
    }

    names = {}
    if ids:
        result = await db.execute(
            select(User.id, User.name, User.email).where(User.id.in_(ids))
        )
        # fall back to email when a user has no display name set
        names = {uid: (name or email) for uid, name, email in result.all()}

    out = []
    for r in rows:
        item = StreakHistoryOut.model_validate(r)
        item.champion_name = names.get(r.champion_id)
        item.runner_up_name = names.get(r.runner_up_id)
        item.third_place_name = names.get(r.third_place_id)
        out.append(item)
    return out


@router.get("/league/{league_id}", response_model=List[StreakHistoryOut])
async def get_league_history(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StreakSeasonHistory)
        .where(
            StreakSeasonHistory.scope == "league",
            StreakSeasonHistory.league_id == league_id,
        )
        .order_by(StreakSeasonHistory.season)
    )
    return await _with_names(result.scalars().all(), db)


@router.get("/global", response_model=List[StreakHistoryOut])
async def get_global_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StreakSeasonHistory)
        .where(StreakSeasonHistory.scope == "global")
        .order_by(StreakSeasonHistory.season)
    )
    return await _with_names(result.scalars().all(), db)
