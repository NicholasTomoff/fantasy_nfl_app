# app/routes/weeks.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.season import get_current_week, get_current_finalized_week  # import utils

router = APIRouter()

# Get current week of the season
@router.get("/current")
async def current_week(season: int = Query(..., description="NFL season year"), db: AsyncSession = Depends(get_db),):
    week = await get_current_week(db, season)
    return {"week": week}

# Get current fnalized week of the season
@router.get("/finalized")
async def current_finalized_week(season: int = Query(..., description="NFL season year"), db: AsyncSession = Depends(get_db),):
    finalized_week = await get_current_finalized_week(db, season)
    return {"week": finalized_week}
