from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Season
from app.utils.season import get_current_season

router = APIRouter()

# GET current season
@router.get("/current")
async def get_current_season_endpoint(db: AsyncSession = Depends(get_db)):
    season = await get_current_season(db)
    return {"year": season.year}

# GET all seasons
@router.get("/all")
async def get_all_seasons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Season).order_by(Season.year.desc()))
    seasons = result.scalars().all()
    return [{"year": s.year, "is_current": s.is_current, "start_date": s.start_date, "end_date": s.end_date} for s in seasons]
