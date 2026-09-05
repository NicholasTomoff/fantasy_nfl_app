from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import StreakSeasonHistory, User
from app.schemas import StreakHistoryOut

router = APIRouter(prefix="/streak-history", tags=["Streak History"])

# (schema field, label column, id column) -- a stored label always wins, because
# it can express things a user id cannot: ties, shared records, and players who
# never had an account. The id lookup is the fallback for older generated rows.
_NAME_FIELDS = [
    ("champion_name", "champion_label", "champion_id"),
    ("runner_up_name", "runner_up_label", "runner_up_id"),
    ("third_place_name", "third_place_label", "third_place_id"),
    ("best_triple_start_name", "best_triple_start_label", "best_triple_start_user_id"),
    ("longest_triple_name", "longest_triple_label", "longest_triple_user_id"),
    ("most_triples_name", "most_triples_label", "most_triples_user_id"),
    ("longest_qb_name", "longest_qb_label", None),
    ("longest_rb_name", "longest_rb_label", None),
    ("longest_wr_name", "longest_wr_label", None),
]


async def _with_names(rows, db: AsyncSession) -> List[StreakHistoryOut]:
    ids = {
        getattr(r, id_col)
        for r in rows
        for _, _, id_col in _NAME_FIELDS
        if id_col and getattr(r, id_col) is not None
    }

    names = {}
    if ids:
        result = await db.execute(
            select(User.id, User.name, User.email).where(User.id.in_(ids))
        )
        names = {uid: (name or email) for uid, name, email in result.all()}

    out = []
    for r in rows:
        item = StreakHistoryOut.model_validate(r)
        for field, label_col, id_col in _NAME_FIELDS:
            label = getattr(r, label_col, None)
            if not label and id_col:
                label = names.get(getattr(r, id_col))
            setattr(item, field, label)
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
